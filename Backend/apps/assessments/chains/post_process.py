from __future__ import annotations

from typing import Any

from apps.assessments.chains.ambiguity_validator import AmbiguityValidator, needs_ambiguity_check
from apps.assessments.chains.enums import QuestionType
from apps.assessments.chains.open_ended_chain import OpenEndedChain
from apps.assessments.chains.router import QuestionTypeRouter, build_default_router
from apps.assessments.chains.rubric_chain import RubricChain
from apps.assessments.chains.stem_validator import (
    resolve_chain_question_type,
    validate_composition_constraint,
    validate_open_ended_specificity,
    validate_stem_for_chain_type,
)
from apps.assessments.coverage import CoverageTracker
from apps.assessments.role_graph import RoleGraph, SubSkill
from apps.assessments.role_graph_taxonomy import is_debugging_dimension
from apps.core import ai_settings as core_ai_settings
from apps.core.gemma_client import GemmaClient


def _subskill_lookup(role_graph: RoleGraph) -> dict[str, SubSkill]:
    return {
        subskill.key: subskill
        for dimension in role_graph.dimensions
        for subskill in dimension.subskills
    }


def enrich_questions(
    questions: list[dict[str, Any]],
    *,
    role_graph: RoleGraph,
    blueprints: list[dict[str, Any]],
    router: QuestionTypeRouter | None = None,
    client: GemmaClient | None = None,
    run_ambiguity: bool = True,
    run_rubric: bool = True,
    coverage_tracker: CoverageTracker | None = None,
) -> list[dict[str, Any]]:
    """Post-generation: helpers, ambiguity checks, rubrics, coverage metadata."""
    router = router or build_default_router()
    lookup = _subskill_lookup(role_graph)
    blueprint_by_subskill = {
        str(bp.get("subskill_key") or ""): bp for bp in blueprints
    }
    coverage = coverage_tracker or CoverageTracker.from_role_graph(role_graph)
    ambiguity = AmbiguityValidator(client=client)
    rubric_chain = RubricChain(client=client)
    open_chain = OpenEndedChain()
    template_version = "chains-v2"

    enriched: list[dict[str, Any]] = []
    for question in questions:
        if not isinstance(question, dict):
            continue
        subskill_key = str(question.get("subskill_key") or "")
        subskill = lookup.get(subskill_key)
        blueprint = blueprint_by_subskill.get(subskill_key) or {}
        router.assign_helper(question, subskill=subskill, blueprint=blueprint)
        _normalize_multi_select_bounds(question)

        gen_meta = dict(question.get("generation_metadata") or {})
        gen_meta.setdefault("template_version", template_version)
        gen_meta["ambiguity_check_passed"] = True
        gen_meta["coverage_slot_filled"] = subskill_key

        dimension_key = str(question.get("dimension_key") or (subskill.dimension if subskill else ""))
        chain_type = resolve_chain_question_type(
            semantic_type=str(question.get("question_type") or ""),
            dimension_key=dimension_key,
            blueprint=blueprint,
        )
        gen_meta["chain_question_type"] = chain_type.value

        flags = list(question.get("validation_flags") or [])
        if not validate_stem_for_chain_type(question, chain_type):
            if "stem_type_mismatch" not in flags:
                flags.append("stem_type_mismatch")
        if not validate_composition_constraint(question):
            if "composition_missing_constraint" not in flags:
                flags.append("composition_missing_constraint")
        if str(question.get("question_type") or "") == "open_ended" and not validate_open_ended_specificity(
            question
        ):
            if "open_ended_too_generic" not in flags:
                flags.append("open_ended_too_generic")
        if flags:
            question["validation_flags"] = sorted(set(flags))

        q_type = str(question.get("question_type") or "")
        ambiguity_enabled = (
            run_ambiguity and core_ai_settings.ASSESSMENT_AMBIGUITY_VALIDATION_ENABLED
        )
        is_debugging = is_debugging_dimension(dimension_key) or chain_type in {
            QuestionType.DEBUGGING_SINGLE,
            QuestionType.DEBUGGING_MULTI,
        }
        if ambiguity_enabled and q_type == "single_choice" and needs_ambiguity_check(question):
            if not is_debugging:
                result = ambiguity.run(question)
                gen_meta["ambiguity_check_passed"] = bool(result.get("unambiguous"))
                if not result.get("unambiguous"):
                    question = ambiguity.apply_disambiguation(question, result)
                    recheck = ambiguity.run(question)
                    gen_meta["ambiguity_check_passed"] = bool(recheck.get("unambiguous"))
                    if not recheck.get("unambiguous"):
                        question = _convert_to_open_ended(question, open_chain=open_chain)
                        q_type = "open_ended"
                        router.assign_helper(question, subskill=subskill, blueprint=blueprint)
                        gen_meta["converted_from_ambiguous_mcq"] = True

        if run_rubric and str(question.get("question_type") or "") == "open_ended":
            if core_ai_settings.ASSESSMENT_RUBRIC_LLM_ENABLED and client is not None:
                question["rubric"] = rubric_chain.run(question)
                gen_meta["rubric_template_version"] = rubric_chain.template_version
            else:
                from apps.assessments.chains.rubric_chain import fallback_rubric

                question["rubric"] = fallback_rubric(question)
                gen_meta["rubric_template_version"] = "rubric-fallback"
            _sync_answer_key_from_rubric(question)

        question["generation_metadata"] = gen_meta
        coverage.record(question)
        enriched.append(question)

    return enriched


def _convert_to_open_ended(
    question: dict[str, Any],
    *,
    open_chain: OpenEndedChain,
) -> dict[str, Any]:
    question["question_type"] = "open_ended"
    question["type"] = "text"
    question["interaction_mode"] = "text"
    question["options"] = []
    answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
    if not answer_key.get("expected_concepts"):
        answer_key = {
            "expected_concepts": ["approach", "tradeoffs", "constraints"],
            "required_concept_count": 2,
            "forbidden_concepts": [],
            "scoring": "concept_coverage",
        }
        question["answer_key"] = answer_key
    helper = open_chain.helper
    if helper:
        question["helper"] = helper
    return question


def _normalize_multi_select_bounds(question: dict[str, Any]) -> None:
    if str(question.get("question_type") or "") != "multi_select":
        return
    answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
    correct_ids = list(answer_key.get("correct_option_ids") or [])
    if len(correct_ids) == 1:
        question["question_type"] = "single_choice"
        question["type"] = "multiple_choice"
        question["interaction_mode"] = "single_select"
        answer_key["scoring"] = "single_best"
        question.pop("helper", None)
        return
    if len(correct_ids) > 3:
        flags = list(question.get("validation_flags") or [])
        if "multi_select_too_many_correct_options" not in flags:
            flags.append("multi_select_too_many_correct_options")
        question["validation_flags"] = sorted(set(flags))


def _sync_answer_key_from_rubric(question: dict[str, Any]) -> None:
    rubric = question.get("rubric")
    if not isinstance(rubric, dict):
        return
    answer_key = dict(question.get("answer_key") or {})
    if rubric.get("required_concepts"):
        answer_key["expected_concepts"] = rubric["required_concepts"]
        answer_key["required_concept_count"] = min(
            len(rubric["required_concepts"]),
            max(1, int(answer_key.get("required_concept_count") or 2)),
        )
    if rubric.get("auto_fail_if"):
        answer_key["forbidden_concepts"] = rubric["auto_fail_if"]
    answer_key.setdefault("scoring", "rubric_weighted")
    question["answer_key"] = answer_key
