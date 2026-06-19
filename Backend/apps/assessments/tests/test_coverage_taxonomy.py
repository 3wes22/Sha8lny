"""Regression tests for role taxonomies, coverage, and debugging chain contracts."""

from __future__ import annotations

import pytest

from apps.assessments.chains.enums import QuestionType
from apps.assessments.chains.post_process import enrich_questions
from apps.assessments.chains.router import build_default_router
from apps.assessments.chains.stem_validator import (
    stem_matches_debugging_multi,
    stem_matches_debugging_single,
    validate_composition_constraint,
    validate_open_ended_specificity,
)
from apps.assessments.coverage import CoverageTracker
from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.assessments.role_graph_taxonomy import (
    BACKEND_DIMENSION_KEYS,
    FRONTEND_DIMENSION_KEYS,
    get_all_role_keys,
    get_taxonomy,
)


@pytest.fixture
def frontend_graph():
    return load_role_graph("frontend")


def test_all_roles_have_coverage_taxonomy():
    for role_key in get_all_role_keys():
        taxonomy = get_taxonomy(role_key)
        if role_key == "ui_ux_designer":
            continue
        assert taxonomy is not None, f"missing taxonomy for {role_key}"
        total = sum(float(spec["weight"]) for spec in taxonomy.values())
        assert abs(total - 1.0) < 0.02, f"{role_key} weights sum to {total}"
        assert all("min" in spec for spec in taxonomy.values())


def test_full_stack_alternates_domains():
    graph = load_role_graph("fullstack")
    targets = StageAllocator.allocate_stage_one(graph)
    frontend_count = sum(1 for target in targets if target.dimension in FRONTEND_DIMENSION_KEYS or target.dimension.startswith("fe_"))
    backend_count = sum(1 for target in targets if target.dimension in BACKEND_DIMENSION_KEYS or target.dimension.startswith("be_"))
    assert abs(frontend_count - backend_count) <= 1


def test_debugging_stem_matches_type(frontend_graph):
    router = build_default_router()
    single_bp = {
        "slot": 1,
        "subskill_key": "browser_debugging",
        "dimension_key": "debugging_devtools",
        "question_type": "single_choice",
        "chain_question_type": QuestionType.DEBUGGING_SINGLE.value,
    }
    multi_bp = {
        "slot": 2,
        "subskill_key": "network_panel",
        "dimension_key": "debugging_devtools",
        "question_type": "multi_select",
        "chain_question_type": QuestionType.DEBUGGING_MULTI.value,
    }
    single_q = {
        "subskill_key": "browser_debugging",
        "dimension_key": "debugging_devtools",
        "question_type": "single_choice",
        "stem": "What is the most effective first step to reproduce this React error?",
        "options": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
        "answer_key": {"correct_option_ids": ["a"]},
    }
    multi_q = {
        "subskill_key": "network_panel",
        "dimension_key": "debugging_devtools",
        "question_type": "multi_select",
        "stem": "Which of the following steps would help diagnose this API failure? Select all that apply.",
        "options": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
        "answer_key": {"correct_option_ids": ["a", "b"]},
    }
    lookup = {
        subskill.key: subskill
        for dimension in frontend_graph.dimensions
        for subskill in dimension.subskills
    }
    router.assign_helper(single_q, subskill=lookup["browser_debugging"], blueprint=single_bp)
    router.assign_helper(multi_q, subskill=lookup["network_panel"], blueprint=multi_bp)
    assert stem_matches_debugging_single(single_q["stem"])
    assert stem_matches_debugging_multi(multi_q["stem"])
    assert single_q.get("helper") == "Select the single best first action."
    assert "diagnostic evidence" in (multi_q.get("helper") or "").lower()


def test_composition_questions_have_constraint():
    question = {
        "dimension_key": "react_core",
        "subskill_key": "component_composition",
        "scenario_context": "The component is part of a shared library used by five teams.",
        "question_type": "single_choice",
    }
    assert validate_composition_constraint(question) is True


def test_open_ended_has_specific_component():
    stem = (
        "You are building a dashboard with a collapsible sidebar, a 3-column card grid, and sticky header. "
        "It requires the sidebar to collapse to a bottom nav on mobile and cards to keep a 16:9 image ratio. "
        "Describe your CSS strategy, comparing CSS Grid auto-fill versus auto-fit for the card grid, "
        "including at least one tradeoff and one approach you would rule out."
    )
    question = {"question_type": "open_ended", "stem": stem}
    assert validate_open_ended_specificity(question) is True


def test_coverage_tracker_assessment_wide(frontend_graph):
    tracker = CoverageTracker.from_role_graph(frontend_graph)
    stage_one = [
        {"dimension_key": "javascript_fundamentals"},
        {"dimension_key": "react_core"},
        {"dimension_key": "react_hooks_depth"},
        {"dimension_key": "css_layout_styling"},
        {"dimension_key": "debugging_devtools"},
    ]
    stage_two = [
        {"dimension_key": "state_management"},
        {"dimension_key": "performance_optimization"},
        {"dimension_key": "typescript_basics"},
        {"dimension_key": "testing"},
        {"dimension_key": "security_basics"},
    ]
    tracker.seed_from_questions(stage_one)
    tracker.seed_from_questions(stage_two)
    uncovered = tracker.get_uncovered_dimensions()
    assert "html_accessibility" in uncovered or len(uncovered) > 0
