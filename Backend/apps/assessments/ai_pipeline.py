"""
Assessment-specific AI prompts and deterministic fallbacks.
"""

from __future__ import annotations

import copy
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from apps.assessments.models import Assessment
from apps.assessments.services import BaselineAssessmentAnalyzer
from apps.core.ai_contracts import AssessmentAnalysisInput, AssessmentAnalysisResult
from apps.core.ai_logging import build_ai_metadata
from apps.core.gemma_client import GemmaClient, GemmaResponse


DEFAULT_QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "multiple_choice",
        "interaction_mode": "visual_choice",
        "question": "How familiar are you with programming fundamentals (variables, loops, functions)?",
        "category": "Fundamentals",
        "estimated_seconds": 45,
        "options": [
            {"value": "none", "label": "I've never written code before", "score": 1},
            {"value": "basic", "label": "I've done some tutorials / small scripts", "score": 2},
            {"value": "comfortable", "label": "I can build small apps/projects", "score": 4},
            {"value": "advanced", "label": "I'm very comfortable and help others learn", "score": 5},
        ],
    },
    {
        "id": 2,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "Rate your confidence in problem-solving and debugging.",
        "category": "Problem Solving",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "Very low", "5": "Very high"},
    },
    {
        "id": 3,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "Rate your familiarity with web technologies (HTML, CSS, JavaScript).",
        "category": "Web Development",
        "estimated_seconds": 35,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "Not familiar", "5": "Expert"},
    },
    {
        "id": 4,
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "question": "Which best describes your current experience level?",
        "category": "Experience",
        "estimated_seconds": 35,
        "options": [
            {"value": "student", "label": "Student / completely new", "score": 1},
            {"value": "junior", "label": "Junior / < 2 years experience", "score": 3},
            {"value": "mid", "label": "Mid-level / 2-5 years", "score": 4},
            {"value": "senior", "label": "Senior / 5+ years", "score": 5},
        ],
    },
    {
        "id": 5,
        "type": "text",
        "interaction_mode": "text",
        "question": "What is your main goal with this career path?",
        "category": "Goals",
        "estimated_seconds": 60,
        "helper": "For example: get a first job, switch from another field, grow to senior, freelancing, etc.",
    },
    {
        "id": 6,
        "type": "scale",
        "interaction_mode": "scale",
        "question": "How much time per week can you realistically dedicate to learning?",
        "category": "Commitment",
        "estimated_seconds": 30,
        "min_value": 1,
        "max_value": 5,
        "labels": {"1": "<3 hours", "5": "15+ hours"},
    },
]


QUESTION_SYSTEM_PROMPT = """You generate professional career assessment questions for a career-development platform.
Return strict JSON with a top-level "questions" array.
Each question must include:
- id (integer)
- type
- interaction_mode
- question
- category
- estimated_seconds

Allowed interaction_mode values: visual_choice, single_select, scale, text.
Return 6 concise questions total.
"""


EVALUATION_SYSTEM_PROMPT = """You evaluate assessment responses for a career-development platform.
Return strict JSON with:
- overall_score
- skill_scores
- strengths
- areas_for_improvement
- recommended_careers
- recommended_learning_paths
- ai_insights
- ai_confidence_score

Keep recommendations grounded and concise.
"""


def get_default_questions(_: str = "skills") -> List[Dict[str, Any]]:
    """Return the deterministic fallback question set."""
    return copy.deepcopy(DEFAULT_QUESTIONS)


