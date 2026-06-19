"""Tests for the authored scenario corpus.

Covers:
    - Every approved scenario passes ``validate_scenario`` with zero errors.
    - Every ``doc_id`` is unique across per-role modules.
    - Every ``role_key``/``subskill_key`` exists in ``ROLE_GRAPHS``.
    - Every approved ``corpus_version`` equals ``SCENARIO_CORPUS_VERSION``.
    - ``assert_corpus_integrity`` returns cleanly on the current corpus.

See ``specs/005-scenario-rag-corpus/tasks.md`` T015 + T026 + T027.
"""

from __future__ import annotations

import copy

import pytest

from apps.assessments.role_graph_data import ROLE_GRAPHS
from apps.assessments.scenario_corpus.registry import (
    SCENARIO_CORPUS_VERSION,
    assert_corpus_integrity,
    iter_all_scenarios,
    iter_approved_scenarios,
)
from apps.assessments.scenario_corpus.schema import (
    ScenarioDocument,
    iter_validation_errors,
    validate_scenario,
)


# ---------------------------------------------------------------------------
# Corpus integrity (T015)
# ---------------------------------------------------------------------------


def test_corpus_integrity_passes_on_current_corpus():
    assert_corpus_integrity()


def test_every_approved_scenario_validates_with_zero_errors():
    failures = iter_validation_errors(iter_approved_scenarios())
    assert failures == [], (
        "Every approved scenario must validate cleanly. Failures:\n"
        + "\n".join(f"{doc_id}: {errors}" for doc_id, errors in failures)
    )


def test_every_doc_id_is_unique():
    seen: dict[str, str] = {}
    duplicates: list[str] = []
    for scenario in iter_all_scenarios():
        doc_id = scenario.get("doc_id")
        if not doc_id:
            continue
        if doc_id in seen:
            duplicates.append(f"{doc_id} (first seen in {seen[doc_id]})")
        else:
            seen[doc_id] = scenario.get("role_key") or "<unknown>"
    assert not duplicates, f"Duplicate doc_ids: {duplicates}"


def test_every_role_and_subskill_key_exists_in_role_graphs():
    for scenario in iter_all_scenarios():
        role_key = scenario["role_key"]
        subskill_key = scenario["subskill_key"]
        assert role_key in ROLE_GRAPHS, (
            f"{scenario['doc_id']}: role_key {role_key!r} not in ROLE_GRAPHS"
        )
        graph = ROLE_GRAPHS[role_key]
        subskill_keys = {
            subskill.key
            for dimension in graph.dimensions
            for subskill in dimension.subskills
        }
        assert subskill_key in subskill_keys, (
            f"{scenario['doc_id']}: subskill_key {subskill_key!r} not in role "
            f"graph for {role_key!r}"
        )


def test_every_approved_doc_uses_current_corpus_version():
    for scenario in iter_approved_scenarios():
        assert scenario["corpus_version"] == SCENARIO_CORPUS_VERSION, (
            f"{scenario['doc_id']}: corpus_version "
            f"{scenario['corpus_version']!r} != {SCENARIO_CORPUS_VERSION!r}"
        )


def test_every_dimension_key_matches_role_graph():
    for scenario in iter_all_scenarios():
        role_key = scenario["role_key"]
        graph = ROLE_GRAPHS[role_key]
        subskill_to_dim = {
            subskill.key: dimension.key
            for dimension in graph.dimensions
            for subskill in dimension.subskills
        }
        expected = subskill_to_dim[scenario["subskill_key"]]
        assert scenario["dimension_key"] == expected, (
            f"{scenario['doc_id']}: dimension_key {scenario['dimension_key']!r} "
            f"!= role-graph dimension {expected!r}"
        )


# ---------------------------------------------------------------------------
# Coverage floor (T026)
# ---------------------------------------------------------------------------


def test_coverage_floor_for_backend_stage1_single_choice_seed():
    """The v1 backend seed must cover every stage-1 allocation subskill with
    at least one approved stage-1 single_choice scenario.
    """
    from apps.assessments.engine import StageAllocator
    from apps.assessments.role_graph import load_role_graph

    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    target_subskills = {target.key for target in targets}

    backend_stage1_single = {
        s["subskill_key"]
        for s in iter_approved_scenarios()
        if s["role_key"] == "backend"
        and s["stage"] == 1
        and s["question_type"] == "single_choice"
    }
    missing = target_subskills - backend_stage1_single
    assert not missing, (
        "Backend stage-1 allocation subskills missing seed coverage: "
        f"{sorted(missing)}"
    )


