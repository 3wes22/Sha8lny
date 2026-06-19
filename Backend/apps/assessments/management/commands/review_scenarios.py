"""Review staged drafts: validate, near-duplicate-check, then (on accept)
promote into the per-role module and remove from staging.

Interactive by default; `--yes` accepts every schema-valid, non-duplicate draft
(used by tests and bulk runs). The near-duplicate check reuses the audit's
embedding text + cosine logic; if sentence-transformers is unavailable it is
skipped with a warning.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.assessments.scenario_corpus.registry import iter_approved_scenarios
from apps.assessments.scenario_corpus.schema import validate_scenario
from apps.assessments.scenario_corpus.staging import (
    promote_to_module,
    read_drafts,
    write_drafts,
)
from apps.assessments.scenario_retriever import ScenarioRetriever


class Command(BaseCommand):
    help = "Review staged scenario drafts and promote accepted ones into the role module."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--role", required=True)
        parser.add_argument("--yes", action="store_true", help="Accept all valid, non-duplicate drafts.")
        parser.add_argument("--duplicate-threshold", type=float, default=0.92)

    def handle(self, *args: Any, **options: Any) -> None:
        role_key = options["role"]
        drafts = read_drafts(role_key)
        if not drafts:
            self.stdout.write(f"{role_key}: no staged drafts.")
            return

        embedder = self._load_embedder()
        approved_texts = [self._text(s) for s in iter_approved_scenarios()]

        accepted: list[dict] = []
        remaining: list[dict] = []
        for draft in drafts:
            errors = validate_scenario(draft)
            if errors:
                self.stderr.write(self.style.WARNING(f"invalid draft {draft.get('doc_id')}: {errors[0]}"))
                remaining.append(draft)
                continue
            if embedder is not None and self._is_duplicate(
                embedder, self._text(draft),
                approved_texts + [self._text(a) for a in accepted],
                options["duplicate_threshold"],
            ):
                self.stderr.write(self.style.WARNING(f"near-duplicate held back: {draft.get('doc_id')}"))
                remaining.append(draft)
                continue
            if options["yes"] or self._prompt_accept(draft):
                draft["review_status"] = "approved"
                accepted.append(draft)
            else:
                remaining.append(draft)

        if accepted:
            promote_to_module(role_key, accepted)
        write_drafts(role_key, remaining)
        self.stdout.write(self.style.SUCCESS(
            f"{role_key}: promoted {len(accepted)}, {len(remaining)} left in staging."
        ))

    @staticmethod
    def _text(scn: dict) -> str:
        return ScenarioRetriever.build_embedding_text(
            competency=scn.get("competency", ""),
            question_type=scn.get("question_type", ""),
            stage=int(scn.get("stage", 0)),
            scenario_context=scn.get("scenario_context", ""),
            stem=scn.get("stem", ""),
        )

    def _load_embedder(self):
        try:
            from sentence_transformers import SentenceTransformer

            from apps.core.ai_settings import EMBEDDING_MODEL

            return SentenceTransformer(EMBEDDING_MODEL)
        except Exception:  # noqa: BLE001 - dedup is best-effort
            self.stderr.write(self.style.WARNING("near-duplicate check skipped (sentence-transformers unavailable)"))
            return None

    @staticmethod
    def _is_duplicate(embedder, text: str, others: list[str], threshold: float) -> bool:
        if not others:
            return False
        vectors = embedder.encode([text, *others], normalize_embeddings=True)
        query = vectors[0]
        for other in vectors[1:]:
            score = float(sum(a * b for a, b in zip(query, other)))
            if score > threshold:
                return True
        return False

    def _prompt_accept(self, draft: dict) -> bool:
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"{draft['doc_id']}")
        self.stdout.write(f"scenario: {draft['scenario_context']}")
        self.stdout.write(f"stem:     {draft['stem']}")
        for opt in draft.get("options", []):
            self.stdout.write(f"  ({opt['id']}) {opt['label']}")
        answer = input("accept? [y/N] ").strip().lower()
        return answer == "y"
