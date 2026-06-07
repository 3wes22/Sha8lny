from __future__ import annotations

import json
import logging
from typing import Any

from apps.core.gemma_client import GemmaClient

logger = logging.getLogger(__name__)

RUBRIC_RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "question_id",
        "scoring_dimensions",
        "required_concepts",
        "bonus_concepts",
        "auto_fail_if",
    ],
    "properties": {
        "question_id": {"type": "string"},
        "scoring_dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "weight": {"type": "number"},
                    "score_1_descriptor": {"type": "string"},
                    "score_3_descriptor": {"type": "string"},
                    "score_5_descriptor": {"type": "string"},
                },
            },
        },
        "required_concepts": {"type": "array", "items": {"type": "string"}},
        "bonus_concepts": {"type": "array", "items": {"type": "string"}},
        "auto_fail_if": {"type": "array", "items": {"type": "string"}},
    },
}


class RubricChain:
    """Second-pass rubric generation for open-ended questions."""

    template_version = "rubric-v1"

    def __init__(self, client: GemmaClient | None = None) -> None:
        self._client = client

    def _get_client(self) -> GemmaClient:
        if self._client is None:
            self._client = GemmaClient(
                task_type="assessment_quality_review",
                max_output_tokens=1200,
            )
        return self._client

    def run(self, question: dict[str, Any]) -> dict[str, Any]:
        question_id = str(question.get("id") or "")
        prompt = (
            "You are a senior hiring manager at a MENA-region tech company evaluating a "
            "mid-to-senior frontend candidate.\n"
            "Generate a structured scoring rubric for this open-ended interview question.\n"
            f"Question:\n{json.dumps(question, ensure_ascii=True)}\n"
            "Return JSON with: question_id, scoring_dimensions (each with dimension, weight 0-1, "
            "score_1_descriptor, score_3_descriptor, score_5_descriptor — weights must sum to 1.0), "
            "required_concepts, bonus_concepts, auto_fail_if.\n"
            f'Use question_id: "{question_id}".'
        )
        try:
            response = self._get_client().generate_structured(
                prompt=prompt,
                system="Return strict JSON only for interview rubrics.",
                required_keys=(
                    "question_id",
                    "scoring_dimensions",
                    "required_concepts",
                    "bonus_concepts",
                    "auto_fail_if",
                ),
                response_json_schema=RUBRIC_RESPONSE_SCHEMA,
            )
            rubric = normalize_rubric(response.payload or {}, question_id=question_id)
            return rubric
        except Exception as error:
            logger.warning("Rubric generation failed, using fallback rubric: %s", error)
            return fallback_rubric(question)


def normalize_rubric(raw: dict[str, Any], *, question_id: str) -> dict[str, Any]:
    dimensions = []
    for item in raw.get("scoring_dimensions") or []:
        if not isinstance(item, dict):
            continue
        dimensions.append(
            {
                "dimension": str(item.get("dimension") or "").strip(),
                "weight": float(item.get("weight") or 0),
                "score_1_descriptor": str(item.get("score_1_descriptor") or "").strip(),
                "score_3_descriptor": str(item.get("score_3_descriptor") or "").strip(),
                "score_5_descriptor": str(item.get("score_5_descriptor") or "").strip(),
            }
        )
    total_weight = sum(d["weight"] for d in dimensions)
    if dimensions and total_weight > 0 and abs(total_weight - 1.0) > 1e-3:
        for dimension in dimensions:
            dimension["weight"] = round(dimension["weight"] / total_weight, 4)
    elif dimensions and total_weight == 0:
        even = round(1.0 / len(dimensions), 4)
        for dimension in dimensions:
            dimension["weight"] = even

    return {
        "question_id": str(raw.get("question_id") or question_id),
        "scoring_dimensions": dimensions,
        "required_concepts": [
            str(c).strip() for c in (raw.get("required_concepts") or []) if str(c).strip()
        ],
        "bonus_concepts": [
            str(c).strip() for c in (raw.get("bonus_concepts") or []) if str(c).strip()
        ],
        "auto_fail_if": [
            str(c).strip() for c in (raw.get("auto_fail_if") or []) if str(c).strip()
        ],
    }


def fallback_rubric(question: dict[str, Any]) -> dict[str, Any]:
    answer_key = question.get("answer_key") if isinstance(question.get("answer_key"), dict) else {}
    concepts = [
        str(c).strip()
        for c in (answer_key.get("expected_concepts") or [])
        if str(c).strip()
    ] or ["concrete approach", "tradeoffs"]
    return {
        "question_id": str(question.get("id") or ""),
        "scoring_dimensions": [
            {
                "dimension": "Technical depth and relevance",
                "weight": 0.4,
                "score_1_descriptor": "Vague or off-topic answer.",
                "score_3_descriptor": "Covers the main approach with some gaps.",
                "score_5_descriptor": "Deep, specific, and well-structured answer.",
            },
            {
                "dimension": "Tradeoffs and constraints",
                "weight": 0.35,
                "score_1_descriptor": "No tradeoffs mentioned.",
                "score_3_descriptor": "Mentions at least one tradeoff.",
                "score_5_descriptor": "Explicit tradeoffs with reasoning.",
            },
            {
                "dimension": "Communication clarity",
                "weight": 0.25,
                "score_1_descriptor": "Hard to follow.",
                "score_3_descriptor": "Understandable structure.",
                "score_5_descriptor": "Clear, concise expert communication.",
            },
        ],
        "required_concepts": concepts[:3],
        "bonus_concepts": concepts[3:] if len(concepts) > 3 else [],
        "auto_fail_if": list(answer_key.get("forbidden_concepts") or []),
    }
