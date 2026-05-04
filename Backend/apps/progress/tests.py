from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.notifications.signals import roadmap_completed
from apps.progress.models import MilestoneAchievement, UserProgress
from apps.progress.services import TimeLogService
from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapTemplate
from apps.roadmaps.services import RoadmapService
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def progress_user(db):
    return User.objects.create_user(
        auth0_id="progress_auth0_id",
        email="progress@example.com",
        username="progress_user",
        full_name="Progress User",
        date_of_birth="1997-01-01",
    )


@pytest.fixture
def roadmap_template(db):
    return RoadmapTemplate.objects.create(
        title="Backend Engineer Roadmap",
        slug="progress-backend-engineer-roadmap",
        description="A practical roadmap for backend engineering.",
        short_description="Backend focus",
        target_career="Backend Engineer",
        career_level=RoadmapTemplate.ENTRY_LEVEL,
        estimated_duration_weeks=20,
        difficulty_level="intermediate",
        prerequisites=["Python basics"],
        learning_outcomes=["Ship backend services"],
        is_published=True,
    )


def _first_phase_and_milestones(roadmap):
    phase = roadmap.phases.order_by("order").first()
    milestones = list(phase.milestones.order_by("order")[:2])
    assert phase is not None
    assert len(milestones) >= 2
    return phase, milestones[0], milestones[1]


@pytest.mark.django_db
def test_progress_by_roadmap_reflects_roadmap_updates(api_client, progress_user, roadmap_template):
    api_client.force_authenticate(user=progress_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=progress_user,
        template=roadmap_template,
    )
    phase, first_milestone, second_milestone = _first_phase_and_milestones(roadmap)

    response = api_client.put(
        reverse("roadmaps:roadmap-progress", args=[roadmap.id]),
        {"milestone_id": str(first_milestone.id), "status": "completed"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK

    progress_response = api_client.get(reverse("progress:progress-by-roadmap", args=[roadmap.id]))

    assert progress_response.status_code == status.HTTP_200_OK
    assert progress_response.data["roadmap"]["id"] == str(roadmap.id)
    assert progress_response.data["milestones_completed"] == 1
    assert Decimal(str(progress_response.data["overall_completion_percentage"])) > 0
    assert str(progress_response.data["current_phase"]) == str(phase.id)
    assert str(progress_response.data["current_milestone"]) == str(second_milestone.id)
    assert progress_response.data["current_streak_days"] == 1

    roadmap.refresh_from_db()
    assert roadmap.status == "in_progress"


@pytest.mark.django_db
def test_progress_stats_include_hours_and_streak_for_active_roadmap(
    api_client,
    progress_user,
    roadmap_template,
):
    api_client.force_authenticate(user=progress_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=progress_user,
        template=roadmap_template,
    )
    _phase, first_milestone, _second_milestone = _first_phase_and_milestones(roadmap)

    progress_update_response = api_client.put(
        reverse("roadmaps:roadmap-progress", args=[roadmap.id]),
        {"milestone_id": str(first_milestone.id), "status": "completed"},
        format="json",
    )

    assert progress_update_response.status_code == status.HTTP_200_OK

    finished_at = timezone.now()
    TimeLogService.log_learning_session(
        user=progress_user,
        roadmap=roadmap,
        started_at=finished_at - timedelta(hours=2),
        ended_at=finished_at,
        activity_type="project",
    )

    response = api_client.get(reverse("progress:stats"))

    assert response.status_code == status.HTTP_200_OK
    assert Decimal(str(response.data["total_learning_hours"])) == Decimal("2.00")
    assert Decimal(str(response.data["this_week_hours"])) == Decimal("2.00")
    assert response.data["current_streak_days"] == 1
    assert response.data["roadmaps_in_progress"] == 1
    assert response.data["last_activity_date"] is not None


@pytest.mark.django_db
def test_unmarking_milestone_clears_active_achievement_and_stats(
    api_client,
    progress_user,
    roadmap_template,
):
    api_client.force_authenticate(user=progress_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=progress_user,
        template=roadmap_template,
    )
    _phase, first_milestone, _second_milestone = _first_phase_and_milestones(roadmap)
    url = reverse("roadmaps:roadmap-progress", args=[roadmap.id])

    complete_response = api_client.put(
        url,
        {"milestone_id": str(first_milestone.id), "status": "completed"},
        format="json",
    )
    assert complete_response.status_code == status.HTTP_200_OK
    assert MilestoneAchievement.objects.filter(user=progress_user, milestone=first_milestone).count() == 1

    undo_response = api_client.put(
        url,
        {"milestone_id": str(first_milestone.id), "status": "not_started"},
        format="json",
    )

    assert undo_response.status_code == status.HTTP_200_OK
    first_milestone.refresh_from_db()
    assert first_milestone.status == RoadmapMilestone.NOT_STARTED
    assert first_milestone.completed_at is None
    assert MilestoneAchievement.objects.filter(user=progress_user, milestone=first_milestone).count() == 0

    progress = UserProgress.objects.get(user=progress_user, roadmap=roadmap)
    assert progress.milestones_completed == 0
    assert progress.overall_completion_percentage == Decimal("0.00")

    stats_response = api_client.get(reverse("progress:stats"))
    assert stats_response.status_code == status.HTTP_200_OK
    assert stats_response.data["total_milestones_achieved"] == 0


@pytest.mark.django_db
def test_roadmap_stats_read_does_not_persist_progress_or_emit_completion(
    api_client,
    progress_user,
    roadmap_template,
):
    api_client.force_authenticate(user=progress_user)
    roadmap = RoadmapService.create_roadmap_from_template(
        user=progress_user,
        template=roadmap_template,
    )
    RoadmapMilestone.objects.filter(phase__roadmap=roadmap).update(
        status=RoadmapMilestone.COMPLETED,
        completed_at=timezone.now(),
    )
    events = []

    def capture_completion(**kwargs):
        events.append(kwargs["instance"].id)

    roadmap_completed.connect(capture_completion, dispatch_uid="test-roadmap-stats-read-only")
    try:
        first_response = api_client.get(reverse("roadmaps:roadmap-stats", args=[roadmap.id]))
        second_response = api_client.get(reverse("roadmaps:roadmap-stats", args=[roadmap.id]))
    finally:
        roadmap_completed.disconnect(dispatch_uid="test-roadmap-stats-read-only")

    assert first_response.status_code == status.HTTP_200_OK
    assert second_response.status_code == status.HTTP_200_OK
    assert first_response.data["completion_percentage"] == 100.0
    assert first_response.data["roadmap_status"] == Roadmap.COMPLETED
    assert events == []

    roadmap.refresh_from_db()
    assert roadmap.status == Roadmap.DRAFT
    assert roadmap.completion_percentage == Decimal("0.00")
