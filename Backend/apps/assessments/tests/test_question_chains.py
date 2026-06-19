"""Tests for typed question chains, bleed fix, coverage, rubric, and MCQ rules."""

from __future__ import annotations

import pytest

from apps.assessments.ai_pipeline import (
    _apply_chain_helper_to_template,
    _contract_safe_stage_template,
)
from apps.assessments.chains.ambiguity_validator import needs_ambiguity_check
from apps.assessments.chains.post_process import enrich_questions
from apps.assessments.chains.router import BLEED_PHRASES, QuestionTypeRouter, build_default_router
from apps.assessments.chains.rubric_chain import fallback_rubric, normalize_rubric
from apps.assessments.coverage import CoverageTracker
from apps.assessments.engine import AnswerScorer
from apps.assessments.role_graph import load_role_graph
from apps.core.ai_validation import build_stage_validation_flags


@pytest.fixture
def frontend_graph():
    return load_role_graph("frontend")


@pytest.fixture
def router():
    return build_default_router()


def _subskill(graph, key: str):
    for dimension in graph.dimensions:
        for subskill in dimension.subskills:
            if subskill.key == key:
                return subskill
    raise KeyError(key)


def test_isolated_templates_do_not_share_debugging_framing(router):
    from apps.assessments.chains.enums import QuestionType

    single = router._chains[QuestionType.MCQ_SINGLE]
    multi = router._chains[QuestionType.MCQ_MULTI]
    open_chain = router._chains[QuestionType.OPEN_ENDED]
    assert "blast radius" not in single.instruction_block().lower()
    assert "gather evidence" not in open_chain.instruction_block().lower()
    assert "Select all that apply" in multi.instruction_block()


def test_mcq_single_helper_is_none(router):
    slot = {"question_type": "single_choice", "subskill_key": "semantic_html"}
    chain = router.chain_for_slot(slot)
    assert chain.helper is None


def test_debugging_chain_only_for_debugging_dimension(router, frontend_graph):
    from apps.assessments.chains.enums import QuestionType

    debugging = _subskill(frontend_graph, "browser_debugging")
    regular = _subskill(frontend_graph, "semantic_html")
    debug_chain = router.chain_for_slot(
        {
            "question_type": "single_choice",
            "subskill_key": debugging.key,
            "dimension_key": debugging.dimension,
            "chain_question_type": QuestionType.DEBUGGING_SINGLE.value,
        },
        subskill=debugging,
    )
    regular_chain = router.chain_for_slot(
        {
            "question_type": "single_choice",
            "subskill_key": regular.key,
            "dimension_key": regular.dimension,
        },
        subskill=regular,
    )
    assert debug_chain.helper == "Select the single best first action."
    assert regular_chain.helper is None


def test_no_blast_radius_bleed_in_generic_fallback_templates(frontend_graph):
    router = build_default_router()
    samples = []
    for subskill in (
        _subskill(frontend_graph, "semantic_html"),
        _subskill(frontend_graph, "component_composition"),
        _subskill(frontend_graph, "browser_debugging"),
    ):
        for question_type in ("single_choice", "multi_select", "open_ended"):
            template = _contract_safe_stage_template(
                stage=2,
                subskill=subskill,
                role_key="frontend",
                role_label="Frontend Developer",
                question_type=question_type,
            )
            probe = {
                "question_type": question_type,
                "subskill_key": subskill.key,
                "stem": template.get("stem", ""),
                "question_text": template.get("question_text", ""),
                "helper": template.get("helper", ""),
            }
            router.assign_helper(probe, subskill=subskill)
            samples.append((subskill, probe))

    for subskill, question in samples:
        combined = f"{question.get('stem', '')} {question.get('helper', '')}".lower()
        is_debugging = getattr(subskill, "frame", None) == "debugging"
        for phrase in BLEED_PHRASES:
            if phrase in combined and not is_debugging:
                pytest.fail(f"Bleed phrase '{phrase}' in non-debugging question: {question}")


