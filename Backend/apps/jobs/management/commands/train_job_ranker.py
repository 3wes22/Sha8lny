"""Train and save the LightGBM job ranker from DB-exported jobs."""

import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export jobs from DB and train ai-models job ranker"

    def add_arguments(self, parser):
        parser.add_argument(
            "--real-only",
            action="store_true",
            help="Train only on wuzzuf-sourced jobs",
        )

    def handle(self, *args, **options):
        backend_root = Path(__file__).resolve().parents[4]
        ai_models_root = backend_root.parent / "ai-models"
        training_json = ai_models_root / "data" / "job_ranker_training.json"
        train_script = ai_models_root / "scripts" / "train_job_ranker.py"

        export_args = ["python", "manage.py", "export_jobs_for_ranker", "--output", str(training_json)]
        if options["real_only"]:
            export_args.append("--real-only")

        subprocess.run(export_args, cwd=backend_root, check=True)

        python_bin = sys.executable
        subprocess.run(
            [python_bin, str(train_script), "--input", str(training_json)],
            cwd=ai_models_root,
            check=True,
        )
        self.stdout.write(self.style.SUCCESS("Job ranker trained and saved to ai-models/models/custom/"))
