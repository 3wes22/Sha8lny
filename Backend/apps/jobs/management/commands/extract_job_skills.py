"""Extract skills for seeded jobs using Gemini with keyword fallback."""

from django.core.management.base import BaseCommand

from apps.jobs.models import Job
from apps.jobs.services import JobService


class Command(BaseCommand):
    help = "Extract and persist skills for active jobs."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of jobs to process.",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing job skills before extraction.",
        )

    def handle(self, *args, **options) -> None:
        jobs = Job.objects.filter(is_deleted=False, is_active=True).order_by("-posted_date")[
            : options["limit"]
        ]
        processed = 0
        for job in jobs:
            skills = JobService.extract_skills_from_job(
                job,
                replace_existing=options["replace"],
            )
            processed += 1
            self.stdout.write(f"{job.title}: {len(skills)} skills")

        self.stdout.write(self.style.SUCCESS(f"Processed {processed} jobs."))