def test_router_batch_prompt_assembles_slots(router, frontend_graph):
    blueprints = [
        {
            "slot": 1,
            "subskill_key": "semantic_html",
            "dimension_key": "interface_foundations",
            "question_type": "single_choice",
            "competency": "Semantic HTML",
            "learning_objective_hint": "Test HTML",
            "difficulty": 3,
            "focus": "narrow one decision",
        },
        {
            "slot": 2,
            "subskill_key": "browser_debugging",
            "dimension_key": "debugging_devtools",
            "question_type": "single_choice",
            "chain_question_type": "debugging_single",
            "competency": "Browser Debugging",
            "learning_objective_hint": "Test debugging",
            "difficulty": 4,
            "focus": "diagnosis",
        },
    ]
    lookup = {
        subskill.key: subskill
        for dimension in frontend_graph.dimensions
        for subskill in dimension.subskills
    }
    prompt = router.build_batch_prompt(
        role_label="Frontend Developer",
        stage=2,
        slots=blueprints,
        subskill_lookup=lookup,
    )
    assert "mcq_single" in prompt or "single_choice" in prompt
    assert "browser_debugging" in prompt
    assert "Do not embed sub-instructions" in prompt


def test_coverage_tracker_from_role_graph(frontend_graph):
    tracker = CoverageTracker.from_role_graph(frontend_graph)
    tracker.record({"dimension_key": "javascript_fundamentals"})
    tracker.record({"dimension_key": "javascript_fundamentals"})
    tracker.record({"dimension_key": "javascript_fundamentals"})
    assert tracker.get_dimension_count("javascript_fundamentals") == 3
    assert "react_hooks_depth" in tracker.get_uncovered_dimensions()


