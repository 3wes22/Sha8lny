from decimal import Decimal

import pytest

from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
from apps.users.models import User


@pytest.mark.django_db
def test_milestone_completed_from_assessment_defaults_false():
    user = User.objects.create_user(
        auth0_id="m1", email="m1@example.com", username="m1",
        full_name="M1", date_of_birth="1997-01-01",
    )
    roadmap = Roadmap.objects.create(
        user=user, title="R", target_career="Backend Developer",
        current_level="beginner", target_level="job-ready",
        estimated_duration_weeks=12, status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap, title="Foundations", description="", order=1,
        estimated_duration_weeks=4,
    )
    milestone = RoadmapMilestone.objects.create(
        phase=phase, title="Learn HTTP", description="", order=1,
        estimated_duration_hours=Decimal("10.00"),
    )
    assert milestone.completed_from_assessment is False

    milestone.completed_from_assessment = True
    milestone.save(update_fields=["completed_from_assessment", "updated_at"])
    milestone.refresh_from_db()
    assert milestone.completed_from_assessment is True
