"""
Tests for Assessment API endpoints.

Tests Phase 2 functionality:
- Assessment creation
- Question fetching
- Response submission
- Result retrieval
"""

import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from apps.core.ai_contracts import AIInvocationMetadata
from apps.users.models import User
from apps.assessments.models import Assessment, AssessmentResult


@pytest.mark.django_db
class TestAssessmentAPI:
    """Test assessment CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            auth0_id='test_auth0_id',
            username='testuser',
            full_name='Test User',
            date_of_birth=date.today() - timedelta(days=365 * 25),
            password='testpass123'
        )

        # Authenticate client
        self.client.force_authenticate(user=self.user)

    def test_create_assessment(self):
        """Test creating a new assessment queues question generation."""
        url = reverse('assessment-list')
        data = {
            'assessment_type': 'skills',
            'target_career': 'Software Engineer'
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['assessment_type'] == 'skills'
        assert response.data['target_career'] == 'Software Engineer'
        assert response.data['status'] == 'draft'
        assert response.data['stage'] == 'stage_1'
        assert response.data['generation_status'] in {'pending', 'completed'}
        assert response.data['ai_processing_status'] in {'pending', 'processing', 'completed'}
        assert response.data['total_questions'] == 10
        if response.data['ai_processing_status'] == 'completed':
            assert response.data['presentation']['submission_state'] == 'stage_1_ready'
            assert len(response.data['questions']) > 0
        else:
            assert response.data['questions'] == []
            assert response.data['presentation']['submission_state'] == 'stage_1_generating'

        assessment = Assessment.objects.get(id=response.data['id'])
        assert assessment.target_career == 'Software Engineer'
        assert assessment.ai_task_id

    def test_create_assessment_returns_201_when_stage_generation_fails(self, monkeypatch):
        """Eager generation failures must not turn assessment creation into HTTP 500."""
        def fail_generate_stage_one(*_args, **_kwargs):
            raise RuntimeError("simulated generation outage")

        monkeypatch.setattr(
            "apps.assessments.tasks.AssessmentAIService.generate_stage_one",
            fail_generate_stage_one,
        )

        url = reverse('assessment-list')
        response = self.client.post(
            url,
            {'assessment_type': 'skills', 'target_career': 'Backend Developer'},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['ai_processing_status'] == 'failed'
        assert response.data['presentation']['submission_state'] == 'failed'

    def test_create_assessment_unauthenticated(self):
        """Test creating assessment without authentication fails."""
        self.client.force_authenticate(user=None)

        url = reverse('assessment-list')
        data = {'assessment_type': 'skills'}

        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_user_assessments(self):
        """Test listing user's assessments."""
        # Create some assessments
        Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0
        )
        Assessment.objects.create(
            user=self.user,
            assessment_type='career_interests',
            questions=[],
            total_questions=0
        )

        url = reverse('assessment-list')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_get_latest_assessment(self):
        """Test getting user's latest assessment."""
        # Create assessments
        old_assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0
        )
        new_assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0
        )

        url = reverse('assessment-latest')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(new_assessment.id)

    def test_get_assessment_by_id(self):
        """Test retrieving specific assessment."""
        assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[{'id': 1, 'question': 'Test?', 'type': 'text'}],
            total_questions=1
        )

        url = reverse('assessment-detail', kwargs={'pk': str(assessment.id)})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(assessment.id)
        assert len(response.data['questions']) == 1

    def test_runtime_health_endpoint(self, monkeypatch):
        monkeypatch.setattr(
            "apps.assessments.views.get_ai_runtime_health",
            lambda: {
                "runtime": "gemini",
                "provider_available": True,
                "model_available": True,
                "settings": {"default_model": "gemini-2.5-flash-lite"},
            },
        )

        response = self.client.get(reverse("assessment-runtime-health"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["runtime"] == "gemini"
        assert response.data["provider_available"] is True
        assert response.data["model_available"] is True
        assert response.data["settings"]["default_model"] == "gemini-2.5-flash-lite"

    def test_preview_questions_returns_generation_metadata(self, monkeypatch):
        def fake_generate_stage_one(role_key, role_graph):
            return (
                [
                    {
                        "id": "s1_q1",
                        "stage": 1,
                        "subskill_key": "apis",
                        "dimension_key": "backend_core",
                        "question_text": "How comfortable are you with API design?",
                        "question_type": "multiple_choice",
                        "interaction_mode": "single_select",
                        "options": [],
                    }
                ],
                AIInvocationMetadata(
                    source="llm",
                    processing_time_ms=1200,
                    model="gemini-2.5-flash-lite",
                    provider="gemini",
                    version=role_graph.version,
                    trace_id="trace-preview-1",
                    fallback_used=False,
                ),
                {},
            )

        monkeypatch.setattr(
            "apps.assessments.views.AssessmentAIService.generate_stage_one",
            fake_generate_stage_one,
        )
        monkeypatch.setattr(
            "apps.assessments.views.get_ai_runtime_health",
            lambda: {
                "runtime": "gemini",
                "provider_available": True,
                "model_available": True,
                "settings": {"default_model": "gemini-2.5-flash-lite"},
            },
        )

        response = self.client.post(
            reverse("assessment-preview-questions"),
            {"target_career": "Backend Developer"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["target_career"] == "Backend Developer"
        assert response.data["role_key"] == "backend"
        assert response.data["question_count"] == 1
        assert response.data["metadata"]["model"] == "gemini-2.5-flash-lite"
        assert response.data["metadata"]["provider"] == "gemini"
        assert response.data["metadata"]["fallback_used"] is False
        assert response.data["runtime_health"]["provider_available"] is True
        assert response.data["questions"][0]["id"] == "s1_q1"

    def test_preview_questions_can_require_live_llm(self, monkeypatch):
        def fake_generate_stage_one(role_key, role_graph):
            return (
                [
                    {
                        "id": "s1_q1",
                        "stage": 1,
                        "subskill_key": "apis",
                        "dimension_key": "backend_core",
                        "question_text": "Fallback question",
                        "question_type": "multiple_choice",
                        "interaction_mode": "single_select",
                        "options": [],
                    }
                ],
                AIInvocationMetadata(
                    source="fallback",
                    processing_time_ms=12,
                    model=None,
                    provider="gemini",
                    version=role_graph.version,
                    trace_id="trace-preview-fallback",
                    fallback_used=True,
                    error_code="AIServiceError",
                ),
                {},
            )

        monkeypatch.setattr(
            "apps.assessments.views.AssessmentAIService.generate_stage_one",
            fake_generate_stage_one,
        )
        monkeypatch.setattr(
            "apps.assessments.views.get_ai_runtime_health",
            lambda: {
                "runtime": "gemini",
                "provider_available": False,
                "model_available": False,
                "settings": {"default_model": "gemini-2.5-flash-lite"},
            },
        )

        response = self.client.post(
            reverse("assessment-preview-questions"),
            {"target_career": "Backend Developer", "require_live_llm": True},
            format="json",
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.data["error"] == "Live Gemini generation is unavailable"
        assert response.data["metadata"]["fallback_used"] is True
        assert response.data["runtime_health"]["provider_available"] is False

    def test_submit_assessment_responses(self):
        """Test submitting assessment responses queues async evaluation."""
        assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[
                {'id': 1, 'question': 'Rate Python skills', 'type': 'scale'},
                {'id': 2, 'question': 'Years of experience', 'type': 'text'}
            ],
            total_questions=2
        )

        url = reverse('assessment-submit', kwargs={'pk': str(assessment.id)})
        data = {
            'responses': [
                {'question_id': 1, 'answer': 4},
                {'question_id': 2, 'answer': '3 years'}
            ]
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'message' in response.data
        assert 'assessment' in response.data
        assert response.data['submission_state'] == 'processing'
        assert response.data['result_id'] is None

        # Verify assessment was updated
        assessment.refresh_from_db()
        assert assessment.status == 'completed'
        assert assessment.answered_questions == 2
        assert assessment.ai_processing_status == 'completed'
        assert AssessmentResult.objects.filter(assessment=assessment, is_deleted=False).exists()

    def test_submit_already_completed_assessment(self):
        """Test submitting responses to already completed assessment fails."""
        assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[{'id': 1, 'question': 'Test?', 'type': 'text'}],
            total_questions=1,
            status='completed'
        )

        url = reverse('assessment-submit', kwargs={'pk': str(assessment.id)})
        data = {
            'responses': [{'question_id': 1, 'answer': 'test'}]
        }

        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_get_assessment_result(self):
        """Test retrieving assessment result."""
        assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0,
            status='completed',
            ai_processing_status='completed'
        )

        # Create result
        result = AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=85.5,
            skill_scores={'python': 90, 'django': 80},
            strengths=['Problem solving', 'Quick learner'],
            areas_for_improvement=['Testing', 'DevOps'],
            recommended_careers=[
                {'title': 'Backend Developer', 'match_score': 90, 'reasoning': 'Good fit'}
            ],
            ai_insights='Strong technical skills',
            llm_model_used='mock-v1',
            ai_confidence_score=75.0
        )

        url = reverse('assessment-result', kwargs={'pk': str(assessment.id)})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(result.id)
        assert response.data['overall_score'] == '85.50'
        assert 'strengths' in response.data
        assert 'recommended_careers' in response.data

    def test_get_result_for_incomplete_assessment(self):
        """Test getting result for incomplete assessment fails."""
        assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0,
            status='draft'
        )

        url = reverse('assessment-result', kwargs={'pk': str(assessment.id)})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_get_result_while_processing(self):
        """Test getting result while AI is processing returns 202."""
        assessment = Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0,
            status='completed',
            ai_processing_status='pending'
        )

        url = reverse('assessment-result', kwargs={'pk': str(assessment.id)})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert 'message' in response.data

    def test_filter_assessments_by_type(self):
        """Test filtering assessments by assessment_type."""
        Assessment.objects.create(
            user=self.user,
            assessment_type='skills',
            questions=[],
            total_questions=0
        )
        Assessment.objects.create(
            user=self.user,
            assessment_type='career_interests',
            questions=[],
            total_questions=0
        )

        url = reverse('assessment-list')
        response = self.client.get(url, {'assessment_type': 'skills'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['assessment_type'] == 'skills'

    def test_user_can_only_access_own_assessments(self):
        """Test users cannot access other users' assessments."""
        other_user = User.objects.create_user(
            email='other@example.com',
            auth0_id='other_auth0_id',
            username='otheruser',
            full_name='Other User',
            date_of_birth=date.today() - timedelta(days=365 * 30),
            password='otherpass123'
        )

        other_assessment = Assessment.objects.create(
            user=other_user,
            assessment_type='skills',
            questions=[],
            total_questions=0
        )

        url = reverse('assessment-detail', kwargs={'pk': str(other_assessment.id)})
        response = self.client.get(url)

        # Should return 404 since queryset filters by user
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_assessment_history(self):
        """Test getting assessment history."""
        # Create multiple assessments
        for i in range(3):
            Assessment.objects.create(
                user=self.user,
                assessment_type='skills',
                questions=[],
                total_questions=0
            )

        url = reverse('assessment-history')
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_assessment_history_with_limit(self):
        """Test assessment history respects limit parameter."""
        for i in range(5):
            Assessment.objects.create(
                user=self.user,
                assessment_type='skills',
                questions=[],
                total_questions=0
            )

        url = reverse('assessment-history')
        response = self.client.get(url, {'limit': 2})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2


@pytest.mark.django_db
class TestAssessmentQuestionGeneration:
    """Test assessment question generation."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Set up test fixtures."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            auth0_id='test_auth0_id',
            username='testuser',
            full_name='Test User',
            date_of_birth=date.today() - timedelta(days=365 * 25),
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_assessment_has_predefined_questions(self):
        """Test generated assessment detail exposes the fallback/generated questions."""
        url = reverse('assessment-list')
        data = {'assessment_type': 'skills'}

        response = self.client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        detail_response = self.client.get(reverse('assessment-detail', kwargs={'pk': response.data['id']}))
        assert detail_response.status_code == status.HTTP_200_OK
        questions = detail_response.data['questions']

        assert detail_response.data['stage'] == 'stage_1'
        assert detail_response.data['presentation']['submission_state'] == 'stage_1_ready'
        assert len(questions) == 5
        assert all('id' in q for q in questions)
        assert all('question' in q for q in questions)
        assert all('type' in q for q in questions)
        assert all('category' in q for q in questions)

    def test_question_types_present(self):
        """Test generated assessment detail contains different question types."""
        url = reverse('assessment-list')
        data = {'assessment_type': 'skills'}

        response = self.client.post(url, data, format='json')
        detail_response = self.client.get(reverse('assessment-detail', kwargs={'pk': response.data['id']}))
        questions = detail_response.data['questions']

        question_types = {q['type'] for q in questions}

        assert 'multiple_choice' in question_types
