"""
Validation helpers for structured AI outputs.
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from string import ascii_lowercase
from typing import Any, Iterable

from apps.core.exceptions import AIServiceError


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extract a JSON object from a model response."""
    candidate = (raw_text or "").strip()
    if not candidate:
        raise AIServiceError("Model returned an empty response", details={"reason": "empty_response"})

    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate).strip()

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as error:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise AIServiceError(
                "Model response did not contain valid JSON",
                details={"reason": "invalid_json", "raw_text": candidate[:1000]},
            )
        try:
            parsed = json.loads(candidate[start : end + 1])
        except json.JSONDecodeError as inner_error:
            raise AIServiceError(
                "Model response contained malformed JSON",
                details={
                    "reason": "malformed_json",
                    "raw_text": candidate[:1000],
                    "message": str(inner_error),
                },
            ) from inner_error

    if not isinstance(parsed, dict):
        raise AIServiceError(
            "Model response must be a JSON object",
            details={"reason": "json_object_required", "parsed_type": type(parsed).__name__},
        )

    return parsed


def require_keys(payload: dict[str, Any], required_keys: Iterable[str]) -> dict[str, Any]:
    """Ensure a parsed payload includes the required top-level keys."""
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise AIServiceError(
            "Model response is missing required keys",
            details={"reason": "missing_keys", "missing_keys": missing},
        )
    return payload


# ---------------------------------------------------------------------------
# Value-level validation for assessment evaluation payloads
# ---------------------------------------------------------------------------

def _clamp(value: Any, low: float, high: float, *, default: float) -> float:
    """Coerce *value* to a float within [low, high], or return *default*."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(low, min(high, numeric))


def _ensure_non_empty_strings(items: Any, *, fallback: list[str]) -> list[str]:
    """Return a list of non-empty strings, falling back if the input is bad."""
    if not isinstance(items, list):
        return fallback
    cleaned = [str(item).strip() for item in items if isinstance(item, str) and str(item).strip()]
    return cleaned if len(cleaned) >= 1 else fallback


def _normalize_keyword(value: Any) -> str:
    """Normalize a model enum-like value to lowercase snake_case."""
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def normalize_question_type(raw_type: Any, *, default: str) -> str:
    """Coerce question_type to one of the supported assessment question types."""
    normalized = _normalize_keyword(raw_type)
    aliases = {
        "multiple_choice": "multiple_choice",
        "multiplechoice": "multiple_choice",
        "scale": "scale",
        "text": "text",
        "single_choice": "single_choice",
        "single_select": "single_choice",
        "single_best": "single_choice",
        "multi_select": "multi_select",
        "multiselect": "multi_select",
        "select_all": "multi_select",
        "open_ended": "open_ended",
        "openended": "open_ended",
        "open_end": "open_ended",
        "short_answer": "open_ended",
        "short_response": "open_ended",
        "free_text": "open_ended",
    }
    if normalized in aliases:
        return aliases[normalized]
    return default


def normalize_stage_question_type(
    raw_type: Any,
    *,
    raw_mode: Any,
    raw_options: Any,
    default: str = "single_choice",
) -> str:
    """Normalize staged question types to semantic item formats."""
    normalized = normalize_question_type(raw_type, default="")
    if normalized in {"single_choice", "multi_select", "open_ended"}:
        return normalized
    if normalized == "text":
        return "open_ended"

    mode = _normalize_keyword(raw_mode)
    if mode == "multi_select":
        return "multi_select"
    if not isinstance(raw_options, list) or len(raw_options) == 0:
        return "open_ended"
    return "single_choice"


def stage_question_type_to_ui_type(question_type: str) -> tuple[str, str]:
    """Map semantic staged question types to UI type and interaction mode."""
    mapping = {
        "single_choice": ("multiple_choice", "single_select"),
        "multi_select": ("multiple_choice", "multi_select"),
        "open_ended": ("text", "text"),
    }
    return mapping.get(question_type, ("multiple_choice", "single_select"))


def build_stage_choice_options(subskill_label: str) -> list[dict[str, Any]]:
    """Return the canonical staged multiple-choice options for a subskill label."""
    label = str(subskill_label or "").strip() or "this skill"
    return [
        {
            "value": "low",
            "label": f"I would need guidance to complete {label}",
            "score": 1,
        },
        {
            "value": "mid",
            "label": f"I can handle common {label} work independently",
            "score": 3,
        },
        {
            "value": "high",
            "label": f"I can make tradeoffs, debug edge cases, and lead {label} work",
            "score": 5,
        },
    ]


def normalize_choice_options(
    raw_options: Any,
    *,
    default_options: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Repair a choice-option list by filling missing fields from defaults."""
    if not default_options:
        return []

    options = raw_options if isinstance(raw_options, list) else []

    def _coerce_score(value: Any) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    def _select_option_label(option: dict[str, Any]) -> str:
        raw_label = str(option.get("label") or "").strip()
        raw_value = str(option.get("value") or "").strip()
        if _normalize_keyword(raw_value) in {"low", "mid", "high"}:
            return raw_label or raw_value
        if raw_value and raw_label and raw_value != raw_label:
            if any(token in raw_value for token in ("/", "?", "=", "(", ")", "{", "}", ":", "[")):
                return raw_value
        if raw_value and (not raw_label or len(raw_value) > len(raw_label)):
            return raw_value
        return raw_label or raw_value

    if len(options) == len(default_options) and all(isinstance(option, dict) for option in options):
        raw_option_dicts = [option for option in options if isinstance(option, dict)]
        if raw_option_dicts:
            uses_canonical_values = all(
                _normalize_keyword(option.get("value")) in {"low", "mid", "high"}
                for option in raw_option_dicts
            )
            if not uses_canonical_values:
                ranked_options = []
                for index, option in enumerate(raw_option_dicts):
                    label = _select_option_label(option)
                    if not label:
                        continue
                    score = _coerce_score(option.get("score"))
                    ranked_options.append(
                        {
                            "index": index,
                            "label": label,
                            "score": score,
                        }
                    )

                if len(ranked_options) == len(default_options):
                    if all(item["score"] is not None for item in ranked_options):
                        ranked_options.sort(key=lambda item: (item["score"], item["index"]))
                    normalized: list[dict[str, Any]] = []
                    for ranked_option, default_option in zip(
                        ranked_options,
                        default_options,
                        strict=False,
                    ):
                        default_score = int(
                            _clamp(default_option.get("score"), 1, 5, default=3)
                        )
                        score = ranked_option["score"]
                        normalized.append(
                            {
                                "value": str(default_option.get("value") or "").strip(),
                                "label": ranked_option["label"],
                                "score": (
                                    default_score
                                    if score is None
                                    else int(_clamp(score, 1, 5, default=default_score))
                                ),
                            }
                        )
                    return normalized

    options_by_value: dict[str, dict[str, Any]] = {}
    for option in options:
        if not isinstance(option, dict):
            continue
        value = _normalize_keyword(option.get("value"))
        if value and value not in options_by_value:
            options_by_value[value] = option

    normalized: list[dict[str, Any]] = []
    for index, default_option in enumerate(default_options):
        default_value = _normalize_keyword(default_option.get("value"))
        if not default_value:
            continue

        raw_option = options_by_value.get(default_value)
        if raw_option is None and index < len(options) and isinstance(options[index], dict):
            raw_option = options[index]

        default_score = int(_clamp(default_option.get("score"), 1, 5, default=3))
        score = int(_clamp((raw_option or {}).get("score"), 1, 5, default=default_score))
        label = str((raw_option or {}).get("label") or default_option.get("label") or "").strip()

        normalized.append(
            {
                "value": default_value,
                "label": label or default_value,
                "score": score,
            }
        )

    return normalized


