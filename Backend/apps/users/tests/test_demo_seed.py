from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command

from apps.assessments.models import Assessment
from apps.progress.models import CourseCompletion, TimeLog, UserProgress
from apps.roadmaps.models import Roadmap
from apps.users.management.commands.seed_graduation_demo import (
    NEW_USER_EMAIL,
    RETURNING_USER_EMAIL,
)
from apps.users.models import User


@pytest.mark.django_db
def test_seed_graduation_demo_creates_evaluator_accounts():
    stdout = StringIO()

    call_command("seed_graduation_demo", stdout=stdout)

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
    assert progress.milestones_completed == 3
    assert progress.courses_completed == 2
    assert progress.current_phase is not None
    assert progress.current_milestone is not None
    assert progress.current_streak_days == 4
    assert progress.total_learning_hours == Decimal("7.50")
    assert CourseCompletion.objects.filter(user=returning_user).count() == 2
    assert TimeLog.objects.filter(user=returning_user, roadmap=roadmap).count() == 4


@pytest.mark.django_db
def test_seed_graduation_demo_is_idempotent():
    call_command("seed_graduation_demo")
    call_command("seed_graduation_demo")

    assert User.objects.filter(email__in=[NEW_USER_EMAIL, RETURNING_USER_EMAIL]).count() == 2

    returning_user = User.objects.get(email=RETURNING_USER_EMAIL)
    new_user = User.objects.get(email=NEW_USER_EMAIL)

    assert new_user.roadmaps.count() == 0
    assert Assessment.objects.filter(user=returning_user).count() == 1
    assert Roadmap.objects.filter(user=returning_user).count() == 1
    assert UserProgress.objects.filter(user=returning_user).count() == 1
    assert CourseCompletion.objects.filter(user=returning_user).count() == 2
    assert TimeLog.objects.filter(user=returning_user).count() == 4
