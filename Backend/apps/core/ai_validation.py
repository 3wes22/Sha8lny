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
