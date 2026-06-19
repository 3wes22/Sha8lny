from __future__ import annotations

import pytest

from apps.assessments.scenario_corpus.coverage import Blueprint
from apps.assessments.scenario_corpus.generation import (
    LLM_CONTENT_KEYS,
    assemble_scenario_document,
    build_generation_prompt,
)
from apps.assessments.scenario_corpus.schema import validate_scenario


def _backend_blueprint() -> Blueprint:
    return Blueprint(
        role_key="backend",
        subskill_key="decorators",
        competency="Decorators",
        dimension_key="python_fundamentals",
        stage=1,
        question_type="single_choice",
    )


def test_prompt_includes_competency_dimension_and_banned_phrases():
    system, prompt = build_generation_prompt(_backend_blueprint(), exemplars=[])
    assert "Decorators" in prompt
    assert "python_fundamentals" in prompt
    assert "Disable logging" in prompt          # banned-phrase guidance present
    assert "single_choice" in prompt
    assert "Select all that apply" not in prompt  # only for multi_select


def test_assembled_document_passes_validation():
    bp = _backend_blueprint()
    llm_payload = {
        "learning_objective": "Assess decorator metadata preservation.",
        "scenario_context": "A logging decorator wraps Django views and breaks help() output in tests.",
        "stem": "Which decorator pattern best preserves the wrapped callable's metadata?",
        "options": [
            {"id": "a", "label": "Use functools.wraps on the inner wrapper."},
            {"id": "b", "label": "Stack bare nested functions without copying __name__."},
            {"id": "c", "label": "Replace the function with a lambda that drops hints."},
            {"id": "d", "label": "Avoid decorators and inline the logging call."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "functools.wraps copies metadata to the wrapper.",
        "correct_answer_rationale": "It keeps introspection and tests stable.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Standard metadata forwarding."},
            {"option_id": "b", "is_correct": False, "rationale": "Loses metadata."},
            {"option_id": "c", "is_correct": False, "rationale": "Hides the signature."},
            {"option_id": "d", "is_correct": False, "rationale": "Avoids the concern asked."},
        ],
        "difficulty": 3,
        "estimated_seconds": 50,
    }
    doc = assemble_scenario_document(bp, llm_payload, slug="gen-test")
    assert doc["doc_id"] == "backend.decorators.s1.single_choice.gen-test"
    assert doc["review_status"] == "draft"
    assert validate_scenario(doc) == []


def test_llm_content_keys_are_the_required_keys():
    assert "scenario_context" in LLM_CONTENT_KEYS
    assert "stem" in LLM_CONTENT_KEYS
    assert "doc_id" not in LLM_CONTENT_KEYS  # governance fields are injected, not generated


def test_prompt_raises_for_unknown_question_type():
    bp = Blueprint(
        role_key="backend",
        subskill_key="decorators",
        competency="Decorators",
        dimension_key="python_fundamentals",
        stage=1,
        question_type="bogus_type",
    )
    with pytest.raises(ValueError, match="unknown question_type"):
        build_generation_prompt(bp, exemplars=[])