def _normalize_questions(raw_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, raw_question in enumerate(raw_questions[:6], start=1):
        question = dict(raw_question)
        question["id"] = int(question.get("id") or index)
        question["type"] = question.get("type") or "text"
        question["interaction_mode"] = question.get("interaction_mode") or question["type"]
        question["question"] = str(question.get("question") or "").strip()
        question["category"] = str(question.get("category") or "General").strip()
        question["estimated_seconds"] = int(question.get("estimated_seconds") or 45)
        if question["question"]:
            normalized.append(question)

    return normalized


class AssessmentAIService:
    """AI-backed assessment generation and evaluation with deterministic fallback."""

    QUESTION_FALLBACK_VERSION = "assessment-questions-fallback-v1"
    EVALUATION_VERSION = "assessment-eval-gemma-v1"

    @staticmethod
    def generate_questions(assessment: Assessment) -> Tuple[List[Dict[str, Any]], GemmaResponse | None]:
        client = GemmaClient()
        prompt = (
            f"Assessment type: {assessment.assessment_type}\n"
            f"Target career: {assessment.target_career or 'Software Engineer'}\n"
            "Generate six serious, readable questions for career planning."
        )

        try:
            result = client.generate_structured(
                prompt=prompt,
                system=QUESTION_SYSTEM_PROMPT,
                required_keys=("questions",),
            )
            questions = _normalize_questions(result.payload.get("questions", []) if result.payload else [])
            if questions:
                return questions, result
        except Exception:
            pass

        return get_default_questions(assessment.assessment_type), None

    @staticmethod
    def evaluate_assessment(assessment: Assessment) -> AssessmentAnalysisResult:
        baseline = BaselineAssessmentAnalyzer.analyze(
            AssessmentAnalysisInput(
                assessment_id=str(assessment.id),
                assessment_type=assessment.assessment_type,
                target_career=assessment.target_career,
                responses=assessment.responses or [],
            )
        )

        prompt = (
            f"Assessment type: {assessment.assessment_type}\n"
            f"Target career: {assessment.target_career or 'Software Engineer'}\n"
            f"Questions: {assessment.questions}\n"
            f"Responses: {assessment.responses}\n"
            "Evaluate the answers and return structured JSON."
        )

        try:
            result = GemmaClient().generate_structured(
                prompt=prompt,
                system=EVALUATION_SYSTEM_PROMPT,
                required_keys=(
                    "overall_score",
                    "skill_scores",
                    "strengths",
                    "areas_for_improvement",
                    "recommended_careers",
                    "recommended_learning_paths",
                    "ai_insights",
                    "ai_confidence_score",
                ),
            )
            payload = result.payload or {}
            return AssessmentAnalysisResult(
                overall_score=Decimal(str(payload.get("overall_score", baseline.overall_score))),
                skill_scores=payload.get("skill_scores") or baseline.skill_scores,
                strengths=payload.get("strengths") or baseline.strengths,
                areas_for_improvement=payload.get("areas_for_improvement") or baseline.areas_for_improvement,
                recommended_careers=payload.get("recommended_careers") or baseline.recommended_careers,
                recommended_learning_paths=payload.get("recommended_learning_paths") or baseline.recommended_learning_paths,
                ai_insights=str(payload.get("ai_insights") or baseline.ai_insights),
                ai_confidence_score=Decimal(str(payload.get("ai_confidence_score", baseline.ai_confidence_score or 75))),
                metadata=build_ai_metadata(
                    source="llm",
                    processing_time_ms=result.metadata.processing_time_ms,
                    model=result.metadata.model,
                    provider=result.metadata.provider,
                    version=AssessmentAIService.EVALUATION_VERSION,
                    trace_id=result.metadata.trace_id,
                ),
            )
        except Exception as error:
            return AssessmentAnalysisResult(
                overall_score=baseline.overall_score,
                skill_scores=baseline.skill_scores,
                strengths=baseline.strengths,
                areas_for_improvement=baseline.areas_for_improvement,
                recommended_careers=baseline.recommended_careers,
                recommended_learning_paths=baseline.recommended_learning_paths,
                ai_insights=baseline.ai_insights,
                ai_confidence_score=baseline.ai_confidence_score,
                metadata=build_ai_metadata(
                    source="fallback",
                    processing_time_ms=baseline.metadata.processing_time_ms,
                    model=BaselineAssessmentAnalyzer.MODEL_NAME,
                    provider="sha8alny",
                    version=BaselineAssessmentAnalyzer.VERSION,
                    fallback_used=True,
                    error_code=type(error).__name__,
                ),
            )
