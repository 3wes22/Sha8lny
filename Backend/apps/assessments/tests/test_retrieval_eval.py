from __future__ import annotations

from apps.assessments.scenario_corpus.eval.retrieval_eval import (
    RetrievalEvalResult,
    evaluate_role,
)


def test_evaluate_role_returns_coverage_and_precision_fields():
    result = evaluate_role("backend")
    assert isinstance(result, RetrievalEvalResult)
    assert 0.0 <= result.coverage <= 1.0
    assert 0.0 <= result.subskill_precision <= 1.0
    assert result.role_key == "backend"
    assert result.blueprint_count > 0
