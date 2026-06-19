"""Tests for job ingest (CSV + Wuzzuf HTML fixtures)."""

from pathlib import Path

import pytest

from apps.jobs.ingest.csv_loader import parse_jobs_csv
from apps.jobs.ingest.wuzzuf import parse_wuzzuf_page
from apps.jobs.models import Job


@pytest.mark.django_db
class TestJobIngest:
    def test_parse_jobs_csv_fixture(self):
        csv_path = (
            Path(__file__).resolve().parent.parent
            / "ingest"
            / "fixtures"
            / "jobs_egypt_tech.csv"
        )
        rows = parse_jobs_csv(csv_path)
        assert len(rows) >= 50
        assert all(row["external_url"].startswith("https://wuzzuf.net/") for row in rows)
        assert all(row["skills"] for row in rows)

    def test_ingest_jobs_csv_command(self):
        from django.core.management import call_command

        call_command("ingest_jobs_csv", "--clear-fabricated")
        count = Job.objects.filter(platform_metadata__source="wuzzuf").count()
        assert count >= 50

    def test_parse_wuzzuf_html_fixture(self):
        fixture = (
            Path(__file__).resolve().parent.parent
            / "ingest"
            / "test_fixtures"
            / "wuzzuf_sample.html"
        )
        html = fixture.read_text(encoding="utf-8")
        jobs = parse_wuzzuf_page(html, career_hint="backend")
        assert len(jobs) >= 2
        assert jobs[0]["external_url"].startswith("https://wuzzuf.net/")
