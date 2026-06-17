"""
Contract tests for the retrieval citation payload (plan Task 1.10).

Every retrieved doc must carry the fields downstream citation rendering
depends on: metadata (source, file, url where present) and confidence_tier.
"""

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import retriever  # noqa: E402
from src.rag.retriever import _build_where, _confidence_tier  # noqa: E402


class TestConfidenceTier:
    @pytest.mark.parametrize("quality,expected", [
        ("official", "HIGH"),
        ("curated", "HIGH"),
        ("established", "MEDIUM"),
        ("dev_fallback", "LOW"),
        (None, "LOW"),
    ])
    def test_base_tier_from_source_quality(self, quality, expected):
        doc = {"metadata": {"quality_tier": quality}}
        assert _confidence_tier(doc) == expected

    def test_negative_rerank_score_downgrades(self):
        doc = {"metadata": {"quality_tier": "official"}, "rerank_score": -1.2}
        assert _confidence_tier(doc) == "MEDIUM"

    def test_positive_rerank_score_keeps_tier(self):
        doc = {"metadata": {"quality_tier": "official"}, "rerank_score": 3.4}
        assert _confidence_tier(doc) == "HIGH"

    def test_low_cannot_downgrade_below_low(self):
        doc = {"metadata": {"quality_tier": "dev_fallback"}, "rerank_score": -5.0}
        assert _confidence_tier(doc) == "LOW"


class TestBuildWhere:
    def test_none_when_empty(self):
        assert _build_where(None, None) is None

    def test_single_key_direct(self):
        assert _build_where("learning", None) == {"category": "learning"}
        assert _build_where(None, {"source": "mdn"}) == {"source": "mdn"}

    def test_multiple_keys_use_and(self):
        where = _build_where("learning", {"source": "roadmap.sh"})
        assert "$and" in where
        assert {"source": "roadmap.sh"} in where["$and"]
        assert {"category": "learning"} in where["$and"]


class TestPayloadContract:
    def test_hybrid_docs_carry_citation_fields(self, monkeypatch):
        monkeypatch.setenv("RAG_RERANK_ENABLED", "0")
        dense = [{
            "id": "d1",
            "content": "passage",
            "metadata": {"source": "bls_ooh", "file": "software-developers.md",
                         "url": "https://www.bls.gov/ooh/...", "quality_tier": "official"},
            "score": 0.4,
        }]

        class FakeIndex:
            available = True

            def search(self, query, top_k=10):
                return []

        monkeypatch.setattr(retriever, "_get_hybrid_index", lambda: FakeIndex())
        monkeypatch.setattr(retriever.vector_store, "search",
                            lambda query, top_k=5, filter_metadata=None: list(dense))
        monkeypatch.setattr(retriever.vector_store, "get_by_ids", lambda ids: [])

        (doc,) = retriever.retrieve_context("query", top_k=1)
        assert doc["confidence_tier"] == "HIGH"
        assert doc["metadata"]["url"].startswith("https://www.bls.gov")
        assert doc["metadata"]["file"] == "software-developers.md"

    def test_filters_force_dense_path_with_where(self, monkeypatch):
        captured = {}

        def fake_search(query, top_k=5, filter_metadata=None):
            captured["where"] = filter_metadata
            return []

        monkeypatch.setattr(retriever.vector_store, "search", fake_search)
        retriever.retrieve_context("query", top_k=3, filters={"source": "roadmap.sh"})
        assert captured["where"] == {"source": "roadmap.sh"}
