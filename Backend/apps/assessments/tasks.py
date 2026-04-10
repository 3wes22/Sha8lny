from __future__ import annotations

import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.models import Assessment
from apps.assessments.services import AssessmentResultService
from apps.core.ai_logging import log_ai_failure
from apps.core.ai_settings import AI_TASK_HARD_TIME_LIMIT, AI_TASK_SOFT_TIME_LIMIT

logger = logging.getLogger(__name__)


def _mark_assessment_failed(assessment_id: str, error: Exception, task_id: str = "") -> None:
    """Mark an assessment as failed so the frontend never shows a perpetual spinner."""
    try:
        Assessment.objects.filter(id=assessment_id, is_deleted=False).update(
            ai_processing_status="failed",
            ai_processing_error=f"{type(error).__name__}: {str(error)[:300]}",
            updated_at=timezone.now(),
        )
    except Exception as update_error:
        logger.error(
            "Failed to record assessment failure status for %s: %s",
            assessment_id,
            update_error,
        )

    log_ai_failure(
        feature="assessment",
        error=error,
        trace_id=task_id or assessment_id,
        extra={"assessment_id": assessment_id},
    )


def run_generate_assessment_questions(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
    assessment.ai_processing_status = "processing"
    assessment.ai_task_id = task_id
    assessment.save(update_fields=["ai_processing_status", "ai_task_id", "updated_at"])

    try:
        questions, generation = AssessmentAIService.generate_questions(assessment)
    except (SoftTimeLimitExceeded, Exception) as error:
        _mark_assessment_failed(assessment_id, error, task_id)
        raise

    assessment.questions = questions
    assessment.total_questions = len(questions)
    assessment.ai_processing_status = "completed"
    assessment.ai_processed_at = timezone.now()
    assessment.ai_processing_error = ""
    assessment.ai_trace_id = generation.metadata.trace_id if generation else assessment.ai_trace_id
    assessment.save(
        update_fields=[
            "questions",
            "total_questions",
            "ai_processing_status",
            "ai_processed_at",
            "ai_processing_error",
            "ai_trace_id",
            "updated_at",
        ]
    )
    return str(assessment.id)


def run_evaluate_assessment_answers(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
    assessment.ai_processing_status = "processing"
    assessment.ai_task_id = task_id
    assessment.save(update_fields=["ai_processing_status", "ai_task_id", "updated_at"])

    try:
        analysis = AssessmentAIService.evaluate_assessment(assessment)
    except (SoftTimeLimitExceeded, Exception) as error:
        _mark_assessment_failed(assessment_id, error, task_id)
        raise

    AssessmentResultService.create_assessment_result(
        assessment=assessment,
        overall_score=analysis.overall_score,
        skill_scores=analysis.skill_scores,
        strengths=analysis.strengths,
        areas_for_improvement=analysis.areas_for_improvement,
        recommended_careers=analysis.recommended_careers,
        recommended_learning_paths=analysis.recommended_learning_paths,
        ai_insights=analysis.ai_insights,
        ai_confidence_score=analysis.ai_confidence_score,
        llm_model_used=analysis.metadata.model or "",
        processing_time_seconds=analysis.metadata.processing_time_ms / 1000,
        version=analysis.metadata.version or "1.0",
    )
    assessment.ai_processing_status = "completed"
    assessment.ai_processed_at = timezone.now()
    assessment.ai_processing_error = ""
    assessment.ai_trace_id = analysis.metadata.trace_id
    assessment.save(
        update_fields=[
            "ai_processing_status",
            "ai_processed_at",
            "ai_processing_error",
            "ai_trace_id",
            "updated_at",
        ]
    )
    return str(assessment.id)


@shared_task(
    bind=True,
    soft_time_limit=AI_TASK_SOFT_TIME_LIMIT,
    time_limit=AI_TASK_HARD_TIME_LIMIT,
)
def generate_assessment_questions_task(self, assessment_id: str) -> str:
    return run_generate_assessment_questions(assessment_id, task_id=self.request.id or "")


@shared_task(
    bind=True,
    soft_time_limit=AI_TASK_SOFT_TIME_LIMIT,
    time_limit=AI_TASK_HARD_TIME_LIMIT,
)
def evaluate_assessment_answers_task(self, assessment_id: str) -> str:
    return run_evaluate_assessment_answers(assessment_id, task_id=self.request.id or "")
