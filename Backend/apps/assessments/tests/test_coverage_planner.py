from __future__ import annotations

import pytest

from apps.assessments.scenario_corpus.coverage import (
    Blueprint,
    stage1_calibration_subskills,
    tier1_blueprints,
    uncovered_blueprints,
    tier2_subskills,
)


@pytest.mark.django_db
def test_stage1_calibration_returns_five_backend_subskills():
    subs = stage1_calibration_subskills("backend")
    assert len(subs) == 5
    assert all(isinstance(s, str) for s in subs)


def test_tier1_blueprints_are_stage1_single_choice():
    bps = tier1_blueprints("backend")
    assert bps, "tier-1 blueprint set must be non-empty"
    assert all(bp.stage == 1 and bp.question_type == "single_choice" for bp in bps)
    # Two blueprints per calibration subskill (floor is >= 2).
    assert len(bps) == 2 * len(stage1_calibration_subskills("backend"))
    bp = bps[0]
    assert bp.role_key == "backend"
    assert bp.competency and bp.dimension_key  # populated from the role graph


def test_uncovered_excludes_already_satisfied_subskills():
    # backend.py ships >=1 stage-1 single_choice for several subskills already;
    # uncovered must return strictly fewer blueprints than the full tier-1 set.
    full = tier1_blueprints("backend")
    todo = uncovered_blueprints("backend", tier=1)
    assert len(todo) < len(full)


def test_uncovered_blueprints_raises_for_unsupported_tier():
    with pytest.raises(ValueError, match="unsupported tier"):
        uncovered_blueprints("backend", tier=3)


@pytest.mark.django_db
def test_tier2_subskills_are_a_subset_of_all_subskills():
    from apps.assessments.role_graph_data import ROLE_GRAPHS

    all_subs = {s.key for d in ROLE_GRAPHS["backend"].dimensions for s in d.subskills}
    demand = set(tier2_subskills("backend"))
    assert demand and demand.issubset(all_subs)
    assert len(demand) < len(all_subs)  # demand-weighted, not all subskills


@pytest.mark.django_db
def test_uncovered_tier2_returns_stage2_blueprints():
    todo = uncovered_blueprints("backend", tier=2)
    assert todo  # backend has little/no stage-2 content yet
    assert all(bp.stage == 2 for bp in todo)
    assert all(bp.question_type in ("single_choice", "multi_select", "open_ended") for bp in todo)


@pytest.mark.django_db
def test_uncovered_tier2_respects_per_type_floor():
    from apps.assessments.scenario_corpus.coverage import (
        _approved_counts,
        tier2_subskills,
        uncovered_blueprints,
    )

    demand = tier2_subskills("backend")
    counts = _approved_counts()
    # A demand subskill with no approved stage-2 content -> gaps equal the floor.
    target = next(
        s
        for s in demand
        if counts.get(("backend", 2, "single_choice", s), 0) == 0
        and counts.get(("backend", 2, "multi_select", s), 0) == 0
        and counts.get(("backend", 2, "open_ended", s), 0) == 0
    )
    todo = uncovered_blueprints("backend", tier=2)
    sc = [bp for bp in todo if bp.subskill_key == target and bp.question_type == "single_choice"]
    ms = [bp for bp in todo if bp.subskill_key == target and bp.question_type == "multi_select"]
    oe = [bp for bp in todo if bp.subskill_key == target and bp.question_type == "open_ended"]
    assert len(sc) == 2  # floor 2, have 0
    assert len(ms) == 1  # floor 1, have 0
    assert len(oe) == 1  # floor 1, have 0
