"""
Unit tests for hybrid retrieval wiring in retrieve_context (plan Task 1.8).

vector_store and the BM25 index are monkeypatched — no Chroma, no models.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import retriever  # noqa: E402


DENSE = [
    {"id": "d1", "content": "dense one", "metadata": {"source": "mdn"}, "score": 0.5},
    {"id": "d2", "content": "dense two", "metadata": {"source": "onet"}, "score": -0.2},
]
BM25 = [("d3", 7.0), ("d1", 5.0)]
STORE_D3 = {"id": "d3", "content": "bm25 only", "metadata": {"source": "bls_ooh"}}


class FakeIndex:
    available = True

    def search(self, query, top_k=10):
        return BM25


@pytest.fixture
def hybrid_env(monkeypatch):
    # rerank off: these tests pin the RRF fusion contract (the reranker has
    # its own tests); also prevents any model download in CI
    monkeypatch.setenv("RAG_RERANK_ENABLED", "0")
    monkeypatch.setattr(retriever, "_hybrid_index", None)
    monkeypatch.setattr(retriever, "_hybrid_index_failed", False)
    monkeypatch.setattr(retriever, "_get_hybrid_index", lambda: FakeIndex())
    monkeypatch.setattr(retriever.vector_store, "search",
                        lambda query, top_k=5, filter_metadata=None: list(DENSE))
    monkeypatch.setattr(retriever.vector_store, "get_by_ids",
                        lambda ids: [STORE_D3] if "d3" in ids else [])


class TestHybridPath:
    def test_fusion_order(self, hybrid_env):
        results = retriever.retrieve_context("query", top_k=3)
        assert [doc["id"] for doc in results] == ["d1", "d3", "d2"]

    def test_rrf_scores_attached(self, hybrid_env):
        results = retriever.retrieve_context("query", top_k=3)
        by_id = {doc["id"]: doc for doc in results}
        assert by_id["d1"]["score"] == pytest.approx(1 / 61 + 1 / 62)
        assert by_id["d3"]["score"] == pytest.approx(1 / 61)
        assert all(doc["retrieval"] == "hybrid_rrf" for doc in results)

    def test_bm25_only_docs_fetched_from_store(self, hybrid_env):
        results = retriever.retrieve_context("query", top_k=3)
        d3 = next(doc for doc in results if doc["id"] == "d3")
        assert d3["content"] == "bm25 only"
        assert d3["metadata"]["source"] == "bls_ooh"

    def test_no_min_score_filter_on_hybrid_path(self, hybrid_env):
        # d2 has score -0.2; the legacy threshold would drop it
        results = retriever.retrieve_context("query", top_k=3, min_score=0.3)
        assert any(doc["id"] == "d2" for doc in results)

    def test_top_k_respected(self, hybrid_env):
        assert len(retriever.retrieve_context("query", top_k=2)) == 2


class TestDenseFallback:
    def test_min_score_filter_applies_when_index_unavailable(self, monkeypatch):
        monkeypatch.setattr(retriever, "_get_hybrid_index", lambda: None)
        monkeypatch.setattr(retriever.vector_store, "search",
                            lambda query, top_k=5, filter_metadata=None: list(DENSE))
        results = retriever.retrieve_context("query", top_k=5, min_score=0.3)
        assert [doc["id"] for doc in results] == ["d1"]

    def test_category_filter_forces_dense_path(self, monkeypatch):
        consulted = {"hybrid": False}

        def tracking_index():
            consulted["hybrid"] = True
            return FakeIndex()

        captured = {}

        def fake_search(query, top_k=5, filter_metadata=None):
            captured["filter"] = filter_metadata
            return list(DENSE)

        monkeypatch.setattr(retriever, "_get_hybrid_index", tracking_index)
        monkeypatch.setattr(retriever.vector_store, "search", fake_search)
        retriever.retrieve_context("query", top_k=5, category="learning")
        assert consulted["hybrid"] is False
        assert captured["filter"] == {"category": "learning"}
