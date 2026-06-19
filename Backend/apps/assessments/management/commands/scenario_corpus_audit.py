"""Audit the assessment scenario corpus.

Runs three checks and exits non-zero if any of them fails:
    1. Validation: every approved scenario passes ``validate_scenario``.
    2. Coverage:   the per-role × per-stage × per-question-type floor
                   (see ``research.md`` Decision 12) is met.
    3. Near-duplicate detection: for each
       ``(role_key, subskill_key, question_type)`` cluster, no pair of
       approved scenarios has cosine similarity > 0.92 over their
       embedded retrieval texts.

The near-duplicate check requires ``sentence-transformers`` to be
importable. If it is not, the check is skipped with a warning and the
command continues with validation + coverage. Validation and coverage
results alone are sufficient to drive CI gates for content PRs.

Usage:
    python manage.py scenario_corpus_audit
    python manage.py scenario_corpus_audit --skip-duplicates
    python manage.py scenario_corpus_audit --duplicate-threshold 0.95
"""

from __future__ import annotations

import sys
from collections import defaultdict
from typing import Any

from django.core.management.base import BaseCommand

from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.assessments.role_graph_data import ROLE_GRAPHS
from apps.assessments.scenario_corpus.coverage import tier2_subskills
from apps.assessments.scenario_corpus.registry import (
    SCENARIO_CORPUS_VERSION,
    iter_all_scenarios,
    iter_approved_scenarios,
)
from apps.assessments.scenario_corpus.schema import iter_validation_errors
from apps.assessments.scenario_retriever import ScenarioRetriever
from apps.core.ai_settings import EMBEDDING_MODEL


# Coverage floor per Decision 12 in research.md.
_STAGE1_SINGLE_CHOICE_MIN = 2
_STAGE2_SINGLE_CHOICE_MIN = 2
_STAGE2_MULTI_SELECT_MIN = 1
_STAGE2_OPEN_ENDED_MIN = 1


