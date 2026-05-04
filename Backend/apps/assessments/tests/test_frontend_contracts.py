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
    assert create_response.data["presentation"]["submission_state"] == "stage_1_generating"
    assert create_response.data["presentation"]["question_count"] == 0

    detail_response = api_client.get(
        reverse("assessment-detail", kwargs={"pk": str(create_response.data["id"])})
    )

    assert detail_response.status_code == status.HTTP_200_OK
    assert detail_response.data["presentation"]["submission_state"] == "stage_1_ready"
    assert detail_response.data["presentation"]["question_count"] == 5
    assert detail_response.data["presentation"]["interaction_modes"]
    assert detail_response.data["questions"][0]["interaction_mode"]


@pytest.mark.django_db
def test_assessment_detail_repairs_malformed_staged_option_contract(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)
    assessment = Assessment.objects.create(
        user=assessment_user,
        assessment_type="skills",
        target_career="Backend Developer",
        stage="stage_1",
        stage_one_questions=[
            {
                "id": "s1_q1",
                "stage": 1,
                "subskill_key": "http_api_design",
                "dimension_key": "backend_core",
                "type": "multiple_choice",
                "question": "Which option best matches your current API design judgment?",
                "category": "HTTP API Design",
                "options": [
                    {"value": "low"},
                    {"value": "mid"},
                    {"value": "high"},
                ],
            }
        ],
        questions=[
            {
                "id": "s1_q1",
                "stage": 1,
                "subskill_key": "http_api_design",
                "dimension_key": "backend_core",
                "type": "multiple_choice",
                "question": "Which option best matches your current API design judgment?",
                "category": "HTTP API Design",
                "options": [
                    {"value": "low"},
                    {"value": "mid"},
                    {"value": "high"},
                ],
            }
        ],
        responses=[],
        status="draft",
        ai_processing_status="completed",
        total_questions=5,
    )

    response = api_client.get(reverse("assessment-detail", kwargs={"pk": str(assessment.id)}))

    assert response.status_code == status.HTTP_200_OK
    options = response.data["active_questions"][0]["options"]
    assert options == [
        {
            "value": "low",
            "label": "I would need guidance to complete HTTP API Design",
            "score": 1,
        },
        {
            "value": "mid",
            "label": "I can handle common HTTP API Design work independently",
            "score": 3,
        },
        {
            "value": "high",
            "label": "I can make tradeoffs, debug edge cases, and lead HTTP API Design work",
            "score": 5,
        },
    ]


@pytest.mark.django_db
def test_assessment_detail_normalizes_string_options_and_invalid_interaction_mode(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)
    assessment = Assessment.objects.create(
        user=assessment_user,
        assessment_type="skills",
        target_career="Backend Developer",
        stage="stage_1",
        stage_one_questions=[
            {
                "id": "s1_q1",
                "stage": 1,
                "subskill_key": "http_api_design",
                "dimension_key": "backend_core",
                "type": "multiple_choice",
                "interaction_mode": "text_input",
                "question": "Which endpoint shape best matches the update?",
                "category": "HTTP API Design",
                "options": [
                    "PUT /users/{id}/profile",
                    "POST /users/update_profile",
                    "PATCH /users/{id}",
                    "GET /users/{id}/profile",
                ],
            }
        ],
        questions=[
            {
                "id": "s1_q1",
                "stage": 1,
                "subskill_key": "http_api_design",
                "dimension_key": "backend_core",
                "type": "multiple_choice",
                "interaction_mode": "text_input",
                "question": "Which endpoint shape best matches the update?",
                "category": "HTTP API Design",
                "options": [
                    "PUT /users/{id}/profile",
                    "POST /users/update_profile",
                    "PATCH /users/{id}",
                    "GET /users/{id}/profile",
                ],
            }
        ],
        responses=[],
        status="draft",
        ai_processing_status="completed",
        total_questions=5,
    )

    response = api_client.get(reverse("assessment-detail", kwargs={"pk": str(assessment.id)}))

    assert response.status_code == status.HTTP_200_OK
    question = response.data["active_questions"][0]
    assert question["interaction_mode"] == "single_select"
    assert question["options"] == [
        {
            "value": "low",
            "label": "I would need guidance to complete HTTP API Design",
            "score": 1,
        },
        {
            "value": "mid",
            "label": "I can handle common HTTP API Design work independently",
            "score": 3,
        },
        {
            "value": "high",
            "label": "I can make tradeoffs, debug edge cases, and lead HTTP API Design work",
            "score": 5,
        },
    ]


@pytest.mark.django_db
def test_assessment_detail_hides_internal_answer_keys_but_preserves_question_type(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)
    assessment = Assessment.objects.create(
        user=assessment_user,
        assessment_type="skills",
        target_career="Backend Developer",
        stage="stage_1",
        stage_one_questions=[
            {
                "id": "s1_q1",
                "stage": 1,
                "subskill_key": "http_api_design",
                "dimension_key": "backend_core",
                "question_type": "single_choice",
                "type": "multiple_choice",
                "interaction_mode": "single_select",
                "question": "Which endpoint shape best matches the update?",
                "category": "HTTP API Design",
                "competency": "HTTP API Design",
                "learning_objective": "Pick the most RESTful partial-update endpoint.",
                "options": [
                    {"id": "a", "value": "a", "label": "POST /users/update-profile"},
                    {"id": "b", "value": "b", "label": "PATCH /users/{id}"},
                    {"id": "c", "value": "c", "label": "GET /users/{id}?update=true"},
                    {"id": "d", "value": "d", "label": "PUT /profiles/search"},
                ],
                "answer_key": {
                    "correct_option_ids": ["b"],
                    "scoring": "single_best",
                },
                "explanation": "PATCH is the best fit for partial updates.",
                "scenario_context": "A client retries partial profile updates after intermittent timeouts.",
                "correct_answer_rationale": "PATCH preserves resource semantics for a partial update.",
                "option_rationales": [
                    {
                        "option_id": "a",
                        "is_correct": False,
                        "rationale": "POST with a custom verb hides the resource update semantics.",
                    },
                    {
                        "option_id": "b",
                        "is_correct": True,
                        "rationale": "PATCH is the standard partial update method for an existing resource.",
                    },
                    {
                        "option_id": "c",
                        "is_correct": False,
                        "rationale": "GET must remain side-effect free.",
                    },
                    {
                        "option_id": "d",
                        "is_correct": False,
                        "rationale": "The endpoint does not point at the resource being updated.",
                    },
                ],
                "validation_flags": [],
            }
        ],
        questions=[],
        responses=[],
        status="draft",
        ai_processing_status="completed",
        total_questions=5,
    )

    response = api_client.get(reverse("assessment-detail", kwargs={"pk": str(assessment.id)}))

    assert response.status_code == status.HTTP_200_OK
    question = response.data["active_questions"][0]
    assert question["question_type"] == "single_choice"
    assert "answer_key" not in question
    assert "explanation" not in question
    assert "scenario_context" not in question
    assert "correct_answer_rationale" not in question
    assert "option_rationales" not in question


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
