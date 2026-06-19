"""Deterministic retrieval eval for the scenario corpus.

For every Tier-1 blueprint, ask the retriever for a scenario and measure:
  - coverage: fraction of blueprints that returned >=1 scenario
  - subskill_precision: fraction of returned scenarios whose subskill_key
    exactly matches the requested one (i.e. not the broad-where fallback)
No Gemini calls; safe to gate in CI once the index is built.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.assessments.scenario_corpus.coverage import tier1_blueprints
from apps.assessments.scenario_retriever import ScenarioRetriever


@dataclass(frozen=True)
class RetrievalEvalResult:
    role_key: str
    blueprint_count: int
    coverage: float
    subskill_precision: float


def evaluate_role(role_key: str) -> RetrievalEvalResult:
    # tier1_blueprints emits TIER1_STAGE1_SINGLE_CHOICE_MIN copies per
    # (subskill, stage, question_type) cell; measure once per unique cell.
    seen: set[tuple[str, int, str]] = set()
    returned = 0
    subskill_hits = 0
    for bp in tier1_blueprints(role_key):
        cell = (bp.subskill_key, bp.stage, bp.question_type)
        if cell in seen:
            continue
        seen.add(cell)
        docs = ScenarioRetriever.retrieve_for_blueprint(
            role_key=role_key,
            blueprint={
                "question_type": bp.question_type,
                "subskill_key": bp.subskill_key,
                "competency": bp.competency,
                # Eval uses the competency label here; the production path passes
                # a richer scenario-context string, so these numbers are a lower
                # bound on real-world retrieval fidelity.
                "focus": bp.competency,
            },
            stage=bp.stage,
        )
        if docs:
            returned += 1
            if any(d.get("subskill_key") == bp.subskill_key for d in docs):
                subskill_hits += 1
    n = len(seen) or 1  # guard: no Tier-1 cells -> avoid ZeroDivisionError
    return RetrievalEvalResult(
        role_key=role_key,
        blueprint_count=len(seen),
        coverage=returned / n,
        subskill_precision=(subskill_hits / returned) if returned else 0.0,
    )


def evaluate_all(role_keys: list[str]) -> list[RetrievalEvalResult]:
    return [evaluate_role(role) for role in role_keys]
