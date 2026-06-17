from __future__ import annotations

import pytest

from apps.assessments.scenario_corpus.coverage import (
    Blueprint,
    stage1_calibration_subskills,
    tier1_blueprints,
    uncovered_blueprints,
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