class Command(BaseCommand):
    help = (
        "Audit the assessment scenario corpus for validation errors, coverage "
        "gaps, and near-duplicate scenarios. Exits non-zero on any failure."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--skip-duplicates",
            action="store_true",
            help="Skip the embedding-based near-duplicate detection.",
        )
        parser.add_argument(
            "--duplicate-threshold",
            type=float,
            default=0.92,
            help="Cosine similarity threshold for near-duplicate detection (default 0.92).",
        )
        parser.add_argument(
            "--tier",
            type=str,
            default="all",
            choices=["1", "2", "all"],
            help="Scope the coverage report to Tier 1 (stage-1 calibration), Tier 2 (stage-2), or all.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        exit_code = 0
        self.stdout.write(
            f"Scenario corpus audit (version={SCENARIO_CORPUS_VERSION})"
        )
        self.stdout.write("=" * 68)

        # --- 1. Validation ---------------------------------------------------
        all_scenarios = list(iter_all_scenarios())
        failures = iter_validation_errors(all_scenarios)
        if failures:
            exit_code = 1
            self.stdout.write(self.style.ERROR(
                f"\nValidation: FAILED ({len(failures)} document(s) invalid)"
            ))
            for doc_id, errors in failures:
                self.stdout.write(f"  {doc_id}:")
                for error in errors:
                    self.stdout.write(f"    * {error}")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\nValidation: OK ({len(all_scenarios)} document(s) checked)"
            ))

        # --- 2. Coverage ----------------------------------------------------
        approved = list(iter_approved_scenarios())
        coverage_ok = self._report_coverage(approved, options["tier"])
        if not coverage_ok:
            exit_code = 1

        # --- 3. Near-duplicate detection ------------------------------------
        if options.get("skip_duplicates"):
            self.stdout.write(self.style.WARNING(
                "\nNear-duplicate detection: SKIPPED (--skip-duplicates)"
            ))
        else:
            duplicates = self._detect_duplicates(
                approved, threshold=options["duplicate_threshold"]
            )
            if duplicates is None:
                self.stdout.write(self.style.WARNING(
                    "\nNear-duplicate detection: SKIPPED "
                    "(sentence-transformers unavailable)"
                ))
            elif duplicates:
                exit_code = 1
                self.stdout.write(self.style.ERROR(
                    f"\nNear-duplicate detection: FAILED "
                    f"({len(duplicates)} pair(s) above threshold "
                    f"{options['duplicate_threshold']})"
                ))
                for left_id, right_id, score in duplicates:
                    self.stdout.write(
                        f"  {left_id}  <==>  {right_id}   cosine={score:.3f}"
                    )
            else:
                self.stdout.write(self.style.SUCCESS(
                    "\nNear-duplicate detection: OK"
                ))

        self.stdout.write("\n" + "=" * 68)
        if exit_code == 0:
            self.stdout.write(self.style.SUCCESS("Audit PASSED."))
        else:
            self.stdout.write(self.style.ERROR("Audit FAILED."))
        sys.exit(exit_code)

    # ------------------------------------------------------------------
    # Coverage report
    # ------------------------------------------------------------------

    def _report_coverage(self, approved: list[dict[str, Any]], tier: str) -> bool:
        self.stdout.write("\nCoverage report")
        self.stdout.write("-" * 68)
        all_ok = True

        # Bucket approved scenarios by (role_key, stage, question_type, subskill_key).
        buckets: dict[tuple[str, int, str, str], int] = defaultdict(int)
        for scenario in approved:
            key = (
                scenario["role_key"],
                int(scenario["stage"]),
                scenario["question_type"],
                scenario["subskill_key"],
            )
            buckets[key] += 1

        for role_key, graph in ROLE_GRAPHS.items():
            self.stdout.write(f"\n  {role_key}")
            role_subskills = [
                subskill.key
                for dimension in graph.dimensions
                for subskill in dimension.subskills
            ]
            try:
                stage1_targets = {
                    target.key
                    for target in StageAllocator.allocate_stage_one(
                        load_role_graph(role_key)
                    )
                }
            except Exception as error:
                self.stdout.write(self.style.WARNING(
                    f"    could not compute stage-1 allocation: {error}"
                ))
                stage1_targets = set(role_subskills)

            stage2_subskills = role_subskills
            if tier == "2":
                stage2_subskills = tier2_subskills(role_key)

            all_checks: list[tuple[str, int, list[str], int]] = [
                ("stage 1 single_choice", 1, sorted(stage1_targets), _STAGE1_SINGLE_CHOICE_MIN),
                ("stage 2 single_choice", 2, stage2_subskills, _STAGE2_SINGLE_CHOICE_MIN),
                ("stage 2 multi_select", 2, stage2_subskills, _STAGE2_MULTI_SELECT_MIN),
                ("stage 2 open_ended", 2, stage2_subskills, _STAGE2_OPEN_ENDED_MIN),
            ]
            if tier == "1":
                checks = [c for c in all_checks if c[1] == 1]
            elif tier == "2":
                checks = [c for c in all_checks if c[1] == 2]
            else:
                checks = all_checks
            for label, stage, expected_subskills, floor in checks:
                question_type = label.rsplit(" ", 1)[1]
                gaps: list[str] = []
                for subskill_key in expected_subskills:
                    count = buckets.get(
                        (role_key, stage, question_type, subskill_key), 0
                    )
                    if count < floor:
                        gaps.append(f"{subskill_key} (have {count}, need {floor})")
                total = sum(
                    count
                    for (r, s, q, _), count in buckets.items()
                    if r == role_key and s == stage and q == question_type
                )
                if gaps:
                    all_ok = False
                    self.stdout.write(self.style.WARNING(
                        f"    {label:25s} : {total} doc(s) total, "
                        f"BELOW FLOOR for {len(gaps)} subskill(s)"
                    ))
                    for gap in gaps:
                        self.stdout.write(f"        - {gap}")
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"    {label:25s} : {total} doc(s) total, OK"
                    ))
        return all_ok

    # ------------------------------------------------------------------
    # Near-duplicate detection
    # ------------------------------------------------------------------

    def _detect_duplicates(
        self,
        approved: list[dict[str, Any]],
        *,
        threshold: float,
    ) -> list[tuple[str, str, float]] | None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None

        try:
            embedder = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as error:
            self.stdout.write(self.style.WARNING(
                f"\nNear-duplicate detection: SKIPPED (embedder load failed: {error})"
            ))
            return None

        clusters: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for scenario in approved:
            clusters[
                (
                    scenario["role_key"],
                    scenario["subskill_key"],
                    scenario["question_type"],
                )
            ].append(scenario)

        pairs: list[tuple[str, str, float]] = []
        for cluster_key, scenarios in clusters.items():
            if len(scenarios) < 2:
                continue
            texts = [
                ScenarioRetriever.build_embedding_text(
                    competency=s.get("competency", ""),
                    question_type=s.get("question_type", ""),
                    stage=int(s.get("stage", 0)),
                    scenario_context=s.get("scenario_context", ""),
                    stem=s.get("stem", ""),
                )
                for s in scenarios
            ]
            try:
                embeddings = embedder.encode(texts, normalize_embeddings=True)
            except Exception as error:
                self.stdout.write(self.style.WARNING(
                    f"  could not embed cluster {cluster_key}: {error}"
                ))
                continue
            for i in range(len(scenarios)):
                for j in range(i + 1, len(scenarios)):
                    vec_i = embeddings[i]
                    vec_j = embeddings[j]
                    score = float(sum(a * b for a, b in zip(vec_i, vec_j)))
                    if score > threshold:
                        pairs.append(
                            (
                                str(scenarios[i].get("doc_id") or "<?>"),
                                str(scenarios[j].get("doc_id") or "<?>"),
                                score,
                            )
                        )
        return pairs
