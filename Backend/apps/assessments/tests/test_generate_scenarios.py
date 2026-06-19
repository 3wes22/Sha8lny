from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from apps.assessments.scenario_corpus.staging import read_drafts
from apps.core.ai_logging import build_ai_metadata
from apps.core.gemma_client import GemmaResponse


def _valid_payload() -> dict:
    return {
        "learning_objective": "Assess decorator metadata preservation.",
        "scenario_context": "A logging decorator wraps Django views and breaks help() output.",
        "stem": "Which decorator pattern best preserves the wrapped callable's metadata?",
        "options": [
            {"id": "a", "label": "Use functools.wraps on the inner wrapper."},
            {"id": "b", "label": "Stack bare nested functions without copying __name__."},
            {"id": "c", "label": "Replace the function with a lambda dropping hints."},
            {"id": "d", "label": "Avoid decorators and inline the logging."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "functools.wraps copies metadata to the wrapper.",
        "correct_answer_rationale": "Keeps introspection stable.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Standard forwarding."},
            {"option_id": "b", "is_correct": False, "rationale": "Loses metadata."},
            {"option_id": "c", "is_correct": False, "rationale": "Hides the signature."},
            {"option_id": "d", "is_correct": False, "rationale": "Avoids the concern."},
        ],
        "difficulty": 3,
        "estimated_seconds": 50,
    }


@pytest.mark.django_db
def test_generate_writes_only_valid_drafts_to_staging(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )

    def fake_generate_structured(self, *, prompt, system="", required_keys=(), response_json_schema=None):  # noqa: ARG001
        return GemmaResponse(
            text="{}",
            payload=_valid_payload(),
            metadata=build_ai_metadata(source="llm", processing_time_ms=1, model="mock"),
            prompt_tokens=1,
            completion_tokens=1,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    call_command("generate_scenarios", "--role", "frontend", "--tier", "1", "--limit", "2", stdout=StringIO())

    drafts = read_drafts("frontend")
    assert len(drafts) == 2
    assert all(d["review_status"] == "draft" for d in drafts)
    assert all(d["role_key"] == "frontend" for d in drafts)


@pytest.mark.django_db
def test_generate_skips_invalid_model_output(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )

    def fake_generate_structured(self, *, prompt, system="", required_keys=(), response_json_schema=None):  # noqa: ARG001
        bad = _valid_payload()
        bad["options"] = bad["options"][:2]  # only 2 options -> invalid single_choice
        return GemmaResponse(
            text="{}", payload=bad,
            metadata=build_ai_metadata(source="llm", processing_time_ms=1, model="mock"),
            prompt_tokens=1, completion_tokens=1,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    call_command("generate_scenarios", "--role", "frontend", "--tier", "1", "--limit", "2", stdout=StringIO())
    assert read_drafts("frontend") == []  # nothing valid was staged


@pytest.mark.django_db
def test_generate_skips_failed_generation_and_continues(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )
    calls = {"n": 0}

    def fake_generate_structured(self, *, prompt, system="", required_keys=(), response_json_schema=None):  # noqa: ARG001
        calls["n"] += 1
        if calls["n"] == 1:
            from apps.core.exceptions import AIServiceError

            raise AIServiceError("simulated generation failure")
        return GemmaResponse(
            text="{}",
            payload=_valid_payload(),
            metadata=build_ai_metadata(source="llm", processing_time_ms=1, model="mock"),
            prompt_tokens=1,
            completion_tokens=1,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    call_command(
        "generate_scenarios", "--role", "frontend", "--tier", "1", "--limit", "2",
        stdout=StringIO(), stderr=StringIO(),
    )

    drafts = read_drafts("frontend")
    assert len(drafts) == 1   # first blueprint failed (skipped), second succeeded
    assert calls["n"] == 2    # the batch continued past the failure
