"""Draft scenario documents with Gemini for uncovered blueprints.

Validated drafts are appended to `_staging/<role>.jsonl` as review_status=draft.
Never writes to role .py modules or Chroma. Invalid model output is skipped
(with one logged warning), so the staging file only ever holds schema-valid drafts.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.assessments.scenario_corpus.coverage import uncovered_blueprints
from apps.assessments.scenario_corpus.generation import (
    LLM_CONTENT_KEYS,
    assemble_scenario_document,
    build_generation_prompt,
)
from apps.assessments.scenario_corpus.registry import iter_approved_scenarios
from apps.assessments.scenario_corpus.schema import validate_scenario
from apps.assessments.scenario_corpus.staging import append_drafts
from apps.core.gemma_client import GemmaClient


class Command(BaseCommand):
    help = "Generate draft scenarios for uncovered blueprints into JSONL staging."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--role", required=True)
        parser.add_argument("--tier", type=int, default=1, choices=[1, 2])
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        role_key = options["role"]
        todo = uncovered_blueprints(role_key, tier=options["tier"])[: options["limit"]]
        if not todo:
            self.stdout.write(self.style.SUCCESS(f"{role_key}: already covered for tier {options['tier']}."))
            return

        exemplars_by_subskill: dict[str, list[dict]] = {}
        for scn in iter_approved_scenarios():
            exemplars_by_subskill.setdefault(scn["subskill_key"], []).append(scn)

        client = GemmaClient(task_type="json_generation")
        staged: list[dict] = []
        for bp in todo:
            system, prompt = build_generation_prompt(
                bp, exemplars=exemplars_by_subskill.get(bp.subskill_key, [])
            )
            if options["dry_run"]:
                self.stdout.write(f"[dry-run] would generate {bp.subskill_key}/{bp.question_type}")
                continue
            try:
                response = client.generate_structured(
                    prompt=prompt, system=system, required_keys=LLM_CONTENT_KEYS
                )
            except Exception as error:  # noqa: BLE001 - generation must never abort the batch
                self.stderr.write(self.style.WARNING(f"generation failed for {bp.subskill_key}: {error}"))
                continue
            doc = assemble_scenario_document(
                bp, response.payload or {}, slug=f"gen-{uuid.uuid4().hex[:8]}"
            )
            errors = validate_scenario(doc)
            if errors:
                self.stderr.write(self.style.WARNING(
                    f"discarded invalid draft for {bp.subskill_key}: {errors[0]}"
                ))
                continue
            staged.append(doc)

        if staged:
            append_drafts(role_key, staged)
        self.stdout.write(self.style.SUCCESS(
            f"{role_key}: staged {len(staged)} valid draft(s) of {len(todo)} attempted."
        ))
