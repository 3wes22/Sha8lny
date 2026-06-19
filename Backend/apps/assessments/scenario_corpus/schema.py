"""Typed schema and validator for the assessment scenario corpus.

Implements the rules from
``specs/005-scenario-rag-corpus/data-model.md`` and delegates the live
question-contract validation to
``apps.core.ai_validation.build_stage_validation_flags`` so the corpus
cannot drift below the in-production validation bar.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, Literal, TypedDict

from apps.core.ai_validation import build_stage_validation_flags


QuestionType = Literal["single_choice", "multi_select", "open_ended"]
ReviewStatus = Literal["draft", "approved"]


class ScenarioOption(TypedDict):
    id: str
    label: str


class ScenarioOptionRationale(TypedDict):
    option_id: str
    is_correct: bool
    rationale: str


class ScenarioDocument(TypedDict, total=False):
    # Identity / retrieval keys
    doc_id: str
    role_key: str
    subskill_key: str
    competency: str
    dimension_key: str
    stage: Literal[1, 2]
    question_type: QuestionType
    difficulty: int
    estimated_seconds: int

    # Few-shot payload (aligned with the LLM question schema)
    learning_objective: str
    scenario_context: str
    stem: str
    options: list[ScenarioOption]
    answer_key: dict[str, Any]
    explanation: str
    correct_answer_rationale: str
    option_rationales: list[ScenarioOptionRationale]
    helper: str

    # Provenance / governance
    author: str
    license: str
    review_status: ReviewStatus
    created_at: str
    corpus_version: str


_DOC_ID_PATTERN = re.compile(
    r"^[a-z0-9_]+\.[a-z0-9_]+\.s[12]\.(single_choice|multi_select|open_ended)\.[a-z0-9_-]+$"
)
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_REQUIRED_FIELDS: tuple[str, ...] = (
    "doc_id",
    "role_key",
    "subskill_key",
    "competency",
    "dimension_key",
    "stage",
    "question_type",
    "difficulty",
    "estimated_seconds",
    "learning_objective",
    "scenario_context",
    "stem",
    "options",
    "answer_key",
    "explanation",
    "correct_answer_rationale",
    "option_rationales",
    "author",
    "license",
    "review_status",
    "created_at",
    "corpus_version",
)

_ALLOWED_QUESTION_TYPES: frozenset[str] = frozenset(
    {"single_choice", "multi_select", "open_ended"}
)
_ALLOWED_REVIEW_STATUSES: frozenset[str] = frozenset({"draft", "approved"})
_ALLOWED_SCORING_BY_TYPE: dict[str, str] = {
    "single_choice": "single_best",
    "multi_select": "partial_credit",
    "open_ended": "concept_coverage",
}


def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _load_role_graphs():
    """Import here to keep schema.py importable in test contexts without Django app readiness."""
    from apps.assessments.role_graph_data import ROLE_GRAPHS

    return ROLE_GRAPHS


def _subskill_lookup(role_graph) -> dict[str, Any]:
    return {
        subskill.key: subskill
        for dimension in role_graph.dimensions
        for subskill in dimension.subskills
    }


def _validate_answer_key_shape(doc: ScenarioDocument, errors: list[str]) -> None:
    question_type = doc.get("question_type")
    answer_key = doc.get("answer_key") or {}
    if not isinstance(answer_key, dict):
        errors.append("answer_key must be a dict")
        return

    expected_scoring = _ALLOWED_SCORING_BY_TYPE.get(str(question_type))
    if expected_scoring is None or answer_key.get("scoring") != expected_scoring:
        errors.append(
            f"answer_key.scoring must be '{expected_scoring}' for question_type "
            f"'{question_type}', got {answer_key.get('scoring')!r}"
        )

    if question_type == "single_choice":
        correct_ids = answer_key.get("correct_option_ids")
        if not isinstance(correct_ids, list) or len(correct_ids) != 1:
            errors.append("single_choice answer_key.correct_option_ids must have exactly 1 entry")
    elif question_type == "multi_select":
        correct_ids = answer_key.get("correct_option_ids")
        if not isinstance(correct_ids, list) or len(correct_ids) not in (2, 3):
            errors.append("multi_select answer_key.correct_option_ids must have 2 or 3 entries")
    elif question_type == "open_ended":
        expected = answer_key.get("expected_concepts")
        if not isinstance(expected, list) or len(expected) != 3:
            errors.append("open_ended answer_key.expected_concepts must be a list of length 3")
        required_count = answer_key.get("required_concept_count")
        if not isinstance(required_count, int) or not 1 <= required_count <= 5:
            errors.append("open_ended answer_key.required_concept_count must be an int in [1, 5]")
        forbidden = answer_key.get("forbidden_concepts")
        if not isinstance(forbidden, list) or len(forbidden) != 1:
            errors.append("open_ended answer_key.forbidden_concepts must be a list of length 1")


def _validate_options_and_rationales(doc: ScenarioDocument, errors: list[str]) -> None:
    question_type = doc.get("question_type")
    options = doc.get("options") or []
    option_rationales = doc.get("option_rationales") or []

    if not isinstance(options, list):
        errors.append("options must be a list")
        return
    if not isinstance(option_rationales, list):
        errors.append("option_rationales must be a list")
        return

    if question_type == "single_choice":
        if len(options) != 4:
            errors.append(f"single_choice requires exactly 4 options, got {len(options)}")
    elif question_type == "multi_select":
        if len(options) != 5:
            errors.append(f"multi_select requires exactly 5 options, got {len(options)}")
        stem = str(doc.get("stem") or "")
        if "select all that apply" not in stem.lower():
            errors.append("multi_select stem must contain 'Select all that apply.'")
    elif question_type == "open_ended":
        if options:
            errors.append("open_ended must have an empty options list")
        if option_rationales:
            errors.append("open_ended must have an empty option_rationales list")

    if question_type in {"single_choice", "multi_select"}:
        option_ids: list[str] = []
        for index, option in enumerate(options):
            if not isinstance(option, dict):
                errors.append(f"options[{index}] must be a dict")
                continue
            opt_id = option.get("id")
            opt_label = option.get("label")
            if not _is_non_empty_str(opt_id):
                errors.append(f"options[{index}].id must be a non-empty string")
            else:
                option_ids.append(opt_id)
            if not _is_non_empty_str(opt_label):
                errors.append(f"options[{index}].label must be a non-empty string")

        if len(option_rationales) != len(options):
            errors.append(
                "option_rationales must have one entry per option, "
                f"got {len(option_rationales)} for {len(options)} options"
            )
        correct_count = 0
        seen_option_ids: set[str] = set()
        for index, rationale in enumerate(option_rationales):
            if not isinstance(rationale, dict):
                errors.append(f"option_rationales[{index}] must be a dict")
                continue
            rid = rationale.get("option_id")
            if not _is_non_empty_str(rid):
                errors.append(f"option_rationales[{index}].option_id must be a non-empty string")
            else:
                if rid not in option_ids:
                    errors.append(
                        f"option_rationales[{index}].option_id {rid!r} not present in options"
                    )
                if rid in seen_option_ids:
                    errors.append(
                        f"option_rationales[{index}].option_id {rid!r} duplicated"
                    )
                seen_option_ids.add(rid)
            if not isinstance(rationale.get("is_correct"), bool):
                errors.append(f"option_rationales[{index}].is_correct must be a bool")
            if not _is_non_empty_str(rationale.get("rationale")):
                errors.append(
                    f"option_rationales[{index}].rationale must be a non-empty string"
                )
            if rationale.get("is_correct") is True:
                correct_count += 1

        if question_type == "single_choice" and correct_count != 1:
            errors.append(
                "single_choice option_rationales must mark exactly one option as is_correct=True"
            )
        if question_type == "multi_select" and correct_count not in (2, 3):
            errors.append(
                "multi_select option_rationales must mark 2 or 3 options as is_correct=True"
            )

        answer_key_ids = (doc.get("answer_key") or {}).get("correct_option_ids") or []
        for cid in answer_key_ids:
            if cid not in option_ids:
                errors.append(
                    f"answer_key.correct_option_ids references unknown option {cid!r}"
                )


def _scenario_as_question(doc: ScenarioDocument) -> dict[str, Any]:
    """Reshape a ScenarioDocument into the dict shape that
    ``build_stage_validation_flags`` expects."""
    scenario_context = str(doc.get("scenario_context") or "").strip()
    stem = str(doc.get("stem") or "").strip()
    question_text = f"{scenario_context} {stem}".strip() if scenario_context else stem
    return {
        "question_text": question_text,
        "question": question_text,
        "question_type": doc.get("question_type"),
        "options": doc.get("options") or [],
        "answer_key": doc.get("answer_key") or {},
        "helper": doc.get("helper") or "",
    }


def validate_scenario(doc: ScenarioDocument) -> list[str]:
    """Validate a single scenario document. Returns a list of error strings.

    Empty list means the document passes every rule in
    ``data-model.md`` and would also pass the live
    ``build_stage_validation_flags`` check.
    """
    errors: list[str] = []

    if not isinstance(doc, dict):
        return [f"scenario document must be a dict, got {type(doc).__name__}"]

    # Presence and basic typing of required fields.
    for field in _REQUIRED_FIELDS:
        if field not in doc:
            errors.append(f"missing required field: {field}")

    doc_id = doc.get("doc_id")
    if _is_non_empty_str(doc_id) and not _DOC_ID_PATTERN.match(doc_id):
        errors.append(
            f"doc_id {doc_id!r} does not match expected pattern "
            "<role>.<subskill>.s[12].<question_type>.<slug>"
        )

    review_status = doc.get("review_status")
    if review_status not in _ALLOWED_REVIEW_STATUSES:
        errors.append(
            f"review_status must be one of {sorted(_ALLOWED_REVIEW_STATUSES)}, "
            f"got {review_status!r}"
        )

    question_type = doc.get("question_type")
    if question_type not in _ALLOWED_QUESTION_TYPES:
        errors.append(
            f"question_type must be one of {sorted(_ALLOWED_QUESTION_TYPES)}, "
            f"got {question_type!r}"
        )

    stage = doc.get("stage")
    if stage not in (1, 2):
        errors.append(f"stage must be 1 or 2, got {stage!r}")

    difficulty = doc.get("difficulty")
    if not isinstance(difficulty, int) or not 1 <= difficulty <= 5:
        errors.append(f"difficulty must be an int in [1, 5], got {difficulty!r}")

    estimated_seconds = doc.get("estimated_seconds")
    if not isinstance(estimated_seconds, int) or not 30 <= estimated_seconds <= 120:
        errors.append(
            f"estimated_seconds must be an int in [30, 120], got {estimated_seconds!r}"
        )

    created_at = doc.get("created_at")
    if not _is_non_empty_str(created_at) or not _DATE_PATTERN.match(created_at):
        errors.append(f"created_at must be a YYYY-MM-DD string, got {created_at!r}")

    for str_field in (
        "competency",
        "dimension_key",
        "subskill_key",
        "role_key",
        "learning_objective",
        "scenario_context",
        "stem",
        "explanation",
        "correct_answer_rationale",
        "author",
        "license",
        "corpus_version",
    ):
        if not _is_non_empty_str(doc.get(str_field)):
            errors.append(f"{str_field} must be a non-empty string")

    if "helper" in doc and not _is_non_empty_str(doc.get("helper")):
        errors.append("helper, when present, must be a non-empty string")

    # Cross-reference role_key / subskill_key / dimension_key / competency
    # against the curated role graph.
    role_key = doc.get("role_key")
    subskill_key = doc.get("subskill_key")
    if _is_non_empty_str(role_key) and _is_non_empty_str(subskill_key):
        role_graphs = _load_role_graphs()
        if role_key not in role_graphs:
            errors.append(
                f"role_key {role_key!r} not present in ROLE_GRAPHS"
            )
        else:
            role_graph = role_graphs[role_key]
            lookup = _subskill_lookup(role_graph)
            if subskill_key not in lookup:
                errors.append(
                    f"subskill_key {subskill_key!r} not present in role graph for "
                    f"{role_key!r}"
                )
            else:
                subskill = lookup[subskill_key]
                if doc.get("dimension_key") and doc["dimension_key"] != subskill.dimension:
                    errors.append(
                        f"dimension_key {doc['dimension_key']!r} does not match "
                        f"role graph dimension {subskill.dimension!r} for subskill "
                        f"{subskill_key!r}"
                    )
                if doc.get("competency") and doc["competency"] != subskill.label:
                    errors.append(
                        f"competency {doc['competency']!r} must equal SubSkill.label "
                        f"{subskill.label!r} for subskill {subskill_key!r}"
                    )

    # Corpus version must match the registry. Imported lazily to avoid a
    # circular import on module load.
    if _is_non_empty_str(doc.get("corpus_version")):
        from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION

        if doc["corpus_version"] != SCENARIO_CORPUS_VERSION:
            errors.append(
                f"corpus_version {doc['corpus_version']!r} does not equal "
                f"SCENARIO_CORPUS_VERSION {SCENARIO_CORPUS_VERSION!r}"
            )

    if question_type in _ALLOWED_QUESTION_TYPES:
        _validate_options_and_rationales(doc, errors)
        _validate_answer_key_shape(doc, errors)

    # Finally delegate to the live question-contract validator.
    live_flags = build_stage_validation_flags(_scenario_as_question(doc))
    for flag in live_flags:
        errors.append(f"live question-contract flag: {flag}")

    return errors


def iter_validation_errors(
    documents: Iterable[ScenarioDocument],
) -> list[tuple[str, list[str]]]:
    """Validate a batch and return ``[(doc_id, errors)]`` for each failing doc."""
    failures: list[tuple[str, list[str]]] = []
    for doc in documents:
        errors = validate_scenario(doc)
        if errors:
            failures.append((str(doc.get("doc_id") or "<unknown>"), errors))
    return failures
