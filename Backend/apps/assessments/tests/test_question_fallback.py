"""Tests for curated scenario fallbacks when Gemini is unavailable."""

from django.core.cache import cache

import pytest

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.fallback_scenarios import get_curated_fallback_scenario
from apps.assessments.role_graph import load_role_graph
from apps.assessments.services import AssessmentService
from apps.core import ai_settings as core_ai_settings


@pytest.fixture(autouse=True)
def clear_stage_cache():
    cache.clear()
    yield
    cache.clear()


def test_stage_one_uses_curated_bank_when_gemini_key_missing(monkeypatch):
    monkeypatch.setattr(core_ai_settings, "GEMINI_API_KEY", "")
    graph = load_role_graph("backend")

    questions, metadata, _ = AssessmentAIService.generate_stage_one("backend", graph)

    assert metadata.fallback_used is True
    assert metadata.source == "curated_fallback"
    assert metadata.error_code == "gemini_api_key_missing"
    assert questions[0]["answer_key"]["correct_option_ids"]
    payment_question = next(
        question for question in questions if question["subskill_key"] == "http_api_design"
    )
    assert (
        "idempotency" in payment_question["question_text"].lower()
        or "payment" in payment_question["question_text"].lower()
    )
    assert all(
        len(option.get("label", "")) > 20
        for option in payment_question["options"]
    )


def test_normalize_staged_questions_keeps_scenario_options(monkeypatch):
    monkeypatch.setattr(core_ai_settings, "GEMINI_API_KEY", "")
    graph = load_role_graph("backend")
    scenario = get_curated_fallback_scenario(
        role_key="backend",
        stage=1,
        subskill_key="http_api_design",
        question_type="single_choice",
    )
    stored = [
        {
            "id": "q1",
            "subskill_key": "http_api_design",
            "category": "http_api_design",
            "question_type": "single_choice",
            "type": "multiple_choice",
            "interaction_mode": "single_select",
            "scenario_context": scenario["scenario_context"],
            "question_text": scenario["question_text"],
            "options": scenario["options"],
            "answer_key": scenario["answer_key"],
        }
    ]

    client_questions = AssessmentService._normalize_staged_questions(stored)

    assert "payment API" in client_questions[0]["question_text"]
    assert len(client_questions[0]["options"]) == 4
    labels = [option["label"] for option in client_questions[0]["options"]]
    assert any("idempotency" in label.lower() for label in labels)
    assert "answer_key" not in client_questions[0]
    assert not any("I would need guidance" in label for label in labels)


def test_normalize_staged_questions_does_not_inject_self_assessment_options():
    stored = [
        {
            "id": "q1",
            "subskill_key": "http_api_design",
            "category": "http_api_design",
            "question_type": "single_choice",
            "type": "multiple_choice",
            "interaction_mode": "single_select",
            "question_text": "Which API design prevents duplicate charges?",
            "options": [],
        }
    ]

    client_questions = AssessmentService._normalize_staged_questions(stored)

    assert client_questions[0]["options"] == []