def test_mcq_single_one_correct_after_enrich(frontend_graph):
    blueprints = [
        {
            "slot": 1,
            "subskill_key": "semantic_html",
            "dimension_key": "interface_foundations",
            "question_type": "single_choice",
            "competency": "Semantic HTML",
            "difficulty": 3,
        }
    ]
    questions = [
        {
            "id": "s1_q1",
            "subskill_key": "semantic_html",
            "dimension_key": "interface_foundations",
            "question_type": "single_choice",
            "question_text": "A team must pick a layout approach. Which option is best?",
            "options": [
                {"id": "a", "label": "Use CSS Grid with defined areas."},
                {"id": "b", "label": "Use only absolute positioning."},
                {"id": "c", "label": "Inline all styles in HTML."},
                {"id": "d", "label": "Skip responsive testing."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "option_rationales": [
                {"option_id": "a", "is_correct": True, "rationale": "Grid supports layout intent."},
                {"option_id": "b", "is_correct": False, "rationale": "Absolute positioning is brittle."},
                {"option_id": "c", "is_correct": False, "rationale": "Inline styles harm maintainability."},
                {"option_id": "d", "is_correct": False, "rationale": "Skipping testing increases risk."},
            ],
        }
    ]
    enriched = enrich_questions(
        questions,
        role_graph=frontend_graph,
        blueprints=blueprints,
        run_ambiguity=False,
        run_rubric=False,
    )
    for question in enriched:
        flags = build_stage_validation_flags(question)
        assert "single_choice_requires_exactly_one_correct_option" not in flags


def test_open_ended_has_rubric(frontend_graph):
    blueprints = [
        {
            "slot": 1,
            "subskill_key": "responsive_css",
            "dimension_key": "css_layout_styling",
            "question_type": "open_ended",
            "competency": "Responsive CSS",
            "difficulty": 3,
        }
    ]
    questions = [
        {
            "id": "s2_q5",
            "subskill_key": "responsive_css",
            "dimension_key": "css_layout_styling",
            "question_type": "open_ended",
            "question_text": (
                "You are building a dashboard with a collapsible sidebar and 3-column card grid. "
                "It requires mobile bottom-nav collapse and 16:9 card images. "
                "Compare CSS Grid auto-fill versus auto-fit for the grid, stating tradeoffs."
            ),
            "options": [],
            "answer_key": {
                "expected_concepts": ["components", "tokens", "tradeoffs"],
                "required_concept_count": 2,
                "scoring": "concept_coverage",
            },
        }
    ]
    enriched = enrich_questions(
        questions,
        role_graph=frontend_graph,
        blueprints=blueprints,
        run_ambiguity=False,
        run_rubric=True,
    )
    rubric = enriched[0].get("rubric")
    assert rubric is not None
    weights = sum(d["weight"] for d in rubric["scoring_dimensions"])
    assert abs(weights - 1.0) < 1e-3


def test_multi_select_correct_range(frontend_graph):
    blueprints = [
        {
            "slot": 1,
            "subskill_key": "frontend_testing",
            "dimension_key": "testing",
            "question_type": "multi_select",
            "competency": "Unit Testing",
            "difficulty": 3,
        }
    ]
    questions = [
        {
            "id": "s2_q3",
            "subskill_key": "frontend_testing",
            "dimension_key": "testing",
            "question_type": "multi_select",
            "question_text": "Which practices help? Select all that apply.",
            "options": [
                {"id": "a", "label": "Unit tests for utilities."},
                {"id": "b", "label": "Integration tests for flows."},
                {"id": "c", "label": "Skip CI."},
                {"id": "d", "label": "Snapshot tests for UI."},
                {"id": "e", "label": "Delete the test suite."},
            ],
            "answer_key": {"correct_option_ids": ["a", "b", "d"], "scoring": "partial_credit"},
            "option_rationales": [],
        }
    ]
    enriched = enrich_questions(
        questions,
        role_graph=frontend_graph,
        blueprints=blueprints,
        run_ambiguity=False,
        run_rubric=False,
    )
    correct = enriched[0]["answer_key"]["correct_option_ids"]
    assert 2 <= len(correct) <= 3


def test_needs_ambiguity_check_heuristic():
    ambiguous = {
        "question_type": "single_choice",
        "options": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
        "answer_key": {"correct_option_ids": ["a"]},
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Best for long-term scalability."},
            {"option_id": "b", "is_correct": False, "rationale": "Also valid depending on team context and seniority."},
            {"option_id": "c", "is_correct": False, "rationale": "Wrong for this scenario."},
        ],
    }
    clear = {
        "question_type": "single_choice",
        "options": [{"id": "a"}, {"id": "b"}, {"id": "c"}, {"id": "d"}],
        "answer_key": {"correct_option_ids": ["a"]},
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Correct approach."},
            {"option_id": "b", "is_correct": False, "rationale": "Wrong because it breaks encapsulation."},
        ],
    }
    assert needs_ambiguity_check(ambiguous) is True
    assert needs_ambiguity_check(clear) is False


def test_rubric_scoring_uses_required_concepts(frontend_graph):
    question = {
        "question_type": "open_ended",
        "rubric": fallback_rubric(
            {
                "id": "q1",
                "answer_key": {
                    "expected_concepts": ["grid", "flexbox", "tradeoffs"],
                    "forbidden_concepts": ["no plan"],
                },
            }
        ),
        "answer_key": {},
    }
    score, confidence = AnswerScorer._score_open_ended_with_rubric(
        question,
        "I would use CSS Grid for layout and flexbox for alignment, with tradeoffs on browser support.",
        question["rubric"],
    )
    assert score >= 4.0
    assert confidence >= 0.7


def test_normalize_rubric_weights_sum_to_one():
    rubric = normalize_rubric(
        {
            "question_id": "q1",
            "scoring_dimensions": [
                {"dimension": "a", "weight": 2, "score_1_descriptor": "", "score_3_descriptor": "", "score_5_descriptor": ""},
                {"dimension": "b", "weight": 2, "score_1_descriptor": "", "score_3_descriptor": "", "score_5_descriptor": ""},
            ],
            "required_concepts": [],
            "bonus_concepts": [],
            "auto_fail_if": [],
        },
        question_id="q1",
    )
    total = sum(item["weight"] for item in rubric["scoring_dimensions"])
    assert abs(total - 1.0) < 1e-3
