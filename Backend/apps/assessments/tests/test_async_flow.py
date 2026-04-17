from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Assessment
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def assessment_user(db):
    user = User.objects.create_user(
        email="assessment-async@example.com",
        auth0_id="assessment_async_auth0",
        username="assessment_async_user",
        full_name="Assessment Async User",
        date_of_birth=date.today() - timedelta(days=365 * 24),
        password="TestPass123!",
    )
    return user


@pytest.mark.django_db
def test_create_assessment_queues_question_generation(api_client, assessment_user, monkeypatch):
    api_client.force_authenticate(user=assessment_user)

    monkeypatch.setattr(
        "apps.assessments.views.dispatch_assessment_task",
        lambda task, eager_runner, assessment_id: SimpleNamespace(id="assessment-question-task"),
    )

    response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": "Backend Developer"},
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["stage"] == "stage_1"
    assert response.data["generation_status"] == "pending"
    assert response.data["ai_processing_status"] == "pending"
    assert response.data["questions"] == []
    assert response.data["presentation"]["submission_state"] == "stage_1_generating"

    assessment = Assessment.objects.get(id=response.data["id"])
    assert assessment.ai_task_id == "assessment-question-task"
    assert assessment.total_questions == 10


@pytest.mark.django_db
def test_submit_assessment_queues_async_evaluation(api_client, assessment_user, monkeypatch):
    api_client.force_authenticate(user=assessment_user)

    assessment = Assessment.objects.create(
        user=assessment_user,
        assessment_type="skills",
        target_career="Backend Developer",
        questions=[
            {"id": 1, "question": "What do you want to learn first?", "type": "text", "interaction_mode": "text"}
        ],
        total_questions=1,
        ai_processing_status="completed",
        status="draft",
    )

    monkeypatch.setattr(
        "apps.assessments.views.dispatch_assessment_task",
        lambda task, eager_runner, assessment_id: SimpleNamespace(id="assessment-eval-task"),
    )

    response = api_client.post(
        reverse("assessment-submit", kwargs={"pk": str(assessment.id)}),
        {"responses": [{"question_id": 1, "answer": "Django APIs"}]},
        format="json",
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.data["submission_state"] == "processing"
    assert response.data["assessment"]["ai_processing_status"] == "pending"

    assessment.refresh_from_db()
    assert assessment.status == "completed"
    assert assessment.ai_processing_status == "pending"
    assert assessment.ai_task_id == "assessment-eval-task"
