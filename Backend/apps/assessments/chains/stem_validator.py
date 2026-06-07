from __future__ import annotations

from apps.assessments.chains.enums import QuestionType
from apps.assessments.role_graph_taxonomy import is_debugging_dimension

DEBUGGING_SINGLE_STEM_PHRASES = (
    "first step",
    "first thing",
    "best initial",
    "most important first",
    "should you do first",
    "do first",
    "first when",
)

DEBUGGING_MULTI_STEM_PHRASES = (
    "which of the following",
    "select all",
    "what actions",
    "which steps",
    "what would you do",
    "help diagnose",
    "identify the root cause",
)

COMPOSITION_CONSTRAINT_WORDS = (
    "must support",
    "used by",
    "shared",
    "library",
    "ship today",
    "scalability",
    "independent teams",
    "different contexts",
)


def resolve_chain_question_type(
    *,
    semantic_type: str,
    dimension_key: str,
    blueprint: dict | None = None,
) -> QuestionType:
    if blueprint and blueprint.get("chain_question_type"):
        return QuestionType(str(blueprint["chain_question_type"]))
    if is_debugging_dimension(dimension_key):
        if semantic_type == "multi_select":
            return QuestionType.DEBUGGING_MULTI
        return QuestionType.DEBUGGING_SINGLE
    return {
        "single_choice": QuestionType.MCQ_SINGLE,
        "multi_select": QuestionType.MCQ_MULTI,
        "open_ended": QuestionType.OPEN_ENDED,
    }.get(semantic_type, QuestionType.MCQ_SINGLE)


def stem_matches_debugging_single(stem: str) -> bool:
    lowered = (stem or "").lower()
    return any(phrase in lowered for phrase in DEBUGGING_SINGLE_STEM_PHRASES)


def stem_matches_debugging_multi(stem: str) -> bool:
    lowered = (stem or "").lower()
    return any(phrase in lowered for phrase in DEBUGGING_MULTI_STEM_PHRASES)


def validate_stem_for_chain_type(question: dict, chain_type: QuestionType) -> bool:
    stem = str(
        question.get("stem")
        or question.get("question_text")
        or question.get("question")
        or ""
    ).lower()
    if chain_type == QuestionType.DEBUGGING_SINGLE:
        return stem_matches_debugging_single(stem)
    if chain_type == QuestionType.DEBUGGING_MULTI:
        return stem_matches_debugging_multi(stem) and "select all" in stem
    return True


def validate_composition_constraint(question: dict) -> bool:
    dimension = str(question.get("dimension_key") or question.get("skill_area") or "")
    if "composition" not in dimension:
        return True
    scenario = str(question.get("scenario_context") or "").lower()
    return any(word in scenario for word in COMPOSITION_CONSTRAINT_WORDS)


def validate_open_ended_specificity(question: dict) -> bool:
    stem = str(question.get("stem") or question.get("question_text") or "")
    if len(stem.split()) <= 40:
        return False
    lowered = stem.lower()
    return any(
        word in lowered
        for word in ("compare", "tradeoff", "versus", "instead of", "rather than", " vs ")
    )
