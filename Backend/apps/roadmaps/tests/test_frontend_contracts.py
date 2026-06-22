import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.progress.services import ProgressService
from apps.roadmaps.models import Roadmap, RoadmapTemplate
from apps.roadmaps.services import RoadmapService
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def roadmap_user(db):
    return User.objects.create_user(
        auth0_id="roadmap_auth0_id",
        email="roadmap@example.com",
        username="roadmap_user",
        full_name="Roadmap User",
        date_of_birth="1999-01-01",
    )


@pytest.fixture
def roadmap_template(db):
    return RoadmapTemplate.objects.create(
        title="Frontend Engineer Roadmap",
        slug="frontend-engineer-roadmap",
        description="A practical roadmap for frontend engineering.",
        short_description="Frontend focus",
        target_career="Frontend Engineer",
        career_level=RoadmapTemplate.ENTRY_LEVEL,
        estimated_duration_weeks=20,
        difficulty_level="intermediate",
        prerequisites=["HTML basics"],
        learning_outcomes=["Ship responsive interfaces"],
        is_published=True,
    )


@pytest.mark.django_db
def test_roadmap_detail_exposes_frontend_presentation_fields(api_client, roadmap_user, roadmap_template):
    api_client.force_authenticate(user=roadmap_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=roadmap_user,
        template=roadmap_template,
        customizations={"weekly_hours": 10},
    )

    response = api_client.get(reverse("roadmaps:roadmap-detail", args=[roadmap.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["presentation_mode"] == "atlas"
    assert response.data["journey_summary"]["next_action_title"]
    assert response.data["current_focus_node_id"]
    assert response.data["journey_nodes"]
    assert response.data["journey_nodes"][0]["node_type"] == "phase"


@pytest.mark.django_db
def test_roadmap_stats_exposes_next_action_summary(api_client, roadmap_user, roadmap_template):
    api_client.force_authenticate(user=roadmap_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=roadmap_user,
        template=roadmap_template,
        customizations={"weekly_hours": 12},
    )

    response = api_client.get(reverse("roadmaps:roadmap-stats", args=[roadmap.id]))

    assert response.status_code == status.HTTP_200_OK
    assert "current_focus_node_id" in response.data
    assert "next_action" in response.data
    assert response.data["next_action"]["title"]


@pytest.mark.django_db
def test_roadmap_stats_exposes_dashboard_progress_metrics(api_client, roadmap_user, roadmap_template):
    api_client.force_authenticate(user=roadmap_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=roadmap_user,
        template=roadmap_template,
        customizations={"weekly_hours": 8},
    )
    first_phase = roadmap.phases.order_by("order").first()
    first_milestone = first_phase.milestones.order_by("order").first()
    first_milestone.status = "completed"
    first_milestone.save(update_fields=["status", "updated_at"])

    progress = ProgressService.update_progress_metrics(roadmap_user, roadmap)
    progress.current_streak_days = 3
    progress.total_learning_hours = Decimal("6.50")
    progress.average_hours_per_week = Decimal("3.25")
    progress.save(
        update_fields=[
            "current_streak_days",
            "total_learning_hours",
            "average_hours_per_week",
            "updated_at",
        ]
    )

    response = api_client.get(reverse("roadmaps:roadmap-stats", args=[roadmap.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["roadmap_status"] == roadmap.status
    assert response.data["completed_courses"] == 0
    assert response.data["current_phase"]["id"] == str(first_phase.id)
    assert response.data["current_phase"]["title"] == first_phase.title
    assert response.data["pace"]["current_streak_days"] == 3
    assert response.data["pace"]["total_learning_hours"] == 6.5


@pytest.mark.django_db
def test_pending_roadmap_detail_exposes_generation_summary(api_client, roadmap_user):
    api_client.force_authenticate(user=roadmap_user)
    roadmap = Roadmap.objects.create(
        user=roadmap_user,
        title="Backend roadmap for Roadmap User",
        description="Personalized roadmap for Backend Engineer.",
        target_career="Backend Engineer",
        current_level="beginner",
        target_level="job-ready",
        estimated_duration_weeks=0,
        weekly_hours_commitment=10,
        status="draft",
        ai_processing_status="pending",
        metadata={"generation": {"source": "assessment_result", "version": "roadmap-generator-v1"}},
    )

    response = api_client.get(reverse("roadmaps:roadmap-detail", args=[roadmap.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["ai_processing_status"] == "pending"
    assert response.data["journey_summary"]["next_action_title"] == "Preparing personalized phases"
    assert response.data["journey_nodes"] == []


@pytest.mark.django_db
def test_serializer_exposes_assessment_baseline_fields():
    from decimal import Decimal
    from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
    from apps.roadmaps.serializers import RoadmapPhaseSerializer
    from apps.users.models import User

    user = User.objects.create_user(
        auth0_id="sc1", email="sc1@example.com", username="sc1",
        full_name="SC1", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="completed",
    )
    RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"), status="completed",
        completed_from_assessment=True,
    )

    data = RoadmapPhaseSerializer(phase).data
    assert data["milestones"][0]["completed_from_assessment"] is True
    assert data["baseline_from_assessment"] is True


@pytest.mark.django_db
def test_phase_baseline_false_when_no_milestones():
    from apps.roadmaps.models import Roadmap, RoadmapPhase
    from apps.roadmaps.serializers import RoadmapPhaseSerializer
    from apps.users.models import User

    user = User.objects.create_user(
        auth0_id="sc2", email="sc2@example.com", username="sc2",
        full_name="SC2", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="not_started",
    )

    data = RoadmapPhaseSerializer(phase).data
    assert data["milestones"] == []
    assert data["baseline_from_assessment"] is False


@pytest.mark.django_db
def test_phase_baseline_false_when_a_completed_milestone_is_not_from_assessment():
    from decimal import Decimal
    from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
    from apps.roadmaps.serializers import RoadmapPhaseSerializer
    from apps.users.models import User

    user = User.objects.create_user(
        auth0_id="sc3", email="sc3@example.com", username="sc3",
        full_name="SC3", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="completed",
    )
    RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"), status="completed",
        completed_from_assessment=True,
    )
    RoadmapMilestone.objects.create(
        phase=phase, title="Learn REST", description="", order=2,
        estimated_duration_hours=Decimal("10.00"), status="completed",
        completed_from_assessment=False,
    )

    data = RoadmapPhaseSerializer(phase).data
    assert len(data["milestones"]) == 2
    assert data["baseline_from_assessment"] is False


@pytest.mark.django_db
def test_phase_baseline_false_when_only_in_progress_milestones():
    from decimal import Decimal
    from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
    from apps.roadmaps.serializers import RoadmapPhaseSerializer
    from apps.users.models import User

    user = User.objects.create_user(
        auth0_id="sc4", email="sc4@example.com", username="sc4",
        full_name="SC4", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="in_progress",
    )
    RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"), status="in_progress",
        completed_from_assessment=False,
    )

    data = RoadmapPhaseSerializer(phase).data
    assert len(data["milestones"]) == 1
    assert data["baseline_from_assessment"] is False


@pytest.mark.django_db
def test_milestone_list_serializer_exposes_completed_from_assessment():
    from decimal import Decimal
    from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
    from apps.roadmaps.serializers import RoadmapMilestoneListSerializer
    from apps.users.models import User

    user = User.objects.create_user(
        auth0_id="sc5", email="sc5@example.com", username="sc5",
        full_name="SC5", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="advanced", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4, status="completed",
    )
    milestone = RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"), status="completed",
        completed_from_assessment=True,
    )

    data = RoadmapMilestoneListSerializer(milestone).data
    assert "completed_from_assessment" in data
    assert data["completed_from_assessment"] == milestone.completed_from_assessment
    assert data["completed_from_assessment"] is True
