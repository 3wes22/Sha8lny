"""Unit tests for the deterministic course matcher."""
from decimal import Decimal

import pytest

from apps.courses.matching import CourseCatalog, match_courses, target_level_for_order
from apps.courses.models import Course, CoursePlatform


@pytest.fixture(autouse=True)
def _reset_catalog_cache():
    CourseCatalog.reset()
    yield
    CourseCatalog.reset()


def _platform():
    return CoursePlatform.objects.create(
        name="Coursera", slug="coursera", website_url="https://www.coursera.org",
        integration_type=CoursePlatform.SCRAPING,
    )


def _course(platform, ext, title, *, roles, skills, level="intermediate", rating="4.5", enroll=1000):
    return Course.objects.create(
        platform=platform, external_id=ext, title=title, slug=ext,
        description="x", url=f"https://www.coursera.org/learn/{ext}", level=level,
        rating=Decimal(rating), total_enrollments=enroll, is_published=True,
        metadata={"skills": skills, "roles": roles},
    )


def test_target_level_for_order_maps_bands():
    assert target_level_for_order(1) == "beginner"
    assert target_level_for_order(2) == "beginner"
    assert target_level_for_order(3) == "intermediate"
    assert target_level_for_order(4) == "advanced"
    assert target_level_for_order(5) == "advanced"


@pytest.mark.django_db
def test_empty_catalog_returns_no_matches():
    assert match_courses(
        target_career="Backend Developer", role_key="backend",
        milestone_title="SQL", milestone_skills=["SQL"], target_level="beginner",
    ) == []


@pytest.mark.django_db
def test_off_topic_course_is_excluded():
    platform = _platform()
    _course(platform, "yoga", "Yoga for Beginners", roles=["ui_ux_designer"], skills=["Breathing"])
    matches = match_courses(
        target_career="Backend Developer", role_key="backend",
        milestone_title="Relational databases and SQL", milestone_skills=["SQL"],
        target_level="beginner",
    )
    assert matches == []  # no skill/title overlap and not tagged backend


@pytest.mark.django_db
def test_skill_overlap_outranks_role_only_match():
    platform = _platform()
    # Role-only: tagged backend but no token overlap with the Docker milestone.
    _course(platform, "capstone", "Backend Web Capstone Project", roles=["backend"], skills=["Flask"])
    # Skill-overlap: a real Docker course (even tagged devops, not backend).
    docker = _course(platform, "docker", "Docker and Kubernetes", roles=["devops"], skills=["Docker", "Containers"])

    matches = match_courses(
        target_career="Backend Developer", role_key="backend",
        milestone_title="Containerization with Docker", milestone_skills=["Docker"],
        target_level="advanced", top_k=1,
    )
    assert matches and matches[0]["course_id"] == str(docker.id)


@pytest.mark.django_db
def test_returns_at_most_top_k_sorted_by_score():
    platform = _platform()
    for i in range(4):
        _course(platform, f"sql-{i}", f"SQL Course {i}", roles=["backend"], skills=["SQL", "Databases"])
    matches = match_courses(
        target_career="Backend Developer", role_key="backend",
        milestone_title="Relational databases and SQL", milestone_skills=["SQL"],
        target_level="beginner", top_k=2,
    )
    assert len(matches) == 2
    assert matches[0]["score"] >= matches[1]["score"]
    assert all(0.0 <= m["score"] <= 1.0 for m in matches)
