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
