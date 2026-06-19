from __future__ import annotations

from apps.assessments.scenario_corpus.eval.rubric import score_question


def _good() -> dict:
    return {
        "scenario_context": "A payment API double-charges when a mobile client retries after a timeout.",
        "stem": "Which design prevents a duplicate charge while keeping the API predictable?",
        "options": [
            {"id": "a", "label": "Require an idempotency key and return the first result on retry."},
            {"id": "b", "label": "Let finance reverse duplicate charges overnight in a batch job."},
            {"id": "c", "label": "Convert the endpoint to GET so clients can retry safely each time."},
            {"id": "d", "label": "Delay every charge a few seconds so retries arrive before processing."},
        ],
    }


def test_good_question_scores_high():
    result = score_question(_good(), role_key="backend")
    assert result["has_concrete_scenario"] is True
    assert result["no_banned_phrase"] is True
    assert result["options_parallel"] is True
    assert result["total"] >= 3


def test_banned_phrase_flagged():
    bad = _good()
    bad["options"][0]["label"] = "Disable logging to avoid the duplicate."
    result = score_question(bad, role_key="backend")
    assert result["no_banned_phrase"] is False


def test_short_scenario_not_concrete():
    q = _good()
    q["scenario_context"] = "A short scenario."
    assert score_question(q, role_key="backend")["has_concrete_scenario"] is False


def test_definition_stem_not_decision():
    q = _good()
    q["stem"] = "Explain what an idempotency key represents."
    assert score_question(q, role_key="backend")["decision_not_definition"] is False


def test_unknown_role_key_has_no_vocab_and_does_not_raise():
    result = score_question(_good(), role_key="security")
    assert result["uses_role_vocab"] is False
