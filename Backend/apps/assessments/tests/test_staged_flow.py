from datetime import date, timedelta
import re

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.role_graph import load_role_graph
from apps.core.ai_logging import build_ai_metadata
from apps.core.ai_contracts import SubSkillEvidence
from apps.core.gemma_client import GemmaResponse
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def assessment_user(db):
    return User.objects.create_user(
        email="staged-assessment@example.com",
        auth0_id="staged_assessment_auth0",
        username="staged_assessment_user",
        full_name="Staged Assessment User",
        date_of_birth=date.today() - timedelta(days=365 * 24),
        password="TestPass123!",
    )


def _build_stage_responses(questions):
    responses = []
    for question in questions:
        answer = "mid"
        if question["type"] == "text":
            answer = "I can explain my tradeoffs clearly in production scenarios."
        responses.append(
            {
                "question_id": question["id"],
                "answer": answer,
                "timestamp": "2026-04-14T00:00:00Z",
            }
        )
    return responses


def _question_payload_from_prompt(prompt: str, *, stage: int) -> dict:
    targets: list[tuple[str, str]] = []
    for line in prompt.splitlines():
        match = re.match(r"^- ([a-z0-9_]+): .+ \(([^)]+)\)$", line.strip())
        if match:
            targets.append((match.group(1), match.group(2)))

    return {
        "questions": [
            {
                "id": f"s{stage}_q{index}",
                "stage": stage,
                "subskill_key": subskill_key,
                "dimension_key": dimension_key,
                "question_text": f"Generated question for {subskill_key.replace('_', ' ')}",
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "Low", "score": 1},
                    {"value": "mid", "label": "Mid", "score": 3},
                    {"value": "high", "label": "High", "score": 5},
                ],
                "difficulty": 3,
                "estimated_seconds": 45,
            }
            for index, (subskill_key, dimension_key) in enumerate(targets, start=1)
        ]
    }


@pytest.mark.django_db
def test_staged_assessment_progresses_from_stage_one_to_stage_two_to_result(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)

    create_response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": "Backend Developer"},
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data["stage"] == "stage_1"
    assert create_response.data["generation_status"] == "pending"
    assert create_response.data["presentation"]["submission_state"] == "stage_1_generating"

    assessment_id = create_response.data["id"]
    detail_response = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))

    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.data["stage"] == "stage_1"
    assert detail_response.data["generation_status"] == "completed"
    assert detail_response.data["presentation"]["submission_state"] == "stage_1_ready"
    assert len(detail_response.data["active_questions"]) == 5
    assert len(detail_response.data["questions"]) == 5

    stage_one_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(detail_response.data["active_questions"])},
        format="json",
    )

    assert stage_one_submit.status_code == status.HTTP_202_ACCEPTED
    assert stage_one_submit.data["submission_state"] == "stage_1_analyzing"
    assert stage_one_submit.data["assessment"]["stage"] == "stage_1"

    stage_two_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))

    assert stage_two_detail.status_code == status.HTTP_200_OK
    assert stage_two_detail.data["stage"] == "stage_2"
    assert stage_two_detail.data["generation_status"] == "completed"
    assert stage_two_detail.data["presentation"]["submission_state"] == "stage_2_ready"
    assert stage_two_detail.data["gap_profile_summary"]["high_priority_count"] >= 1
    assert len(stage_two_detail.data["active_questions"]) == 5

    stage_two_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_two_detail.data["active_questions"])},
        format="json",
    )

    assert stage_two_submit.status_code == status.HTTP_202_ACCEPTED
    assert stage_two_submit.data["submission_state"] == "stage_2_analyzing"
    assert stage_two_submit.data["assessment"]["stage"] == "stage_2"

    result_response = api_client.get(reverse("assessment-result", kwargs={"pk": assessment_id}))

    assert result_response.status_code == status.HTTP_200_OK
    assert result_response.data["submission_state"] == "completed"
    assert result_response.data["roadmap_signal"]["role"] == "backend"
    assert len(result_response.data["roadmap_signal"]["priority_order"]) >= 1
    assert result_response.data["roadmap_signal"]["generation_metadata"]["fallback_used"] in {True, False}

    assessment = Assessment.objects.get(id=assessment_id)
    assert assessment.stage == "completed"
    assert assessment.roadmap_signal["role"] == "backend"
    assert AssessmentResult.objects.filter(assessment=assessment, is_deleted=False).exists()


