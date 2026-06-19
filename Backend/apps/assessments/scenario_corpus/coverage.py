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
from apps.assessments.role_graph import SubSkill, load_role_graph
from apps.assessments.scenario_corpus.registry import iter_approved_scenarios

# Floors mirror scenario_corpus_audit + AUTHOR_GUIDE.
TIER1_STAGE1_SINGLE_CHOICE_MIN = 2

# Tier-2 floors (stage-2, demand-weighted).
TIER2_STAGE2_SINGLE_CHOICE_MIN = 2
TIER2_STAGE2_MULTI_SELECT_MIN = 1
TIER2_STAGE2_OPEN_ENDED_MIN = 1

_TIER2_FLOORS: tuple[tuple[str, int], ...] = (
    ("single_choice", TIER2_STAGE2_SINGLE_CHOICE_MIN),
    ("multi_select", TIER2_STAGE2_MULTI_SELECT_MIN),
    ("open_ended", TIER2_STAGE2_OPEN_ENDED_MIN),
)
_TIER2_FLOOR_MAP: dict[str, int] = dict(_TIER2_FLOORS)


@dataclass(frozen=True)
class Blueprint:
    role_key: str
    subskill_key: str
    competency: str
    dimension_key: str
    stage: int
    question_type: str


def _subskill_lookup(role_key: str) -> dict[str, SubSkill]:
    graph = load_role_graph(role_key)
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


def tier2_subskills(role_key: str, *, per_dimension: int = 2) -> list[str]:
    """Stage-2 demand set: the calibration subskills plus the top
    target-proficiency subskills per dimension. Demand-weighted (not all
    subskills) so the Tier-2 audit floor is achievable."""
    graph = load_role_graph(role_key)
    demand: list[str] = list(stage1_calibration_subskills(role_key))
    for dimension in graph.dimensions:
        # Ties in target_proficiency are broken by definition order (stable sort).
        ranked = sorted(
            dimension.subskills,
            key=lambda s: s.target_proficiency,
            reverse=True,
        )
        for subskill in ranked[:per_dimension]:
            if subskill.key not in demand:
                demand.append(subskill.key)
    return demand


def tier2_blueprints(role_key: str) -> list[Blueprint]:
    """Stage-2 blueprints over the demand set: per demand subskill,
    single_choice x2 + multi_select x1 + open_ended x1."""
    lookup = _subskill_lookup(role_key)
    blueprints: list[Blueprint] = []
    for subskill_key in tier2_subskills(role_key):
        subskill = lookup[subskill_key]
        for question_type, floor in _TIER2_FLOORS:
            for _ in range(floor):
                blueprints.append(
                    Blueprint(
                        role_key=role_key,
                        subskill_key=subskill_key,
                        competency=subskill.label,
                        dimension_key=subskill.dimension,
                        stage=2,
                        question_type=question_type,
                    )
                )
    return blueprints


def _floor_for(stage: int, question_type: str) -> int:
    # Stage 1 only contains single_choice in this system.
    if stage == 1:
        return TIER1_STAGE1_SINGLE_CHOICE_MIN
    try:
        return _TIER2_FLOOR_MAP[question_type]
    except KeyError:
        raise ValueError(
            f"no Tier-2 floor defined for stage-2 question_type={question_type!r}"
        )


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
    if tier == 1:
        blueprints = tier1_blueprints(role_key)
    elif tier == 2:
        blueprints = tier2_blueprints(role_key)
    else:
        raise ValueError(f"unsupported tier {tier} (expected 1 or 2)")
    counts = _approved_counts()
    needed: dict[tuple[str, str], int] = defaultdict(int)
    todo: list[Blueprint] = []
    for bp in blueprints:
        cell = (bp.role_key, bp.stage, bp.question_type, bp.subskill_key)
        floor = _floor_for(bp.stage, bp.question_type)
        have = counts.get(cell, 0) + needed[(bp.subskill_key, bp.question_type)]
        if have < floor:
            todo.append(bp)
            needed[(bp.subskill_key, bp.question_type)] += 1
    return todo
