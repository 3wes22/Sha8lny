import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.roadmaps.models import RoadmapTemplate
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
