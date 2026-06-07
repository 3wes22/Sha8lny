"""
Ingest jobs from saved Wuzzuf HTML fixtures (offline batch, not live scraping).

Usage:
    python manage.py ingest_jobs_wuzzuf
    python manage.py ingest_jobs_wuzzuf --fixtures-dir apps/jobs/ingest/test_fixtures
"""

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.jobs.ingest.persist import get_or_create_wuzzuf_platform, persist_ingested_job
from apps.jobs.ingest.wuzzuf import parse_wuzzuf_page


class Command(BaseCommand):
    help = "Parse saved Wuzzuf HTML fixtures into job rows"

    def add_arguments(self, parser):
        default_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "ingest"
            / "test_fixtures"
        )
        parser.add_argument(
            "--fixtures-dir",
            type=str,
            default=str(default_dir),
            help="Directory containing *.html fixture files",
        )
        parser.add_argument(
            "--career-hint",
            type=str,
            default="",
            help="Optional career hint for skill extraction (backend, frontend, data)",
        )

    def handle(self, *args, **options):
        fixtures_dir = Path(options["fixtures_dir"])
        if not fixtures_dir.exists():
            self.stdout.write(self.style.ERROR(f"Fixtures directory not found: {fixtures_dir}"))
            return

        html_files = sorted(fixtures_dir.glob("*.html"))
        if not html_files:
            self.stdout.write(self.style.WARNING(f"No HTML files in {fixtures_dir}"))
            return

        platform = get_or_create_wuzzuf_platform()
        created_count = 0
        updated_count = 0
        total_parsed = 0

        for path in html_files:
            html = path.read_text(encoding="utf-8", errors="replace")
            rows = parse_wuzzuf_page(html, career_hint=options["career_hint"])
            total_parsed += len(rows)
            for row in rows:
                row["ingest_method"] = f"html_fixture:{path.name}"
                _, created = persist_ingested_job(platform, row)
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Parsed {total_parsed} jobs from {len(html_files)} fixtures "
                f"({created_count} created, {updated_count} updated)"
            )
        )