@pytest.mark.django_db
def test_staged_assessment_caps_llm_invocations_at_three(api_client, assessment_user, monkeypatch):
    api_client.force_authenticate(user=assessment_user)
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(self, *, prompt, system="", required_keys=()):  # noqa: ARG001
        calls["count"] += 1
        metadata = build_ai_metadata(
            source="llm",
            processing_time_ms=15,
            model="mock-gemma",
            version="test-v1",
        )

        if tuple(required_keys) == ("questions",):
            stage = 1 if "Generate 5 calibration questions" in prompt else 2
            return GemmaResponse(
                text="{}",
                payload=_question_payload_from_prompt(prompt, stage=stage),
                metadata=metadata,
                prompt_tokens=24,
                completion_tokens=18,
            )

        return GemmaResponse(
            text="{}",
            payload={
                "overall_score": 81,
                "strengths": ["Problem solving", "API design"],
                "areas_for_improvement": ["Database modeling", "Testing"],
                "recommended_careers": [
                    {
                        "title": "Backend Developer",
                        "match_score": 90,
                        "reasoning": "Strong alignment with backend role requirements.",
                    }
                ],
                "recommended_learning_paths": [
                    {"skill": "API Design", "priority": "high", "resources": []}
                ],
                "ai_insights": "The staged assessment indicates solid backend momentum.",
                "ai_confidence_score": 84,
            },
            metadata=metadata,
            prompt_tokens=31,
            completion_tokens=22,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    create_response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": "Backend Developer"},
        format="json",
    )
    assessment_id = create_response.data["id"]

    stage_one_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    stage_one_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_one_detail.data["active_questions"])},
        format="json",
    )
    assert stage_one_submit.status_code == status.HTTP_202_ACCEPTED

    stage_two_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    stage_two_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_two_detail.data["active_questions"])},
        format="json",
    )
    assert stage_two_submit.status_code == status.HTTP_202_ACCEPTED

    result_response = api_client.get(reverse("assessment-result", kwargs={"pk": assessment_id}))

    assert result_response.status_code == status.HTTP_200_OK
    assert result_response.data["submission_state"] == "completed"
    assert calls["count"] == 3
    assert calls["count"] <= 3


def test_deterministic_staged_analysis_uses_graph_driven_role_recommendations():
    role_graph = load_role_graph("backend")
    metadata = build_ai_metadata(
        source="fallback",
        processing_time_ms=8,
        model=None,
        provider="sha8alny",
        version=role_graph.version,
        fallback_used=True,
    )
    merged_evidence = [
        SubSkillEvidence(
            subskill_key=role_graph.dimensions[0].subskills[0].key,
            dimension_key=role_graph.dimensions[0].key,
            observed_level=2.0,
            target_level=role_graph.dimensions[0].subskills[0].target_proficiency,
            gap=2.0,
            confidence=0.82,
            evidence_strength="strong",
        ),
        SubSkillEvidence(
            subskill_key=role_graph.dimensions[1].subskills[0].key,
            dimension_key=role_graph.dimensions[1].key,
            observed_level=3.0,
            target_level=role_graph.dimensions[1].subskills[0].target_proficiency,
            gap=1.0,
            confidence=0.76,
            evidence_strength="strong",
        ),
    ]

    analysis = AssessmentAIService._deterministic_staged_analysis(
        role_graph,
        merged_evidence,
        metadata,
    )

    assert [item["title"] for item in analysis.recommended_careers] == [role_graph.role_label]
