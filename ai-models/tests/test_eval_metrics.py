"""
Unit tests for pure-Python retrieval evaluation metrics.

These metrics form the control-group harness for the Week-1 knowledge-layer
rebuild (IMPLEMENTATION_PLAN.md Task 1.1). They must stay dependency-free:
no Chroma, no network, no model downloads.
"""

from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.eval_metrics import (  # noqa: E402
    mrr,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)


class TestRecallAtK:
    def test_partial_hit(self):
        # top-3 = [a, b, c]; relevant ∩ top-3 = {a, c}; |relevant| = 3
        assert recall_at_k(["a", "b", "c", "d"], {"a", "c", "x"}, k=3) == pytest.approx(2 / 3)

    def test_all_relevant_retrieved(self):
        assert recall_at_k(["a", "b"], {"a", "b"}, k=2) == pytest.approx(1.0)

    def test_no_relevant_retrieved(self):
        assert recall_at_k(["a", "b"], {"x", "y"}, k=2) == pytest.approx(0.0)

    def test_empty_relevant_set_returns_zero(self):
        assert recall_at_k(["a", "b"], set(), k=2) == pytest.approx(0.0)

    def test_empty_retrieval_returns_zero(self):
        assert recall_at_k([], {"a"}, k=5) == pytest.approx(0.0)

    def test_k_smaller_than_result_count_truncates(self):
        # relevant doc 'c' sits at rank 3, outside k=2
        assert recall_at_k(["a", "b", "c"], {"c"}, k=2) == pytest.approx(0.0)


class TestPrecisionAtK:
    def test_partial_hit(self):
        # top-3 = [a, b, c]; hits = {a, c}; denominator is k
        assert precision_at_k(["a", "b", "c", "d"], {"a", "c", "x"}, k=3) == pytest.approx(2 / 3)

    def test_k_larger_than_result_count_uses_k_denominator(self):
        # strict standard: short result lists are penalized
        assert precision_at_k(["a"], {"a"}, k=5) == pytest.approx(1 / 5)

    def test_empty_retrieval_returns_zero(self):
        assert precision_at_k([], {"a"}, k=5) == pytest.approx(0.0)

    def test_no_hits(self):
        assert precision_at_k(["a", "b"], {"x"}, k=2) == pytest.approx(0.0)


class TestReciprocalRank:
    def test_first_position(self):
        assert reciprocal_rank(["a", "b"], {"a"}) == pytest.approx(1.0)

    def test_third_position(self):
        assert reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)

    def test_no_relevant_returns_zero(self):
        assert reciprocal_rank(["x", "y"], {"a"}) == pytest.approx(0.0)

    def test_empty_retrieval_returns_zero(self):
        assert reciprocal_rank([], {"a"}) == pytest.approx(0.0)


class TestMRR:
    def test_mean_over_queries(self):
        runs = [
            (["a", "b"], {"a"}),      # RR = 1.0
            (["x", "y", "b"], {"b"}),  # RR = 1/3
            (["x", "y"], {"z"}),       # RR = 0.0
        ]
        assert mrr(runs) == pytest.approx((1.0 + 1 / 3 + 0.0) / 3)

    def test_empty_runs_returns_zero(self):
        assert mrr([]) == pytest.approx(0.0)