def test_coverage_audit_reports_empty_roles_for_v1_seed():
    """All non-backend roles are intentionally empty in v1; the audit's
    coverage matrix must therefore mark them as below-floor."""
    seen_roles = {s["role_key"] for s in iter_approved_scenarios()}
    assert "backend" in seen_roles, "Backend seed should be approved in v1"
    for role_key in ("frontend", "fullstack", "data_science", "devops",
                     "android", "machine_learning_engineer", "ui_ux_designer"):
        assert role_key not in seen_roles, (
            f"v1 must ship only the backend seed; found unexpected approved "
            f"content for {role_key!r}"
        )


# ---------------------------------------------------------------------------
# Validator rejects intentional violations (T027)
# ---------------------------------------------------------------------------


def _base_valid_single_choice() -> ScenarioDocument:
    """Return a known-valid single_choice scenario derived from the seed."""
    from apps.assessments.scenario_corpus.backend import SCENARIOS

    for scenario in SCENARIOS:
        if scenario["question_type"] == "single_choice" and scenario["stage"] == 1:
            return copy.deepcopy(scenario)
    raise RuntimeError("No backend single_choice seed scenario available")


def test_validator_passes_on_unmodified_seed():
    doc = _base_valid_single_choice()
    assert validate_scenario(doc) == []


def test_validator_rejects_missing_required_field():
    doc = _base_valid_single_choice()
    del doc["correct_answer_rationale"]
    errors = validate_scenario(doc)
    assert any("missing required field: correct_answer_rationale" in e for e in errors)


def test_validator_rejects_wrong_option_count_for_single_choice():
    doc = _base_valid_single_choice()
    doc["options"] = doc["options"][:3]
    doc["option_rationales"] = doc["option_rationales"][:3]
    errors = validate_scenario(doc)
    assert any("single_choice requires exactly 4 options" in e for e in errors)


def test_validator_rejects_mismatched_dimension_key():
    doc = _base_valid_single_choice()
    doc["dimension_key"] = "delivery_collaboration"  # actual is api_service_design
    errors = validate_scenario(doc)
    assert any("dimension_key" in e and "does not match role graph" in e for e in errors)


def test_validator_rejects_stale_corpus_version():
    doc = _base_valid_single_choice()
    doc["corpus_version"] = "scenario-vNEXT"
    errors = validate_scenario(doc)
    assert any("corpus_version" in e and "does not equal" in e for e in errors)


def test_validator_rejects_unknown_role_key():
    doc = _base_valid_single_choice()
    doc["role_key"] = "platform_engineer"
    doc["doc_id"] = "platform_engineer.http_api_design.s1.single_choice.bad-role"
    errors = validate_scenario(doc)
    assert any("role_key" in e and "not present in ROLE_GRAPHS" in e for e in errors)


def test_validator_rejects_unknown_subskill_key():
    doc = _base_valid_single_choice()
    doc["subskill_key"] = "spline_design"
    doc["doc_id"] = "backend.spline_design.s1.single_choice.bad-subskill"
    errors = validate_scenario(doc)
    assert any(
        "subskill_key" in e and "not present in role graph" in e for e in errors
    )


def test_validator_rejects_invalid_doc_id_pattern():
    doc = _base_valid_single_choice()
    doc["doc_id"] = "BackEnd.HTTP_API_DESIGN.s1.single_choice.bad"
    errors = validate_scenario(doc)
    assert any("doc_id" in e and "does not match expected pattern" in e for e in errors)


def test_validator_rejects_multi_select_with_only_one_correct():
    from apps.assessments.scenario_corpus.backend import SCENARIOS

    multi = None
    for scenario in SCENARIOS:
        if scenario["question_type"] == "multi_select":
            multi = copy.deepcopy(scenario)
            break
    assert multi is not None, "Expected a multi_select seed scenario"

    multi["answer_key"]["correct_option_ids"] = [
        multi["answer_key"]["correct_option_ids"][0]
    ]
    for rationale in multi["option_rationales"]:
        rationale["is_correct"] = rationale["option_id"] == multi["answer_key"]["correct_option_ids"][0]

    errors = validate_scenario(multi)
    assert any(
        "multi_select answer_key.correct_option_ids must have 2 or 3 entries" in e
        for e in errors
    )


def test_validator_rejects_open_ended_with_options():
    from apps.assessments.scenario_corpus.backend import SCENARIOS

    open_ended = None
    for scenario in SCENARIOS:
        if scenario["question_type"] == "open_ended":
            open_ended = copy.deepcopy(scenario)
            break
    assert open_ended is not None, "Expected an open_ended seed scenario"

    open_ended["options"] = [{"id": "a", "label": "extra option that should not exist"}]
    errors = validate_scenario(open_ended)
    assert any("open_ended must have an empty options list" in e for e in errors)
