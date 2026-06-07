from __future__ import annotations

import json
import logging
from typing import Any

from apps.core.gemma_client import GemmaClient

logger = logging.getLogger(__name__)

AMBIGUITY_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["unambiguous", "ambiguous_options", "suggested_disambiguating_context"],
    "properties": {
        "unambiguous": {"type": "boolean"},
        "ambiguous_options": {
            "type": "array",
            "items": {"type": "string"},
        },
        "suggested_disambiguating_context": {"type": "string"},
    },
}


def needs_ambiguity_check(question: dict[str, Any]) -> bool:
    """Cheap heuristic — skip validator when ambiguity is unlikely."""
    if str(question.get("question_type") or "") != "single_choice":
        return False
    answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
    correct_ids = set(answer_key.get("correct_option_ids") or [])
    if len(correct_ids) != 1:
        return True
    options = question.get("options") if isinstance(question.get("options"), list) else []
    if len(options) < 3:
        return False
    rationales = question.get("option_rationales") if isinstance(question.get("option_rationales"), list) else []
    correct_rationales = [
        str(item.get("rationale") or "")
        for item in rationales
        if isinstance(item, dict) and item.get("is_correct")
    ]
    incorrect_rationales = [
        str(item.get("rationale") or "")
        for item in rationales
        if isinstance(item, dict) and not item.get("is_correct")
    ]
    if not correct_rationales or not incorrect_rationales:
        return False
    # Flag when multiple rationales sound equally defensible (short overlap heuristic).
    for incorrect in incorrect_rationales:
        if len(incorrect) > 40 and any(
            word in incorrect.lower()
            for word in ("also", "valid", "reasonable", "depending", "context", "senior")
        ):
            return True
    return False


class AmbiguityValidator:
    """Second-pass validator for MCQ_SINGLE ambiguity."""

    def __init__(self, client: GemmaClient | None = None) -> None:
        self._client = client

    def _get_client(self) -> GemmaClient:
        if self._client is None:
            self._client = GemmaClient(task_type="assessment_quality_review", max_output_tokens=600)
        return self._client

    def run(self, question: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Given this question and its options, is there exactly one correct answer that a "
            "consensus of senior engineers would agree on? If not, identify which options could "
            "both be correct and under what conditions.\n"
            f"Question:\n{json.dumps(question, ensure_ascii=True)}\n"
            "Return JSON: "
            '{"unambiguous": boolean, "ambiguous_options": [], '
            '"suggested_disambiguating_context": string}'
        )
        try:
            response = self._get_client().generate_structured(
                prompt=prompt,
                system="You validate technical interview MCQs for unambiguous correct answers. Return strict JSON only.",
                required_keys=("unambiguous", "ambiguous_options", "suggested_disambiguating_context"),
                response_json_schema=AMBIGUITY_RESPONSE_SCHEMA,
            )
            payload = response.payload or {}
            return {
                "unambiguous": bool(payload.get("unambiguous")),
                "ambiguous_options": list(payload.get("ambiguous_options") or []),
                "suggested_disambiguating_context": str(
                    payload.get("suggested_disambiguating_context") or ""
                ).strip(),
            }
        except Exception as error:
            logger.warning("Ambiguity validation failed, assuming unambiguous: %s", error)
            return {
                "unambiguous": True,
                "ambiguous_options": [],
                "suggested_disambiguating_context": "",
            }

    def apply_disambiguation(
        self,
        question: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        context = str(result.get("suggested_disambiguating_context") or "").strip()
        if not context:
            return question
        scenario = str(question.get("scenario_context") or "").strip()
        if context not in scenario:
            question["scenario_context"] = f"{scenario}\n\n{context}".strip() if scenario else context
        stem = str(question.get("stem") or question.get("question_text") or "").strip()
        question_text = str(question.get("question_text") or stem).strip()
        if scenario and scenario not in question_text:
            question_text = f"{scenario}\n\n{stem}".strip() if stem else scenario
        question["question_text"] = question_text
        question["question"] = question_text
        return question
