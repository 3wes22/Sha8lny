from decimal import Decimal
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

from apps.assessments.models import Assessment
from apps.progress.models import CourseCompletion, TimeLog, UserProgress
from apps.roadmaps.models import Roadmap, RoadmapMilestone
from apps.users.management.commands.seed_graduation_demo import (
    NEW_USER_EMAIL,
    RETURNING_USER_EMAIL,
)
from apps.users.models import User


def _run_seed(**kwargs):
    """Seed with the LLM forced offline so the deterministic assessment-aware
    ladder is exercised hermetically (no live Gemini call / 429 retries)."""
    with patch(
        "apps.roadmaps.ai_pipeline.GemmaClient.generate_structured",
        side_effect=RuntimeError("offline"),
    ):
        call_command("seed_graduation_demo", **kwargs)


def _seed_course_catalog():
    """Minimal real-shape catalog so course matching attaches a course during
    seeding (the deterministic matcher needs role-tagged courses to rank)."""
    from apps.courses.matching import CourseCatalog
    from apps.courses.models import Course, CoursePlatform

    platform = CoursePlatform.objects.create(
        name="Coursera",
        slug="coursera",
        website_url="https://www.coursera.org",
        integration_type=CoursePlatform.SCRAPING,
    )
    for index, (title, skills) in enumerate(
        [
            ("Databases and SQL for Backend Engineers", ["SQL", "Database Design", "PostgreSQL"]),
            ("Building REST APIs with Python", ["REST API", "Python", "Backend"]),
        ]
    ):
        Course.objects.create(
            platform=platform,
            external_id=f"learn/backend-{index}",
            title=title,
            slug=f"backend-{index}",
            description="Hands-on backend coursework.",
            url=f"https://www.coursera.org/learn/backend-{index}",
            level="intermediate",
            rating=Decimal("4.70"),
            total_enrollments=10000,
            is_published=True,
            metadata={"skills": skills, "roles": ["backend"]},
        )
    CourseCatalog.reset()  # avoid cross-test staleness from the module-level cache


@pytest.mark.django_db
def test_seed_graduation_demo_creates_evaluator_accounts():
    stdout = StringIO()

    _seed_course_catalog()
    _run_seed(stdout=stdout)

    new_user = User.objects.get(email=NEW_USER_EMAIL)
    returning_user = User.objects.get(email=RETURNING_USER_EMAIL)

    assert new_user.roadmaps.count() == 0
    assert new_user.assessments.count() == 0

    assessment = Assessment.objects.get(user=returning_user)
    roadmap = Roadmap.objects.get(user=returning_user)
    progress = UserProgress.objects.get(user=returning_user, roadmap=roadmap)

    assert assessment.status == "completed"
    assert roadmap.status == "active"
    assert roadmap.assessment_id == assessment.result.id

    # Roadmap is generated through the AI/ladder path (5 bands) and the
    # advanced assessment greys the lower bands as "already mastered".
    assert roadmap.current_level == "advanced"
    phases = list(roadmap.phases.order_by("order"))
    assert len(phases) == 5
    foundations = phases[0]
    assert foundations.status == RoadmapMilestone.COMPLETED
    foundation_milestones = list(foundations.milestones.all())
    assert foundation_milestones
    assert all(m.completed_from_assessment for m in foundation_milestones)

    # Real, in-plan progress also exists: a completed milestone that is NOT
    # assessment-derived (distinct from the greyed bands).
    assert RoadmapMilestone.objects.filter(
        phase__roadmap=roadmap,
        status=RoadmapMilestone.COMPLETED,
        completed_from_assessment=False,
    ).exists()

    # 8 milestones pre-passed from the assessment (Foundations + Core) + 1 real.
    assert progress.milestones_completed == 9
    assert progress.courses_completed == 1
    assert progress.current_phase is not None
    assert progress.current_milestone is not None
    assert progress.current_streak_days == 4
    assert progress.total_learning_hours == Decimal("7.50")
    assert CourseCompletion.objects.filter(user=returning_user).count() == 1
    assert TimeLog.objects.filter(user=returning_user, roadmap=roadmap).count() == 4


@pytest.mark.django_db
def test_seed_graduation_demo_is_idempotent():
    _seed_course_catalog()
    _run_seed()
    _run_seed()

    assert User.objects.filter(email__in=[NEW_USER_EMAIL, RETURNING_USER_EMAIL]).count() == 2

    returning_user = User.objects.get(email=RETURNING_USER_EMAIL)
    new_user = User.objects.get(email=NEW_USER_EMAIL)

    assert new_user.roadmaps.count() == 0
    assert Assessment.objects.filter(user=returning_user).count() == 1
    assert Roadmap.objects.filter(user=returning_user).count() == 1
    assert UserProgress.objects.filter(user=returning_user).count() == 1
    assert CourseCompletion.objects.filter(user=returning_user).count() == 1
    assert TimeLog.objects.filter(user=returning_user).count() == 4
