from dataclasses import replace

from django.core.cache import cache

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.core.ai_logging import build_ai_metadata
from apps.core.gemma_client import GemmaResponse


def _stage_one_payload(graph):
    return {
        "questions": [
            {
                "id": f"s1_q{index + 1}",
                "stage": 1,
                "subskill_key": target.key,
                "dimension_key": target.dimension,
                "question_text": f"Generated question for {target.label}",
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "Low", "score": 1},
                    {"value": "mid", "label": "Mid", "score": 3},
                    {"value": "high", "label": "High", "score": 5},
                ],
                "difficulty": 2 + index,
                "estimated_seconds": 45,
            }
            for index, target in enumerate(StageAllocator.allocate_stage_one(graph))
        ]
    }


def test_stage_one_generation_uses_cache_for_same_role_and_version(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(self, *, prompt, system="", required_keys=()):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=_stage_one_payload(graph),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=12,
                model="mock-gemma",
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    first_questions, _ = AssessmentAIService.generate_stage_one("backend", graph)
    second_questions, _ = AssessmentAIService.generate_stage_one("backend", graph)

    assert calls["count"] == 1
    assert first_questions == second_questions


def test_stage_one_generation_invalidates_cache_when_graph_version_changes(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(self, *, prompt, system="", required_keys=()):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=_stage_one_payload(graph),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=12,
                model="mock-gemma",
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    AssessmentAIService.generate_stage_one("backend", graph)
    AssessmentAIService.generate_stage_one("backend", replace(graph, version="stub-v2"))

    assert calls["count"] == 2
