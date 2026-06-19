"""
Ingest curated Egyptian tech jobs from CSV (Wuzzuf-style URLs).

Usage:
    python manage.py ingest_jobs_csv
    python manage.py ingest_jobs_csv --file path/to/jobs.csv --clear-fabricated
"""

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.jobs.ingest.csv_loader import parse_jobs_csv
from apps.jobs.ingest.persist import get_or_create_wuzzuf_platform, persist_ingested_job
from apps.jobs.models import Job


class Command(BaseCommand):
    help = "Ingest real Egyptian job listings from a curated CSV export"

    def add_arguments(self, parser):
        default_csv = (
            Path(__file__).resolve().parent.parent.parent
            / "ingest"
            / "fixtures"
            / "jobs_egypt_tech.csv"
        )
        parser.add_argument(
            "--file",
            type=str,
            default=str(default_csv),
            help="Path to CSV file",
        )
        parser.add_argument(
            "--clear-fabricated",
            action="store_true",
            help="Delete jobs marked platform_metadata.source=fabricated before ingest",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file"])
        if options["clear_fabricated"]:
            deleted, _ = Job.objects.filter(
                Q(platform_metadata__source="fabricated")
            ).delete()
            self.stdout.write(self.style.WARNING(f"Removed {deleted} fabricated jobs"))

        rows = parse_jobs_csv(csv_path, source="wuzzuf")
        platform = get_or_create_wuzzuf_platform()

        created_count = 0
        updated_count = 0
        for row in rows:
            row["ingest_method"] = "csv"
            _, created = persist_ingested_job(platform, row)
            if created:
                created_count += 1
            else:
                updated_count += 1

        real_count = Job.objects.filter(
            platform_metadata__source="wuzzuf",
            is_deleted=False,
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingested {len(rows)} rows ({created_count} created, {updated_count} updated). "
                f"Total wuzzuf-sourced jobs: {real_count}"
            )
        )
