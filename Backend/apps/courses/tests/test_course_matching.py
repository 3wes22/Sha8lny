"""Tests for course embedding index and roadmap matching."""

from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.courses.course_index import CourseIndex, build_course_embedding_text
from apps.courses.models import Course, CoursePlatform
from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
from apps.roadmaps.services import RoadmapService
from apps.users.models import Skill


@pytest.mark.django_db
def test_build_course_embedding_text_includes_skills(user):
    platform = CoursePlatform.objects.create(
        name="Demo Platform",
        slug="demo-platform",
        website_url="https://example.com",
        integration_type=CoursePlatform.MANUAL,
    )
    course = Course.objects.create(
        platform=platform,
        external_id="c1",
        title="Python Backend",
        slug="python-backend",
        description="Learn Python APIs",
        url="https://example.com/c1",
        is_published=True,
    )
    skill = Skill.objects.create(name="Python", slug="python", category="technical")
    course.course_skills.create(skill=skill, is_primary=True)

    text = build_course_embedding_text(course)
    assert "Python Backend" in text
    assert "Python" in text


@pytest.mark.django_db
def test_match_courses_for_milestone_links_course(user):
    platform = CoursePlatform.objects.create(
        name="Demo Platform",
        slug="demo-platform-2",
        website_url="https://example.com",
        integration_type=CoursePlatform.MANUAL,
    )
    course = Course.objects.create(
        platform=platform,
        external_id="c2",
        title="SQL for Backend Developers",
        slug="sql-backend",
        description="Indexing and joins",
        url="https://example.com/c2",
        is_published=True,
    )

    roadmap = Roadmap.objects.create(
        user=user,
        title="Backend roadmap",
        target_career="Backend Developer",
        current_level="beginner",
        target_level="job-ready",
        estimated_duration_weeks=12,
        status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap,
        title="Phase 1",
        description="Fundamentals",
        order=1,
        estimated_duration_weeks=4,
    )
    milestone = RoadmapMilestone.objects.create(
        phase=phase,
        title="Strengthen SQL foundations",
        description="Practice queries",
        milestone_type=RoadmapMilestone.COURSE,
        order=1,
        estimated_duration_hours=Decimal("10.00"),
        skills=["SQL"],
    )

    with patch.object(
        CourseIndex,
        "search",
        return_value=[{"course_id": str(course.id), "title": course.title, "score": 0.91}],
    ):
        RoadmapService.match_courses_for_milestone(milestone, roadmap)

    assert milestone.courses.count() == 1
    link = milestone.courses.first()
    assert link.match_score == Decimal("91.00")
