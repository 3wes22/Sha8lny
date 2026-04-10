"""
Tests for Roadmaps API endpoints.

Test Coverage:
- RoadmapTemplate endpoints (list, retrieve)
- Roadmap creation from template
- Roadmap CRUD operations
- Progress tracking (milestone completion)
- Statistics endpoint
"""

import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.models import Assessment, AssessmentResult
from apps.core.ai_settings import OLLAMA_MODEL
from apps.users.models import User
from apps.roadmaps.models import (
    RoadmapTemplate, Roadmap, RoadmapPhase,
    RoadmapMilestone
)


@pytest.fixture
def api_client():
    """API client fixture."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        auth0_id='test_auth0_123',
        email='testuser@example.com',
        username='testuser',
        full_name='Test User',
        date_of_birth='1990-01-01'
    )


@pytest.fixture
def roadmap_template(db):
    """Create a roadmap template."""
    return RoadmapTemplate.objects.create(
        title='Backend Developer Roadmap',
        slug='backend-developer-roadmap',
        description='Comprehensive backend development path',
        short_description='Learn backend development',
        target_career='Backend Developer',
        career_level=RoadmapTemplate.ENTRY_LEVEL,
        estimated_duration_weeks=24,
        difficulty_level='intermediate',
        prerequisites=['Basic programming knowledge'],
        learning_outcomes=['Build REST APIs', 'Work with databases'],
        is_published=True
    )


@pytest.mark.django_db
class TestRoadmapTemplateAPI:
    """Tests for RoadmapTemplate API endpoints."""

    def test_list_templates(self, api_client, test_user, roadmap_template):
        """Test listing published roadmap templates."""
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:template-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['title'] == 'Backend Developer Roadmap'

    def test_retrieve_template(self, api_client, test_user, roadmap_template):
        """Test retrieving a specific template."""
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:template-detail', args=[roadmap_template.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'Backend Developer Roadmap'
        assert response.data['target_career'] == 'Backend Developer'

    def test_filter_templates_by_career(self, api_client, test_user, roadmap_template):
        """Test filtering templates by career."""
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:template-by-career')
        response = api_client.get(url, {'career': 'Backend'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['target_career'] == 'Backend Developer'

    def test_only_published_templates_shown(self, api_client, test_user, db):
        """Test that only published templates are returned."""
        # Create an unpublished template
        RoadmapTemplate.objects.create(
            title='Unpublished Roadmap',
            slug='unpublished-roadmap',
            target_career='Test Career',
            career_level=RoadmapTemplate.ENTRY_LEVEL,
            estimated_duration_weeks=10,
            difficulty_level='beginner',
            is_published=False
        )

        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:template-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should not include unpublished template
        assert len(response.data['results']) == 0


@pytest.mark.django_db
class TestRoadmapCreationAPI:
    """Tests for Roadmap creation endpoints."""

    def test_create_roadmap_from_template(self, api_client, test_user, roadmap_template):
        """Test creating a roadmap from a template."""
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-list')
        data = {
            'template_id': str(roadmap_template.id),
            'weekly_hours_commitment': 15
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        assert response.data['target_career'] == 'Backend Developer'
        assert response.data['status'] == 'draft'
        assert response.data['ai_processing_status'] == 'completed'

        # Verify roadmap was created in database
        roadmap = Roadmap.objects.get(id=response.data['id'])
        assert roadmap.user == test_user
        assert roadmap.template == roadmap_template
        assert roadmap.weekly_hours_commitment == 15

        # Verify phases and milestones were created
        assert roadmap.phases.count() == 3  # Backend Developer should have 3 phases
        first_phase = roadmap.phases.first()
        assert first_phase.milestones.count() >= 3  # Each phase should have milestones

    def test_create_roadmap_increments_template_usage(
        self, api_client, test_user, roadmap_template
    ):
        """Test that creating a roadmap increments template usage count."""
        initial_count = roadmap_template.usage_count

        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-list')
        data = {
            'template_id': str(roadmap_template.id),
            'weekly_hours_commitment': 10
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Refresh template and check usage count
        roadmap_template.refresh_from_db()
        assert roadmap_template.usage_count == initial_count + 1

    def test_create_roadmap_invalid_template(self, api_client, test_user):
        """Test creating roadmap with invalid template ID."""
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-list')
        data = {
            'template_id': '00000000-0000-0000-0000-000000000000',
            'weekly_hours_commitment': 10
        }

        response = api_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_ai_roadmap_from_assessment_defaults(self, api_client, test_user):
        """Test creating an AI roadmap from an assessment result without extra manual fields."""
        api_client.force_authenticate(user=test_user)

        assessment = Assessment.objects.create(
            user=test_user,
            assessment_type='skills',
            status='completed',
            ai_processing_status='completed',
            total_questions=6,
            answered_questions=6,
        )
        assessment_result = AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=Decimal('68.00'),
            skill_scores={
                'technical': {'Python': 82, 'SQL': 71},
                'soft': {'Communication': 65},
            },
            strengths=['Problem solving', 'Consistency'],
            areas_for_improvement=['System design', 'Testing discipline'],
            recommended_careers=[
                {
                    'title': 'Backend Developer',
                    'match_score': 88,
                    'reasoning': 'Strong technical baseline with clear backend growth potential.',
                }
            ],
            recommended_learning_paths=[
                {'skill': 'Django', 'priority': 'high'},
                {'skill': 'PostgreSQL', 'priority': 'medium'},
            ],
            ai_insights='You have solid coding foundations but need stronger backend architecture depth.',
            llm_model_used='assessment-mock-v1',
        )

        response = api_client.post(
            reverse('roadmaps:roadmap-list'),
            {'assessment_id': str(assessment_result.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['target_career'] == 'Backend Developer'
        assert response.data['current_level'] == 'intermediate'
        assert response.data['target_level'] == 'job-ready'
        assert response.data['ai_processing_status'] == 'pending'

        roadmap = Roadmap.objects.get(id=response.data['id'])
        roadmap.refresh_from_db()
        assert roadmap.assessment == assessment_result
        assert roadmap.ai_processed_at is not None
        assert roadmap.llm_model_used == OLLAMA_MODEL
        assert roadmap.metadata['generation']['source'] == 'assessment_result'
        assert roadmap.metadata['generation']['version'] == 'roadmap-generator-v1'
        assert roadmap.metadata['generation']['runtime_version']
        assert roadmap.ai_insights['strengths'] == ['Problem solving', 'Consistency']
        assert roadmap.ai_insights['priority_skills'] == ['Django', 'PostgreSQL']
        assert roadmap.phases.count() == 3

        milestone_titles = list(
            RoadmapMilestone.objects.filter(phase__roadmap=roadmap)
            .order_by('phase__order', 'order')
            .values_list('title', flat=True)
        )
        assert any('Django' in title for title in milestone_titles)
        assert any('System design' in title for title in milestone_titles)

    def test_create_ai_roadmap_reuses_existing_assessment_draft(self, api_client, test_user):
        """Test repeated assessment-based generation reuses the existing roadmap draft."""
        api_client.force_authenticate(user=test_user)

        assessment = Assessment.objects.create(
            user=test_user,
            assessment_type='skills',
            status='completed',
            ai_processing_status='completed',
            total_questions=6,
            answered_questions=6,
        )
        assessment_result = AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=Decimal('82.00'),
            skill_scores={'technical': {'React': 88, 'TypeScript': 78}},
            strengths=['Frontend implementation'],
            areas_for_improvement=['Testing'],
            recommended_careers=[
                {'title': 'Frontend Engineer', 'match_score': 91, 'reasoning': 'Strong UI implementation signal.'}
            ],
            recommended_learning_paths=[{'skill': 'React Testing Library', 'priority': 'high'}],
            ai_insights='You are close to frontend job readiness but need stronger testing habits.',
            llm_model_used='assessment-mock-v1',
        )

        url = reverse('roadmaps:roadmap-list')
        first_response = api_client.post(url, {'assessment_id': str(assessment_result.id)}, format='json')
        second_response = api_client.post(url, {'assessment_id': str(assessment_result.id)}, format='json')

        assert first_response.status_code == status.HTTP_202_ACCEPTED
        assert second_response.status_code == status.HTTP_202_ACCEPTED
        assert second_response.data['id'] == first_response.data['id']
        assert Roadmap.objects.filter(user=test_user, assessment=assessment_result, is_deleted=False).count() == 1

    def test_create_ai_roadmap_prefers_explicit_assessment_target_career(self, api_client, test_user):
        """Assessment-selected target career should outrank mock recommended careers."""
        api_client.force_authenticate(user=test_user)

        assessment = Assessment.objects.create(
            user=test_user,
            assessment_type='skills',
            target_career='Frontend Developer',
            status='completed',
            ai_processing_status='completed',
            total_questions=6,
            answered_questions=6,
        )
        assessment_result = AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=Decimal('74.00'),
            skill_scores={'technical': {'React': 84}},
            strengths=['UI implementation'],
            areas_for_improvement=['Testing discipline'],
            recommended_careers=[
                {'title': 'Software Engineer', 'match_score': 91, 'reasoning': 'Generic mock output.'}
            ],
            recommended_learning_paths=[{'skill': 'React Testing Library', 'priority': 'high'}],
            ai_insights='Frontend-oriented signal with a testing gap.',
            llm_model_used='assessment-mock-v1',
        )

        response = api_client.post(
            reverse('roadmaps:roadmap-list'),
            {'assessment_id': str(assessment_result.id)},
            format='json',
        )

        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.data['target_career'] == 'Frontend Developer'


@pytest.mark.django_db
class TestRoadmapProgressAPI:
    """Tests for progress tracking endpoints."""

    @pytest.fixture
    def roadmap_with_phases(self, test_user, roadmap_template):
        """Create a roadmap with phases and milestones."""
        from apps.roadmaps.services import RoadmapService

        roadmap = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template,
            customizations={'weekly_hours': 15}
        )
        return roadmap

    def test_update_milestone_progress(
        self, api_client, test_user, roadmap_with_phases
    ):
        """Test marking a milestone as completed."""
        api_client.force_authenticate(user=test_user)

        # Get first milestone
        first_phase = roadmap_with_phases.phases.first()
        first_milestone = first_phase.milestones.first()

        url = reverse('roadmaps:roadmap-progress', args=[roadmap_with_phases.id])
        data = {
            'milestone_id': str(first_milestone.id),
            'status': 'completed'
        }

        response = api_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

        # Verify milestone was updated
        first_milestone.refresh_from_db()
        assert first_milestone.status == 'completed'
        assert first_milestone.completed_at is not None

    def test_complete_all_milestones_completes_phase(
        self, api_client, test_user, roadmap_with_phases
    ):
        """Test that completing all milestones auto-completes the phase."""
        api_client.force_authenticate(user=test_user)

        first_phase = roadmap_with_phases.phases.first()
        milestones = first_phase.milestones.all()

        url = reverse('roadmaps:roadmap-progress', args=[roadmap_with_phases.id])

        # Complete all milestones in the phase
        for milestone in milestones:
            data = {
                'milestone_id': str(milestone.id),
                'status': 'completed'
            }
            response = api_client.put(url, data, format='json')
            assert response.status_code == status.HTTP_200_OK

        # Verify phase is now completed
        first_phase.refresh_from_db()
        assert first_phase.status == 'completed'
        assert first_phase.completion_percentage == Decimal('100.00')

    def test_update_phase_progress(
        self, api_client, test_user, roadmap_with_phases
    ):
        """Test updating phase status directly."""
        api_client.force_authenticate(user=test_user)

        first_phase = roadmap_with_phases.phases.first()

        url = reverse('roadmaps:roadmap-progress', args=[roadmap_with_phases.id])
        data = {
            'phase_id': str(first_phase.id),
            'status': 'in_progress'
        }

        response = api_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        # Verify phase was updated
        first_phase.refresh_from_db()
        assert first_phase.status == 'in_progress'
        assert first_phase.started_at is not None

        # Verify roadmap status was also updated
        roadmap_with_phases.refresh_from_db()
        assert roadmap_with_phases.status == 'in_progress'


@pytest.mark.django_db
class TestRoadmapStatsAPI:
    """Tests for roadmap statistics endpoint."""

    @pytest.fixture
    def roadmap_with_progress(self, test_user, roadmap_template):
        """Create a roadmap with some completed milestones."""
        from apps.roadmaps.services import RoadmapService

        roadmap = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )

        # Complete first milestone
        first_phase = roadmap.phases.first()
        first_milestone = first_phase.milestones.first()
        first_milestone.status = 'completed'
        first_milestone.save()

        return roadmap

    def test_get_roadmap_stats(
        self, api_client, test_user, roadmap_with_progress
    ):
        """Test retrieving roadmap statistics."""
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-stats', args=[roadmap_with_progress.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total_phases' in response.data
        assert 'completed_phases' in response.data
        assert 'total_milestones' in response.data
        assert 'completed_milestones' in response.data
        assert 'total_courses' in response.data
        assert 'estimated_total_hours' in response.data
        assert 'completion_percentage' in response.data

        # Verify counts
        assert response.data['total_phases'] == 3
        assert response.data['completed_milestones'] == 1


@pytest.mark.django_db
class TestRoadmapActivateAPI:
    """Tests for roadmap activation endpoint."""

    def test_activate_roadmap(
        self, api_client, test_user, roadmap_template
    ):
        """Test activating a roadmap."""
        from apps.roadmaps.services import RoadmapService

        roadmap = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )

        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-activate', args=[roadmap.id])
        response = api_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_200_OK

        # Verify roadmap status was updated
        roadmap.refresh_from_db()
        assert roadmap.status == 'active'
        assert roadmap.started_at is not None


@pytest.mark.django_db
class TestRoadmapListAPI:
    """Tests for roadmap list and filtering."""

    def test_list_user_roadmaps(
        self, api_client, test_user, roadmap_template
    ):
        """Test listing user's roadmaps."""
        from apps.roadmaps.services import RoadmapService

        # Create two roadmaps
        roadmap1 = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )
        roadmap2 = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )

        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2

    def test_filter_roadmaps_by_status(
        self, api_client, test_user, roadmap_template
    ):
        """Test filtering roadmaps by status."""
        from apps.roadmaps.services import RoadmapService

        roadmap1 = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )
        roadmap2 = RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )

        # Activate one roadmap
        roadmap1.status = 'active'
        roadmap1.save()

        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-list')
        response = api_client.get(url, {'status': 'active'})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(roadmap1.id)

    def test_users_only_see_own_roadmaps(
        self, api_client, test_user, roadmap_template, db
    ):
        """Test that users only see their own roadmaps."""
        from apps.roadmaps.services import RoadmapService

        # Create another user
        other_user = User.objects.create_user(
            auth0_id='other_auth0_456',
            email='other@example.com',
            username='otheruser',
            full_name='Other User',
            date_of_birth='1995-01-01'
        )

        # Create roadmap for test_user
        RoadmapService.create_roadmap_from_template(
            user=test_user,
            template=roadmap_template
        )

        # Create roadmap for other_user
        RoadmapService.create_roadmap_from_template(
            user=other_user,
            template=roadmap_template
        )

        # Authenticate as test_user
        api_client.force_authenticate(user=test_user)

        url = reverse('roadmaps:roadmap-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should only see own roadmap
        assert len(response.data['results']) == 1
