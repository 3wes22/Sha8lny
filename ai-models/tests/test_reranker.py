"""
Unit tests for cross-encoder re-ranking (plan Task 1.9).

The scorer is injected — no model download in tests. Unavailability must be
a silent passthrough (same graceful-degradation contract as hybrid search).
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag import reranker  # noqa: E402


DOCS = [
    {"id": "a", "content": "alpha passage", "score": 0.030},
    {"id": "b", "content": "beta passage", "score": 0.020},
    {"id": "c", "content": "gamma passage", "score": 0.010},
]


def fake_scorer(pairs):
    # score by content: gamma best, alpha worst
    table = {"alpha passage": 0.1, "beta passage": 0.5, "gamma passage": 0.9}
    return [table[passage] for _, passage in pairs]


class TestRerank:
    def test_reorders_by_scorer(self):
        result = reranker.rerank("query", list(DOCS), top_k=3, scorer=fake_scorer)
        assert [doc["id"] for doc in result] == ["c", "b", "a"]

    def test_attaches_rerank_score_and_label(self):
        result = reranker.rerank("query", list(DOCS), top_k=2, scorer=fake_scorer)
        assert result[0]["rerank_score"] == 0.9
        assert result[0]["retrieval"] == "hybrid_rrf+ce"

    def test_top_k_truncates(self):
        assert len(reranker.rerank("query", list(DOCS), top_k=1, scorer=fake_scorer)) == 1

    def test_empty_docs(self):
        assert reranker.rerank("query", [], top_k=5, scorer=fake_scorer) == []


class TestGracefulDegradation:
    def test_unavailable_model_is_passthrough(self, monkeypatch):
        monkeypatch.setattr(reranker, "_get_scorer", lambda: None)
        result = reranker.rerank("query", list(DOCS), top_k=2)
        assert [doc["id"] for doc in result] == ["a", "b"]
        assert "rerank_score" not in result[0]

    def test_disabled_via_setting_is_passthrough(self, monkeypatch):
        monkeypatch.setenv("RAG_RERANK_ENABLED", "0")
        result = reranker.rerank("query", list(DOCS), top_k=2, scorer=fake_scorer)
        assert [doc["id"] for doc in result] == ["a", "b"]
