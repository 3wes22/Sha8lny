import pytest
from decimal import Decimal
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.jobs.models import Job, JobPlatform, JobSkill, SavedJob
from apps.users.models import Skill, User, UserSkill


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def jobs_user(db):
    user = User.objects.create_user(
        auth0_id="jobs_contract_auth0",
        email="jobs-contract@example.com",
        username="jobs_contract_user",
        full_name="Jobs Contract User",
        date_of_birth="1998-01-01",
    )
    skill = Skill.objects.create(name="React", slug="react", category="technical")
    UserSkill.objects.create(user=user, skill=skill, proficiency_level=4)
    return user


@pytest.fixture
def contract_job(db, jobs_user):
    platform = JobPlatform.objects.create(
        name="Contract Platform",
        slug="contract-platform",
        website_url="https://jobs.example.com",
        is_active=True,
        scraping_enabled=True,
        target_countries=["Egypt"],
    )
    skill = Skill.objects.get(slug="react")
    job = Job.objects.create(
        platform=platform,
        external_id="react-role-1",
        external_url="https://jobs.example.com/react-role-1",
        title="React Engineer",
        company_name="Atlas Labs",
        description="Build interfaces",
        requirements="React, TypeScript",
        location_city="Cairo",
        location_country="Egypt",
        is_remote=True,
        remote_type="fully_remote",
        job_type="full_time",
        experience_level="mid",
        salary_min=Decimal("12000.00"),
        salary_max=Decimal("18000.00"),
        salary_currency="EGP",
        salary_period="monthly",
        salary_disclosed=True,
        posted_date=timezone.now().date(),
        is_active=True,
    )
    JobSkill.objects.create(job=job, skill=skill, is_required=True)
    return job


@pytest.mark.django_db
def test_job_search_exposes_save_and_match_state(api_client, jobs_user, contract_job):
    api_client.force_authenticate(user=jobs_user)
    SavedJob.objects.create(user=jobs_user, job=contract_job)

    response = api_client.get(reverse("jobs:job-search"))

    assert response.status_code == status.HTTP_200_OK
    first_job = response.data["results"][0]
    assert first_job["is_saved"] is True
    assert first_job["external_action_available"] is True
    assert first_job["skill_match_summary"]


@pytest.mark.django_db
def test_job_detail_exposes_save_and_match_state(api_client, jobs_user, contract_job):
    api_client.force_authenticate(user=jobs_user)

    response = api_client.get(reverse("jobs:job-detail", args=[contract_job.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["external_action_available"] is True
    assert "skill_match_summary" in response.data
