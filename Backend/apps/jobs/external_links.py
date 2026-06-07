"""Resolve external apply/search URLs for job listings."""

from __future__ import annotations

from urllib.parse import quote_plus

from apps.jobs.models import Job

WUZZUF_SEARCH = "https://wuzzuf.net/search/jobs/"


def is_listing_verified(job: Job) -> bool:
    meta = job.platform_metadata or {}
    if meta.get("listing_verified") is True:
        return True
    if meta.get("listing_verified") is False:
        return False
    # HTML fixtures with real /jobs/ paths are treated as verified
    ingest_method = str(meta.get("ingest_method") or "")
    if ingest_method.startswith("html_fixture"):
        return True
    # Curated CSV snapshot — no guaranteed live listing page
    if ingest_method.startswith("csv") or meta.get("ingest_method") == "csv":
        return False
    external_id = str(job.external_id or "")
    if external_id.startswith("eg-tech-"):
        return False
    return bool(job.external_url and "wuzzuf.net" in job.external_url)


def resolve_external_apply_url(job: Job) -> str | None:
    if not job.external_url:
        return None
    if is_listing_verified(job):
        return job.external_url
    query = quote_plus(f"{job.title} {job.company_name}".strip())
    return f"{WUZZUF_SEARCH}?q={query}"


def external_apply_label(job: Job) -> str:
    return "Apply on Wuzzuf" if is_listing_verified(job) else "Search similar roles on Wuzzuf"
