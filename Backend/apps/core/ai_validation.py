"""
Validation helpers for structured AI outputs.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from apps.core.exceptions import AIServiceError


def extract_json_object(raw_text: str) -> dict[str, Any]:
    """Extract a JSON object from a model response."""
    candidate = (raw_text or "").strip()
    if not candidate:
        raise AIServiceError("Model returned an empty response", details={"reason": "empty_response"})

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise AIServiceError(
                "Model response did not contain valid JSON",
                details={"reason": "invalid_json", "raw_text": candidate},
            )
        parsed = json.loads(candidate[start : end + 1])

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
