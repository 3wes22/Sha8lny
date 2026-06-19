"""
Tests for the job-ranker evaluation helpers (NDCG, MAP, leave-one-group-out).
"""

from importlib import import_module
from pathlib import Path
import sys

import pytest


# ranker.py imports `from recommendations...`, so src/ must be importable.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recommendations.ranker import (  # noqa: E402
    average_precision,
    ndcg_at_k,
    _order_relevances_by_scores,
)


def test_ndcg_perfect_order_is_one():
    assert ndcg_at_k([3, 2, 1, 0], 5) == pytest.approx(1.0)


def test_ndcg_all_zero_relevance_is_zero():
    assert ndcg_at_k([0, 0, 0], 5) == 0.0


def test_ndcg_suboptimal_order_known_value():
    # ideal DCG = 3; actual = 3/log2(3) -> ndcg = log2(2)/log2(3)
    assert ndcg_at_k([0, 3], 2) == pytest.approx(0.6309, abs=1e-4)


def test_ndcg_truncates_at_k():
    # The relevant item sits beyond k=1, so NDCG@1 must be 0.
    assert ndcg_at_k([0, 3], 1) == 0.0


def test_average_precision_all_relevant_at_top():
    assert average_precision([3, 2, 0, 0]) == pytest.approx(1.0)


def test_average_precision_relevant_at_bottom():
    # hits at positions 3 and 4: (1/3 + 2/4) / 2
    assert average_precision([0, 0, 3, 2]) == pytest.approx((1 / 3 + 0.5) / 2)


def test_average_precision_no_relevant_is_zero():
    assert average_precision([1, 0, 1]) == 0.0


def test_average_precision_respects_relevant_grade():
    # With threshold 3, the grade-2 item no longer counts as relevant.
    assert average_precision([2, 2, 2], relevant_grade=3.0) == 0.0


def test_order_relevances_by_scores_sorts_descending():
    relevances = [1, 3, 2]
    scores = [0.1, 0.9, 0.5]
    assert _order_relevances_by_scores(relevances, scores) == [3.0, 2.0, 1.0]


def test_train_and_evaluate_reports_metrics_and_beats_random():
    np = pytest.importorskip("numpy")
    pytest.importorskip("lightgbm")
    from recommendations.ranker import train_and_evaluate

    # 4 groups; within each, a single feature is perfectly aligned with relevance.
    rng = np.random.default_rng(0)
    rows, labels, groups = [], [], []
    for _ in range(4):
        grades = [3, 2, 1, 0]
        for grade in grades:
            # feature 1 (required_skill_overlap_ratio) tracks the grade; others noise.
            rows.append([rng.random(), grade / 3.0, rng.random(), rng.random(), rng.random()])
            labels.append(grade)
        groups.append(len(grades))

    result = train_and_evaluate(
        np.asarray(rows, dtype=float), np.asarray(labels, dtype=float), groups, seed=1
    )

    assert result["evaluation"] == "leave-one-group-out"
    assert result["n_folds"] == 4
    metrics = result["metrics"]
    for key in ("ndcg@5", "ndcg@10", "map"):
        assert key in metrics
        for ranker in ("lightgbm", "overlap_baseline", "random_baseline"):
            assert 0.0 <= metrics[key][ranker] <= 1.0
    # The overlap feature is perfectly informative, so the overlap baseline must
    # comfortably beat random.
    assert metrics["ndcg@5"]["overlap_baseline"] > metrics["ndcg@5"]["random_baseline"]
