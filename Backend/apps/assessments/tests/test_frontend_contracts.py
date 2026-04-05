import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Assessment, AssessmentResult
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def assessment_user(db):
    return User.objects.create_user(
        email="assessment-contract@example.com",
        auth0_id="assessment_contract_auth0",
        username="assessment_contract_user",
        full_name="Assessment Contract User",
        date_of_birth=date.today() - timedelta(days=365 * 24),
        password="TestPass123!",
    )


@pytest.mark.django_db
def test_assessment_detail_exposes_presentation_metadata(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)

    create_response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": "Frontend Engineer"},
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assert create_response.data["presentation"]["question_count"] == 6
    assert create_response.data["presentation"]["interaction_modes"]
    assert create_response.data["questions"][0]["interaction_mode"]


@pytest.mark.django_db
def test_assessment_result_processing_exposes_status_message(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)
    assessment = Assessment.objects.create(
        user=assessment_user,
        assessment_type="skills",
        questions=[],
        total_questions=0,
        status="completed",
        ai_processing_status="pending",
    )

    response = api_client.get(reverse("assessment-result", kwargs={"pk": str(assessment.id)}))

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["submission_state"] == "processing"
    assert response.data["status_message"]
    assert response.data["next_actions"]


@pytest.mark.django_db
def test_assessment_result_completed_exposes_next_actions(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)
    assessment = Assessment.objects.create(
        user=assessment_user,
        assessment_type="skills",
        questions=[],
        total_questions=0,
        status="completed",
        ai_processing_status="completed",
    )
    AssessmentResult.objects.create(
        assessment=assessment,
        overall_score=78,
        skill_scores={},
        strengths=["Communication"],
        areas_for_improvement=["System design"],
        recommended_careers=[{"title": "Product Engineer", "match_score": 79, "reasoning": "Strong product sense"}],
        ai_insights="You have solid momentum.",
        llm_model_used="mock-v1",
    )

    response = api_client.get(reverse("assessment-result", kwargs={"pk": str(assessment.id)}))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["submission_state"] == "completed"
    assert response.data["status_message"]
    assert response.data["next_actions"][0]["route"] == "/roadmap"
