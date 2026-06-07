"""Export active jobs to JSON for offline ranker training."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.jobs.models import Job
from apps.jobs.services import JobService


class Command(BaseCommand):
    help = "Export jobs with required skills for train_job_ranker.py"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="../ai-models/data/job_ranker_training.json",
            help="Output JSON path (relative to Backend/)",
        )
        parser.add_argument(
            "--real-only",
            action="store_true",
            help="Only export jobs with platform_metadata.source=wuzzuf",
        )

    def handle(self, *args, **options):
        queryset = Job.objects.filter(is_active=True, is_deleted=False).prefetch_related(
            "job_skills__skill"
        )
        if options["real_only"]:
            queryset = queryset.filter(platform_metadata__source="wuzzuf")

        payload = []
        for job in queryset:
            skills = list(
                job.job_skills.filter(is_required=True).values_list("skill__name", flat=True)
            )
            if not skills:
                skills = JobService._keyword_extract_skills(job)
            payload.append(
                {
                    "id": str(job.id),
                    "title": job.title,
                    "description": job.description,
                    "requirements": job.requirements,
                    "experience_level": job.experience_level,
                    "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                    "location_country": job.location_country,
                    "required_skills": skills,
                    "external_url": job.external_url,
                }
            )

        output = Path(options["output"])
        if not output.is_absolute():
            output = Path(__file__).resolve().parents[4] / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Exported {len(payload)} jobs to {output}"))
