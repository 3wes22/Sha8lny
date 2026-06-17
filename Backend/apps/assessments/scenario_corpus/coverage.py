"""Blueprint enumeration and tier definitions for the scenario corpus.

A *blueprint* is one (role, subskill, stage, question_type) cell the corpus
should cover. The generator drafts for uncovered blueprints; the audit gates
on whether each tier's blueprints are satisfied. This module is the single
source of truth for "what counts as covered", so generator and audit agree.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.assessments.role_graph_data import ROLE_GRAPHS
from apps.assessments.scenario_corpus.registry import iter_approved_scenarios

# Floors mirror scenario_corpus_audit + AUTHOR_GUIDE.
TIER1_STAGE1_SINGLE_CHOICE_MIN = 2


@dataclass(frozen=True)
class Blueprint:
    role_key: str
    subskill_key: str
    competency: str
    dimension_key: str
    stage: int
    question_type: str


def _subskill_lookup(role_key: str) -> dict[str, object]:
    graph = ROLE_GRAPHS[role_key]
    return {
        subskill.key: subskill
        for dimension in graph.dimensions
        for subskill in dimension.subskills
    }


def stage1_calibration_subskills(role_key: str) -> list[str]:
    """The subskills stage-1 calibration actually targets (the high-leverage set)."""
    targets = StageAllocator.allocate_stage_one(load_role_graph(role_key))
    return [target.key for target in targets]


def tier1_blueprints(role_key: str) -> list[Blueprint]:
    """Full Tier-1 floor: stage-1 single_choice, >=2 per calibration subskill."""
    lookup = _subskill_lookup(role_key)
    blueprints: list[Blueprint] = []
    for subskill_key in stage1_calibration_subskills(role_key):
        subskill = lookup[subskill_key]
        for _ in range(TIER1_STAGE1_SINGLE_CHOICE_MIN):
            blueprints.append(
                Blueprint(
                    role_key=role_key,
                    subskill_key=subskill_key,
                    competency=subskill.label,
                    dimension_key=subskill.dimension,
                    stage=1,
                    question_type="single_choice",
                )
            )
    return blueprints


def _approved_counts() -> dict[tuple[str, int, str, str], int]:
    counts: dict[tuple[str, int, str, str], int] = defaultdict(int)
    for scenario in iter_approved_scenarios():
        counts[
            (
                scenario["role_key"],
                int(scenario["stage"]),
                scenario["question_type"],
                scenario["subskill_key"],
            )
        ] += 1
    return counts


def uncovered_blueprints(role_key: str, *, tier: int) -> list[Blueprint]:
    """Blueprints still below floor, accounting for already-approved scenarios."""
    if tier != 1:
        raise ValueError(f"tier {tier} not yet supported (Phase 4 adds tier 2)")
    counts = _approved_counts()
    needed: dict[tuple[str, str], int] = defaultdict(int)
    todo: list[Blueprint] = []
    for bp in tier1_blueprints(role_key):
        cell = (bp.role_key, bp.stage, bp.question_type, bp.subskill_key)
        have = counts.get(cell, 0) + needed[(bp.subskill_key, bp.question_type)]
        if have < TIER1_STAGE1_SINGLE_CHOICE_MIN:
            todo.append(bp)
            needed[(bp.subskill_key, bp.question_type)] += 1
    return todo