def _default_option_id(index: int) -> str:
    if 0 <= index < len(ascii_lowercase):
        return ascii_lowercase[index]
    return f"opt_{index + 1}"


def normalize_stage_options(
    raw_options: Any,
    *,
    question_type: str,
    default_options: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize staged assessment options into stable ids and labels."""
    if question_type == "open_ended":
        return []

    if not isinstance(raw_options, list) or not raw_options:
        raw_options = default_options

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, option in enumerate(raw_options):
        if isinstance(option, str):
            label = option.strip()
            raw_id = ""
            raw_value = ""
            raw_score = None
        elif isinstance(option, dict):
            raw_label = str(option.get("label") or "").strip()
            raw_id = str(option.get("id") or "").strip()
            raw_value = str(option.get("value") or "").strip()
            raw_score = option.get("score")
            label = raw_label or raw_value
            if (
                raw_label
                and raw_value
                and raw_label != raw_value
                and any(token in raw_value for token in ("/", "?", "=", "(", ")", "{", "}", ":", "["))
            ):
                label = raw_value
            if not raw_label and raw_value and default_options:
                default_match = next(
                    (
                        default_option
                        for default_option in default_options
                        if str(default_option.get("value") or "").strip() == raw_value
                    ),
                    None,
                )
                if default_match:
                    label = str(default_match.get("label") or raw_value).strip()
                    if raw_score is None:
                        raw_score = default_match.get("score")
        else:
            continue

        if not label:
            continue

        option_id = _normalize_keyword(raw_id or raw_value)
        if not raw_id and raw_value and any(
            token in raw_value for token in ("/", "?", "=", "(", ")", "{", "}", ":", "[", "]")
        ):
            option_id = ""
        if not option_id:
            option_id = _default_option_id(index)
        if option_id in seen_ids:
            option_id = f"{option_id}_{index + 1}"

        normalized_option = {
            "id": option_id,
            "value": option_id,
            "label": label,
        }
        try:
            if raw_score is not None:
                normalized_option["score"] = int(float(raw_score))
        except (TypeError, ValueError):
            pass

        normalized.append(normalized_option)
        seen_ids.add(option_id)

    if normalized:
        return normalized

    if default_options:
        return normalize_stage_options(
            default_options,
            question_type=question_type,
            default_options=[],
        )
    return []


def _normalize_option_selections(
    raw_selection: Any,
    *,
    options: list[dict[str, Any]],
) -> list[str]:
    """Resolve answer-key option ids against normalized option metadata."""
    option_lookup: dict[str, str] = {}
    for option in options:
        option_id = str(option.get("id") or option.get("value") or "").strip()
        if not option_id:
            continue
        option_lookup[_normalize_keyword(option_id)] = option_id
        option_lookup[_normalize_keyword(option.get("value"))] = option_id
        option_lookup[_normalize_keyword(option.get("label"))] = option_id

    if isinstance(raw_selection, list):
        candidates = raw_selection
    elif raw_selection in (None, ""):
        candidates = []
    else:
        candidates = [raw_selection]

    resolved: list[str] = []
    for candidate in candidates:
        key = _normalize_keyword(candidate)
        option_id = option_lookup.get(key)
        if option_id and option_id not in resolved:
            resolved.append(option_id)
    return resolved


def normalize_stage_answer_key(
    raw_question: dict[str, Any],
    *,
    question_type: str,
    options: list[dict[str, Any]],
) -> dict[str, Any]:
    """Normalize answer-key metadata for staged assessment items."""
    raw_answer_key = (
        raw_question.get("answer_key")
        if isinstance(raw_question.get("answer_key"), dict)
        else {}
    )

    if question_type == "open_ended":
        expected_concepts = _ensure_non_empty_strings(
            raw_answer_key.get("expected_concepts") or raw_question.get("expected_concepts"),
            fallback=[],
        )
        forbidden_concepts = _ensure_non_empty_strings(
            raw_answer_key.get("forbidden_concepts"),
            fallback=[],
        )
        required_count = int(
            _clamp(
                raw_answer_key.get("required_concept_count"),
                1,
                max(1, len(expected_concepts) or 1),
                default=min(len(expected_concepts), 2) if expected_concepts else 1,
            )
        )
        return {
            "expected_concepts": expected_concepts,
            "required_concept_count": required_count,
            "forbidden_concepts": forbidden_concepts,
            "scoring": str(raw_answer_key.get("scoring") or "concept_coverage"),
        }

    correct_ids = _normalize_option_selections(
        raw_answer_key.get("correct_option_ids")
        or raw_answer_key.get("correct_answers")
        or raw_question.get("correct_answer"),
        options=options,
    )
    if not correct_ids and options:
        scored_options = []
        for option in options:
            try:
                scored_options.append((int(float(option.get("score"))), option["id"]))
            except (TypeError, ValueError, KeyError):
                continue
        if scored_options:
            scored_options.sort(key=lambda item: item[0], reverse=True)
            if question_type == "multi_select":
                high_score = scored_options[0][0]
                correct_ids = [
                    option_id
                    for score, option_id in scored_options
                    if score >= max(4, high_score - 1)
                ]
            else:
                correct_ids = [scored_options[0][1]]

    if question_type == "single_choice" and correct_ids:
        correct_ids = correct_ids[:1]

    return {
        "correct_option_ids": correct_ids,
        "scoring": str(
            raw_answer_key.get("scoring")
            or ("partial_credit" if question_type == "multi_select" else "single_best")
        ),
    }


def normalize_stage_option_rationales(
    raw_option_rationales: Any,
    *,
    options: list[dict[str, Any]],
    answer_key: dict[str, Any],
) -> list[dict[str, Any]]:
    """Normalize per-option rationale metadata while preserving option order."""
    option_lookup: dict[str, str] = {}
    option_order: dict[str, int] = {}
    for index, option in enumerate(options):
        option_id = str(option.get("id") or option.get("value") or "").strip()
        if not option_id:
            continue
        option_lookup[_normalize_keyword(option_id)] = option_id
        option_lookup[_normalize_keyword(option.get("value"))] = option_id
        option_lookup[_normalize_keyword(option.get("label"))] = option_id
        option_order[option_id] = index

    if isinstance(raw_option_rationales, dict):
        entries = [
            {
                "option_id": key,
                "rationale": value,
            }
            for key, value in raw_option_rationales.items()
        ]
    elif isinstance(raw_option_rationales, list):
        entries = raw_option_rationales
    else:
        entries = []

    correct_ids = set(answer_key.get("correct_option_ids") or [])
    normalized: list[dict[str, Any]] = []
    seen_option_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw_option_id = (
            entry.get("option_id")
            or entry.get("id")
            or entry.get("value")
            or entry.get("label")
        )
        option_id = option_lookup.get(_normalize_keyword(raw_option_id))
        rationale = str(
            entry.get("rationale")
            or entry.get("why_wrong")
            or entry.get("why")
            or ""
        ).strip()
        if not option_id or not rationale or option_id in seen_option_ids:
            continue
        normalized.append(
            {
                "option_id": option_id,
                "is_correct": (
                    bool(entry.get("is_correct"))
                    if "is_correct" in entry
                    else option_id in correct_ids
                ),
                "rationale": rationale,
            }
        )
        seen_option_ids.add(option_id)

    normalized.sort(key=lambda item: option_order.get(item["option_id"], 999))
    return normalized


def build_stage_question_text(*, scenario_context: str, stem: str) -> str:
    """Combine scenario context and stem without duplicating text."""
    context = str(scenario_context or "").strip()
    narrowed_stem = str(stem or "").strip()
    if not context:
        return narrowed_stem
    if not narrowed_stem:
        return context

    normalized_context = re.sub(r"\s+", " ", context).strip().lower()
    normalized_stem = re.sub(r"\s+", " ", narrowed_stem).strip().lower()
    if normalized_context in normalized_stem:
        return narrowed_stem
    if normalized_stem in normalized_context:
        return context
    return f"{context} {narrowed_stem}".strip()


_CLOSED_STEM_OPEN_PATTERNS = (
    "how would you",
    "describe",
    "outline",
    "explain",
    "translate",
    "justify",
    "what are the trade",
)

_CLOSED_STEM_NARROW_PATTERNS = (
    "which ",
    "what is the best",
    "what is the most",
    "which primary",
    "which option",
    "select all that apply",
)

_GENERIC_JUDGMENT_PATTERNS = (
    "strongest engineering choice",
    "strong engineering judgment",
    "preserves correctness, clarity, and maintainability",
    "increases evidence and reduces risk",
)

_WEAK_DISTRACTOR_PATTERNS = (
    "disable logging",
    "change an unrelated part",
    "increase deployment complexity",
    "skip reproduction",
    "rely on intuition only",
    "restart the failing path without isolating",
    "restart every service and wait",
)


def _closed_stem_is_too_open(question_text: str) -> bool:
    text = str(question_text or "").strip().lower()
    if not text:
        return True
    if any(pattern in text for pattern in _CLOSED_STEM_NARROW_PATTERNS):
        return False
    return any(pattern in text for pattern in _CLOSED_STEM_OPEN_PATTERNS)


def _options_not_parallel(options: list[dict[str, Any]]) -> bool:
    labels = [str(option.get("label") or "").strip() for option in options if str(option.get("label") or "").strip()]
    if len(labels) < 2:
        return False

    token_counts = [len(re.findall(r"\w+", label)) for label in labels]
    if max(token_counts) >= 2 * max(1, min(token_counts)) and (max(token_counts) - min(token_counts)) >= 6:
        return True

    sentence_like = [count >= 7 or label.endswith(".") for count, label in zip(token_counts, labels, strict=False)]
    return any(sentence_like) and not all(sentence_like)


def _looks_like_capability_scale_options(options: list[dict[str, Any]]) -> bool:
    labels = [str(option.get("label") or "").strip().lower() for option in options if str(option.get("label") or "").strip()]
    if not labels:
        return False

    if set(labels) == {"low", "mid", "high"}:
        return True

    markers = (
        "would need guidance",
        "can handle common",
        "make tradeoffs",
        "without help today",
    )
    return sum(1 for label in labels if any(marker in label for marker in markers)) >= 2


def _looks_like_generic_self_assessment(question_text: str, helper: str) -> bool:
    combined = f"{question_text} {helper}".strip().lower()
    if not combined:
        return False

    patterns = (
        "best matches how you would handle",
        "best matches your next step",
        "closest to what you can do without help today",
    )
    return any(pattern in combined for pattern in patterns)


def _looks_like_generic_engineering_judgment(
    question_text: str,
    helper: str,
    options: list[dict[str, Any]],
) -> bool:
    combined = " ".join(
        [
            str(question_text or "").strip().lower(),
            str(helper or "").strip().lower(),
            " ".join(
                str(option.get("label") or "").strip().lower()
                for option in options
                if str(option.get("label") or "").strip()
            ),
        ]
    )
    return any(pattern in combined for pattern in _GENERIC_JUDGMENT_PATTERNS)


def detect_weak_distractors(question: dict[str, Any]) -> list[str]:
    labels = [
        str(option.get("label") or "").strip().lower()
        for option in (
            question.get("options")
            if isinstance(question.get("options"), list)
            else []
        )
    ]
    if any(pattern in label for label in labels for pattern in _WEAK_DISTRACTOR_PATTERNS):
        return ["weak_distractor_detected"]
    return []


def _similarity_tokens(text: str) -> set[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "at",
        "be",
        "for",
        "from",
        "how",
        "in",
        "into",
        "is",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "what",
        "which",
        "with",
        "would",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if token not in stop_words
    }


def detect_duplicate_questions(questions: list[dict[str, Any]]) -> dict[int, list[str]]:
    flags: dict[int, list[str]] = {}
    token_sets = [
        _similarity_tokens(
            question.get("question_text") or question.get("question") or ""
        )
        for question in questions
    ]
    normalized_texts = [
        re.sub(
            r"[^a-z0-9 ]+",
            " ",
            str(question.get("question_text") or question.get("question") or "").lower(),
        )
        for question in questions
    ]

    for first_index in range(len(questions)):
        if not token_sets[first_index]:
            continue
        for second_index in range(first_index + 1, len(questions)):
            if not token_sets[second_index]:
                continue
            overlap = token_sets[first_index] & token_sets[second_index]
            union = token_sets[first_index] | token_sets[second_index]
            similarity = len(overlap) / len(union) if union else 0.0
            sequence_similarity = SequenceMatcher(
                None,
                normalized_texts[first_index],
                normalized_texts[second_index],
            ).ratio()
            if similarity >= 0.6 or sequence_similarity >= 0.75:
                flags.setdefault(second_index, []).append("duplicate_question_stem")
    return flags


def detect_repeated_option_patterns(questions: list[dict[str, Any]]) -> dict[int, list[str]]:
    flags: dict[int, list[str]] = {}
    label_sets: list[set[str]] = []
    for question in questions:
        label_sets.append(
            {
                re.sub(r"\s+", " ", str(option.get("label") or "").strip().lower())
                for option in (
                    question.get("options")
                    if isinstance(question.get("options"), list)
                    else []
                )
                if str(option.get("label") or "").strip()
            }
        )

    for first_index in range(len(questions)):
        if len(label_sets[first_index]) < 3:
            continue
        for second_index in range(first_index + 1, len(questions)):
            if len(label_sets[second_index]) < 3:
                continue
            overlap = label_sets[first_index] & label_sets[second_index]
            union = label_sets[first_index] | label_sets[second_index]
            similarity = len(overlap) / len(union) if union else 0.0
            if similarity >= 0.8:
                flags.setdefault(second_index, []).append("repeated_option_pattern")
    return flags


def build_batch_stage_validation_flags(
    questions: list[dict[str, Any]],
) -> dict[int, list[str]]:
    flags: dict[int, list[str]] = {}
    for detector in (detect_duplicate_questions, detect_repeated_option_patterns):
        detected = detector(questions)
        for index, question_flags in detected.items():
            if not question_flags:
                continue
            flags.setdefault(index, []).extend(question_flags)
    return {
        index: sorted(set(question_flags))
        for index, question_flags in flags.items()
    }


def build_stage_validation_flags(question: dict[str, Any]) -> list[str]:
    """Return deterministic contract flags for a staged assessment item."""
    question_type = str(question.get("question_type") or "").strip()
    question_text = str(question.get("question_text") or question.get("question") or "").strip()
    options = question.get("options") if isinstance(question.get("options"), list) else []
    answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
    helper = str(question.get("helper") or "").strip()
    flags: list[str] = []

    if question_type in {"single_choice", "multi_select"} and _closed_stem_is_too_open(question_text):
        flags.append("closed_question_stem_too_open")
    if question_type in {"single_choice", "multi_select"} and _looks_like_generic_self_assessment(question_text, helper):
        flags.append("generic_self_assessment_stem")
    if question_type in {"single_choice", "multi_select"} and _looks_like_generic_engineering_judgment(question_text, helper, options):
        flags.append("generic_engineering_judgment_stem")
    if question_type in {"single_choice", "multi_select"} and _looks_like_capability_scale_options(options):
        flags.append("capability_scale_options_not_allowed")
    flags.extend(detect_weak_distractors(question))

    if question_type == "single_choice":
        if len(options) < 3 or len(options) > 5:
            flags.append("single_choice_option_count_out_of_range")
        if len(answer_key.get("correct_option_ids") or []) != 1:
            flags.append("single_choice_requires_exactly_one_correct_option")
        if _options_not_parallel(options):
            flags.append("options_not_parallel")

    elif question_type == "multi_select":
        if "select all that apply" not in question_text.lower():
            flags.append("multi_select_missing_select_all_instruction")
        correct_ids = answer_key.get("correct_option_ids") or []
        if len(options) < 4 or len(options) > 6:
            flags.append("multi_select_option_count_out_of_range")
        if len(correct_ids) < 2:
            flags.append("multi_select_requires_two_or_more_correct_options")
        if len(correct_ids) > 3:
            flags.append("multi_select_too_many_correct_options")
        if len(correct_ids) >= len(options):
            flags.append("multi_select_requires_two_or_more_correct_options")
        if _options_not_parallel(options):
            flags.append("options_not_parallel")

    elif question_type == "open_ended":
        if options:
            flags.append("open_ended_should_not_have_options")
        if not (answer_key.get("expected_concepts") or []):
            flags.append("open_ended_missing_expected_concepts")
    else:
        flags.append("unsupported_question_type")

    valid_option_ids = {str(option.get("id") or option.get("value") or "").strip() for option in options}
    invalid_ids = [
        option_id
        for option_id in (answer_key.get("correct_option_ids") or [])
        if option_id not in valid_option_ids
    ]
    if invalid_ids:
        flags.append("answer_key_references_unknown_option")

    return sorted(set(flags))


def normalize_interaction_mode(
    raw_mode: Any,
    *,
    question_type: str,
    default_mode: str,
) -> str:
    """Coerce interaction_mode to one of the supported modes for the question type."""
    allowed_modes = {
        "multiple_choice": {"single_select", "multi_select", "visual_choice"},
        "scale": {"scale"},
        "text": {"text"},
    }
    mode = _normalize_keyword(raw_mode)
    if mode in allowed_modes.get(question_type, set()):
        return mode
    return default_mode


def _sanitize_skill_scores(raw: Any) -> dict[str, float]:
    """Validate and clamp the skill_scores dict from the model."""
    valid_dimensions = {
        "technical_depth", "tooling", "problem_solving",
        "experience", "goals", "commitment",
    }
    if not isinstance(raw, dict):
        return {dim: 50.0 for dim in valid_dimensions}

    result: dict[str, float] = {}
    for dim in valid_dimensions:
        result[dim] = _clamp(raw.get(dim), 0, 100, default=50.0)
    return result


def _sanitize_recommended_careers(raw: Any) -> list[dict[str, Any]]:
    """Validate the recommended_careers array."""
    if not isinstance(raw, list):
        return []
    cleaned: list[dict[str, Any]] = []
    for item in raw[:5]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        cleaned.append({
            "title": title,
            "match_score": int(_clamp(item.get("match_score"), 0, 100, default=70)),
            "reasoning": str(item.get("reasoning") or "").strip(),
        })
    return cleaned


def _sanitize_learning_paths(raw: Any) -> list[dict[str, Any]]:
    """Validate the recommended_learning_paths array."""
    if not isinstance(raw, list):
        return []
    cleaned: list[dict[str, Any]] = []
    for item in raw[:5]:
        if not isinstance(item, dict):
            continue
        skill = str(item.get("skill") or "").strip()
        if not skill:
            continue
        priority = str(item.get("priority") or "medium").strip().lower()
        if priority not in {"high", "medium", "low"}:
            priority = "medium"
        cleaned.append({
            "skill": skill,
            "priority": priority,
            "resources": item.get("resources") if isinstance(item.get("resources"), list) else [],
        })
    return cleaned


def sanitize_evaluation_payload(
    payload: dict[str, Any],
    *,
    fallback_strengths: list[str] | None = None,
    fallback_gaps: list[str] | None = None,
) -> dict[str, Any]:
    """Sanitize and clamp a raw LLM evaluation payload so no insane values leak into the database.

    This function does NOT reject the payload — it repairs it in place. If any
    field is out of range or the wrong type, it is replaced with a safe default.
    """
    _default_strengths = fallback_strengths or ["Commitment to learning", "Goal clarity"]
    _default_gaps = fallback_gaps or ["Advanced specialization", "Production-scale project experience"]

    return {
        "overall_score": _clamp(payload.get("overall_score"), 0, 100, default=50.0),
        "skill_scores": _sanitize_skill_scores(payload.get("skill_scores")),
        "strengths": _ensure_non_empty_strings(
            payload.get("strengths"), fallback=_default_strengths,
        ),
        "areas_for_improvement": _ensure_non_empty_strings(
            payload.get("areas_for_improvement"), fallback=_default_gaps,
        ),
        "recommended_careers": _sanitize_recommended_careers(
            payload.get("recommended_careers"),
        ),
        "recommended_learning_paths": _sanitize_learning_paths(
            payload.get("recommended_learning_paths"),
        ),
        "ai_insights": str(payload.get("ai_insights") or "").strip() or "Assessment completed.",
        "ai_confidence_score": _clamp(
            payload.get("ai_confidence_score"), 50, 95, default=75.0,
        ),
    }


def sanitize_stage_question_payload(
    raw_questions: Any,
    *,
    stage: int,
    allowed_targets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Validate and normalize stage-question payloads from the model."""
    if not isinstance(raw_questions, list):
        raise AIServiceError(
            "Stage question payload must be a list",
            details={"reason": "invalid_stage_questions"},
        )

    if not allowed_targets:
        raise AIServiceError(
            "Stage question payload has no allowed targets",
            details={"reason": "missing_allowed_targets"},
        )

    ordered_target_keys = list(allowed_targets)
    normalized: list[dict[str, Any]] = []
    seen_subskills: set[str] = set()

    def _target_defaults(subskill_key: str) -> dict[str, Any]:
        target = allowed_targets[subskill_key]
        question_type = normalize_stage_question_type(
            target.get("question_type"),
            raw_mode=target.get("interaction_mode"),
            raw_options=target.get("options"),
            default="single_choice",
        )
        ui_type, default_mode = stage_question_type_to_ui_type(question_type)
        interaction_mode = normalize_interaction_mode(
            target.get("interaction_mode"),
            question_type=ui_type,
            default_mode=default_mode,
        )
        return {
            "dimension_key": target["dimension_key"],
            "category": target["category"],
            "question_type": question_type,
            "type": ui_type,
            "interaction_mode": interaction_mode,
            "options": target.get("options") if isinstance(target.get("options"), list) else [],
            "difficulty": int(_clamp(target.get("difficulty"), 1, 5, default=3)),
            "estimated_seconds": int(
                _clamp(target.get("estimated_seconds"), 15, 180, default=45)
            ),
            "helper": str(target.get("helper") or ""),
            "learning_objective": str(target.get("learning_objective") or "").strip(),
            "fallback_question_text": str(target.get("fallback_question_text") or "").strip(),
            "fallback_scenario_context": str(target.get("fallback_scenario_context") or "").strip(),
            "fallback_answer_key": (
                target.get("fallback_answer_key")
                if isinstance(target.get("fallback_answer_key"), dict)
                else {}
            ),
            "fallback_explanation": str(target.get("fallback_explanation") or "").strip(),
            "fallback_correct_answer_rationale": str(
                target.get("fallback_correct_answer_rationale") or ""
            ).strip(),
            "fallback_option_rationales": (
                target.get("fallback_option_rationales")
                if isinstance(target.get("fallback_option_rationales"), list)
                else []
            ),
        }

    def _next_available_target() -> str:
        for target_key in ordered_target_keys:
            if target_key not in seen_subskills:
                return target_key
        return ""

    for index, raw_question in enumerate(raw_questions):
        if not isinstance(raw_question, dict):
            continue

        extra_validation_flags: list[str] = []
        subskill_key = str(raw_question.get("subskill_key") or "").strip()
        if subskill_key not in allowed_targets or subskill_key in seen_subskills:
            extra_validation_flags.append("subskill_key_missing_or_invalid")
            subskill_key = _next_available_target()
        if not subskill_key:
            continue

        defaults = _target_defaults(subskill_key)

        question_type = normalize_stage_question_type(
            raw_question.get("question_type")
            or raw_question.get("type")
            or defaults["question_type"],
            raw_mode=raw_question.get("interaction_mode"),
            raw_options=raw_question.get("options"),
            default=defaults["question_type"],
        )
        if question_type != defaults["question_type"]:
            extra_validation_flags.append("question_type_mismatch_with_blueprint")
        ui_type, default_mode = stage_question_type_to_ui_type(question_type)

        interaction_mode = normalize_interaction_mode(
            raw_question.get("interaction_mode"),
            question_type=ui_type,
            default_mode=default_mode,
        )

        scenario_context = str(raw_question.get("scenario_context") or "").strip()
        stem = str(
            raw_question.get("stem")
            or raw_question.get("question_text")
            or raw_question.get("question")
            or ""
        ).strip()
        if not stem and not scenario_context:
            extra_validation_flags.append("default_stem_used")
            stem = defaults["fallback_question_text"]
            scenario_context = defaults["fallback_scenario_context"]
        question_text = build_stage_question_text(
            scenario_context=scenario_context,
            stem=stem,
        )
        if not question_text:
            continue

        options = normalize_stage_options(
            raw_question.get("options"),
            question_type=question_type,
            default_options=defaults["options"],
        )
        if question_type != "open_ended" and not isinstance(raw_question.get("options"), list):
            extra_validation_flags.append("options_missing_from_model")
        difficulty = int(
            _clamp(
                raw_question.get("difficulty"),
                1,
                5,
                default=defaults["difficulty"],
            )
        )
        estimated_seconds = int(
            _clamp(
                raw_question.get("estimated_seconds"),
                15,
                180,
                default=defaults["estimated_seconds"],
            )
        )
        answer_key = normalize_stage_answer_key(
            raw_question,
            question_type=question_type,
            options=options,
        )
        if not isinstance(raw_question.get("answer_key"), dict):
            extra_validation_flags.append("answer_key_missing_from_model")
        competency = str(raw_question.get("competency") or defaults["category"]).strip() or defaults["category"]
        learning_objective = (
            str(raw_question.get("learning_objective") or defaults["learning_objective"]).strip()
            or defaults["learning_objective"]
        )
        explanation = str(raw_question.get("explanation") or "").strip()
        correct_answer_rationale = str(
            raw_question.get("correct_answer_rationale") or explanation
        ).strip()
        option_rationales = normalize_stage_option_rationales(
            raw_question.get("option_rationales") or raw_question.get("distractor_rationale"),
            options=options,
            answer_key=answer_key,
        )
        # helper is type-scoped by QuestionTypeRouter after sanitize — do not bleed from defaults.
        helper = str(raw_question.get("helper") or "").strip()

        normalized_question = {
            "id": str(raw_question.get("id") or f"s{stage}_q{index + 1}"),
            "stage": stage,
            "subskill_key": subskill_key,
            "dimension_key": defaults["dimension_key"],
            "scenario_context": scenario_context,
            "question_text": question_text,
            "question": question_text,
            "question_type": question_type,
            "type": ui_type,
            "interaction_mode": interaction_mode,
            "options": options,
            "difficulty": difficulty,
            "estimated_seconds": estimated_seconds,
            "category": defaults["category"],
            "competency": competency,
            "learning_objective": learning_objective,
            "answer_key": answer_key,
            "explanation": explanation,
            "correct_answer_rationale": correct_answer_rationale,
            "option_rationales": option_rationales,
            "validation_flags": [],
            "helper": helper,
        }
        normalized_question["validation_flags"] = sorted(
            set(build_stage_validation_flags(normalized_question) + extra_validation_flags)
        )

        normalized.append(normalized_question)
        seen_subskills.add(subskill_key)

    for index, subskill_key in enumerate(ordered_target_keys, start=len(normalized) + 1):
        if subskill_key in seen_subskills:
            continue
        defaults = _target_defaults(subskill_key)
        question_text = build_stage_question_text(
            scenario_context=defaults["fallback_scenario_context"],
            stem=defaults["fallback_question_text"],
        )
        if not question_text:
            continue
        fallback_question = {
            "id": f"s{stage}_q{index}",
            "stage": stage,
            "subskill_key": subskill_key,
            "dimension_key": defaults["dimension_key"],
            "scenario_context": defaults["fallback_scenario_context"],
            "question_text": question_text,
            "question": question_text,
            "question_type": defaults["question_type"],
            "type": defaults["type"],
            "interaction_mode": defaults["interaction_mode"],
            "options": normalize_stage_options(
                defaults["options"],
                question_type=defaults["question_type"],
                default_options=[],
            ),
            "difficulty": defaults["difficulty"],
            "estimated_seconds": defaults["estimated_seconds"],
            "category": defaults["category"],
            "competency": defaults["category"],
            "learning_objective": defaults["learning_objective"],
            "answer_key": defaults["fallback_answer_key"],
            "explanation": defaults["fallback_explanation"],
            "correct_answer_rationale": defaults["fallback_correct_answer_rationale"],
            "option_rationales": defaults["fallback_option_rationales"],
            "validation_flags": [],
            "helper": defaults["helper"],
        }
        fallback_question["validation_flags"] = sorted(
            set(build_stage_validation_flags(fallback_question) + ["fallback_slot_filled"])
        )
        normalized.append(fallback_question)
        seen_subskills.add(subskill_key)

    if not normalized:
        raise AIServiceError(
            "Stage question payload did not include any usable questions",
            details={"reason": "empty_stage_questions"},
        )

    if len(normalized) != len(allowed_targets):
        raise AIServiceError(
            "Stage question payload did not cover all required targets",
            details={
                "reason": "incomplete_stage_questions",
                "expected_targets": list(allowed_targets),
                "returned_targets": [item["subskill_key"] for item in normalized],
            },
        )

    batch_validation_flags = build_batch_stage_validation_flags(normalized)
    for index, question in enumerate(normalized):
        question["validation_flags"] = sorted(
            set(question.get("validation_flags") or [])
            | set(batch_validation_flags.get(index, []))
        )

    return normalized
