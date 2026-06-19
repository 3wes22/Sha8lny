"""Persist normalized ingest payloads into Django Job + JobSkill rows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone

from apps.jobs.models import Job, JobPlatform
from apps.jobs.services import JobService


def get_or_create_wuzzuf_platform() -> JobPlatform:
    platform, _ = JobPlatform.objects.get_or_create(
        slug="wuzzuf",
        defaults={
            "name": "Wuzzuf",
            "website_url": "https://wuzzuf.net",
            "target_countries": ["Egypt"],
            "requires_scraping": True,
            "scraping_enabled": True,
            "is_active": True,
        },
    )
    return platform


def persist_ingested_job(platform: JobPlatform, payload: dict[str, Any]) -> tuple[Any, bool]:
    """
    Create or update a job from an ingest payload.

    Returns (job, created).
    """
    source = str(payload.get("source") or "wuzzuf")
    scraped_at = timezone.now()
    ingest_method = payload.get("ingest_method", "batch")
    listing_verified = ingest_method.startswith("html_fixture")
    platform_metadata = {
        "source": source,
        "ingest_method": ingest_method,
        "listing_verified": listing_verified,
        "scraped_at": scraped_at.isoformat(),
        "source_url": payload.get("external_url", ""),
    }

    existing = Job.objects.filter(
        platform=platform,
        external_id=payload["external_id"],
        is_deleted=False,
    ).first()
    created = existing is None

    job = JobService.create_job(
        platform=platform,
        external_id=payload["external_id"],
        title=payload["title"],
        company_name=payload["company_name"],
        location_city=payload.get("location_city", ""),
        location_country=payload.get("location_country", "Egypt"),
        external_url=payload["external_url"],
        posted_date=payload.get("posted_date") or timezone.now().date(),
        experience_level=payload.get("experience_level") or "mid",
        job_type=payload.get("job_type") or "full_time",
        is_remote=bool(payload.get("is_remote")),
        description=payload.get("description", ""),
        requirements=payload.get("requirements", ""),
        platform_metadata=platform_metadata,
        last_fetched_at=scraped_at,
    )

    skills = payload.get("skills") or []
    if skills:
        JobService.add_skills_to_job(job, skills, is_required=True)

    return job, created
