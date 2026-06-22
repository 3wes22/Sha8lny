"""API tests for course listing and recommendation endpoints."""

from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from apps.courses.models import Course, CoursePlatform


@pytest.fixture
def course_platform(db):
    return CoursePlatform.objects.create(
        name="Courses API Platform",
        slug="courses-api-platform",
        website_url="https://example.com",
        integration_type=CoursePlatform.MANUAL,
    )


@pytest.fixture
def published_courses(course_platform):
    return [
        Course.objects.create(
            platform=course_platform,
            external_id=f"course-{index}",
            title=f"Course {index}",
            slug=f"course-{index}",
            description=f"Description {index}",
            url=f"https://example.com/course-{index}",
            is_published=True,
            rating=Decimal("4.00") + Decimal(index) / 10,
            total_enrollments=100 * index,
        )
        for index in range(1, 4)
    ]


@pytest.mark.django_db
def test_recommended_returns_published_courses(
    authenticated_client,
    published_courses,
):
    response = authenticated_client.get(reverse("courses:course-recommended"))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 3
    assert response.data[0]["id"] == str(published_courses[2].id)
    assert response.data[0]["title"] == published_courses[2].title
