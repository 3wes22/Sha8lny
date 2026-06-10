"""
Unit tests for hybrid retrieval: BM25 keyword search + RRF fusion
(plan Task 1.8). No Chroma, no network — fixture docs only.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import hybrid_search  # noqa: E402
from src.rag.hybrid_search import HybridIndex, rrf_fuse  # noqa: E402


DOCS = [
    {"id": "d1", "content": "CORS is a mechanism that lets servers allow cross-origin requests from browsers."},
    {"id": "d2", "content": "Salary negotiation in Egypt requires knowing your market worth before interviews."},
    {"id": "d3", "content": "Backend developers learn databases, APIs, and server-side programming languages."},
    {"id": "d4", "content": "HTTP caching stores responses so browsers avoid refetching unchanged resources."},
]


requires_bm25 = pytest.mark.skipif(
    hybrid_search.BM25Okapi is None,
    reason="rank_bm25 not installed in this environment",
)


class TestBM25Search:
    @requires_bm25
    def test_keyword_match_ranks_first(self):
        index = HybridIndex(DOCS)
        results = index.search("What is CORS and why do browsers block cross-origin requests", top_k=4)
        assert results, "expected results from keyword search"
        assert results[0][0] == "d1"

    @requires_bm25
    def test_top_k_limits_results(self):
        index = HybridIndex(DOCS)
        assert len(index.search("browsers", top_k=2)) <= 2

    @requires_bm25
    def test_empty_query_returns_nothing(self):
        index = HybridIndex(DOCS)
        assert index.search("", top_k=3) == []

    def test_no_docs(self):
        index = HybridIndex([])
        assert index.available is False
        assert index.search("anything", top_k=3) == []


class TestFallback:
    def test_unavailable_without_rank_bm25(self, monkeypatch):
        monkeypatch.setattr(hybrid_search, "BM25Okapi", None)
        index = HybridIndex(DOCS)
        assert index.available is False
        assert index.search("CORS", top_k=3) == []


class TestRRF:
    def test_fusion_order_and_scores(self):
        fused = rrf_fuse([["a", "b", "c"], ["a", "c"]], k=60)
        ids = [doc_id for doc_id, _ in fused]
        assert ids == ["a", "c", "b"]
        scores = dict(fused)
        assert scores["a"] == pytest.approx(1 / 61 + 1 / 61)
        assert scores["c"] == pytest.approx(1 / 63 + 1 / 62)
        assert scores["b"] == pytest.approx(1 / 62)

    def test_empty_rankings(self):
        assert rrf_fuse([]) == []
        assert rrf_fuse([[], []]) == []

    def test_single_ranking_preserves_order(self):
        fused = rrf_fuse([["x", "y"]])
        assert [doc_id for doc_id, _ in fused] == ["x", "y"]
