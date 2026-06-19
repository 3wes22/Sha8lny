"""Tests for job skill extraction helpers."""

from unittest.mock import patch

import pytest

from apps.jobs.models import Job, JobPlatform
from apps.jobs.services import JobService
from apps.users.models import Skill


@pytest.mark.django_db
def test_keyword_extract_skills_finds_known_terms():
    platform = JobPlatform.objects.create(
        name="Wuzzuf",
        slug="wuzzuf-test",
        website_url="https://wuzzuf.net",
    )
    Skill.objects.create(name="Python", slug="python", category="technical")
    Skill.objects.create(name="SQL", slug="sql", category="technical")

    job = Job.objects.create(
        platform=platform,
        external_id="job-1",
        title="Backend Engineer",
        company_name="Demo Co",
        description="Build APIs with Python and SQL.",
        requirements="Python, REST APIs",
    )

    extracted = JobService._keyword_extract_skills(job)
    assert "Python" in extracted
    assert "SQL" in extracted


@pytest.mark.django_db
def test_extract_skills_from_job_falls_back_to_keywords():
    platform = JobPlatform.objects.create(
        name="Bayt",
        slug="bayt-test",
        website_url="https://bayt.com",
    )
    Skill.objects.create(name="React", slug="react", category="technical")
    job = Job.objects.create(
        platform=platform,
        external_id="job-2",
        title="Frontend Engineer",
        company_name="Demo Co",
        description="React component development.",
    )

    with patch("apps.core.gemma_client.GemmaClient") as mock_client:
        mock_client.return_value.generate_structured.side_effect = RuntimeError("offline")
        skills = JobService.extract_skills_from_job(job)

    assert "React" in skills
    assert job.job_skills.filter(skill__name="React").exists()
