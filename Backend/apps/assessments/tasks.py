from __future__ import annotations

import logging
from dataclasses import asdict

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from django.utils import timezone

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.models import Assessment
from apps.assessments.role_graph import load_role_graph, resolve_role_key
from apps.assessments.services import AssessmentResultService
from apps.core.ai_logging import log_ai_failure
from apps.core.ai_settings import AI_TASK_HARD_TIME_LIMIT, AI_TASK_SOFT_TIME_LIMIT

logger = logging.getLogger(__name__)


def _metadata(assessment: Assessment) -> dict:
    return assessment.generation_metadata if isinstance(assessment.generation_metadata, dict) else {}


def _update_generation_metadata(assessment: Assessment, key: str, payload: dict) -> None:
    metadata = _metadata(assessment)
    metadata[key] = {
        **(metadata.get(key) if isinstance(metadata.get(key), dict) else {}),
        **payload,
    }
    assessment.generation_metadata = metadata


def _mark_assessment_failed(assessment_id: str, error: Exception, task_id: str = "") -> None:
    try:
        assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
        _update_generation_metadata(
            assessment,
            "failure",
            {
                "task_id": task_id or assessment_id,
                "error_type": type(error).__name__,
                "error_message": str(error)[:300],
                "failed_at": timezone.now().isoformat(),
            },
        )
        assessment.ai_processing_status = "failed"
        assessment.ai_processing_error = f"{type(error).__name__}: {str(error)[:300]}"
        assessment.save(
            update_fields=[
                "generation_metadata",
                "ai_processing_status",
                "ai_processing_error",
                "updated_at",
            ]
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


def run_generate_stage_one(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
    assessment.ai_processing_status = "processing"
    assessment.ai_task_id = task_id
    assessment.save(update_fields=["ai_processing_status", "ai_task_id", "updated_at"])

    try:
        graph = load_role_graph(resolve_role_key(assessment.target_career))
        questions, metadata = AssessmentAIService.generate_stage_one(graph.role_key, graph)
    except (SoftTimeLimitExceeded, Exception) as error:
        _mark_assessment_failed(assessment_id, error, task_id)
        raise

    assessment.stage = "stage_1"
    assessment.stage_one_questions = questions
    assessment.questions = questions
    assessment.total_questions = 10
    assessment.ai_processing_status = "completed"
    assessment.ai_processed_at = timezone.now()
    assessment.ai_processing_error = ""
    assessment.ai_trace_id = metadata.trace_id
    _update_generation_metadata(
        assessment,
        "stage_one",
        {
            "task_id": task_id,
            "trace_id": metadata.trace_id,
            "source": metadata.source,
            "fallback_used": metadata.fallback_used,
            "model": metadata.model,
            "provider": metadata.provider,
            "processing_time_ms": metadata.processing_time_ms,
            "error_code": metadata.error_code,
            "version": graph.version,
            "ready_at": timezone.now().isoformat(),
        },
    )
    assessment.save(
        update_fields=[
            "stage",
            "stage_one_questions",
            "questions",
            "total_questions",
            "generation_metadata",
            "ai_processing_status",
            "ai_processed_at",
            "ai_processing_error",
            "ai_trace_id",
            "updated_at",
        ]
    )
    return str(assessment.id)


def run_process_stage_one_submission(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
    try:
        role_graph = load_role_graph(resolve_role_key(assessment.target_career))
        gap_profile = AssessmentAIService.build_gap_profile(assessment, role_graph)
        questions, metadata = AssessmentAIService.generate_stage_two(gap_profile, role_graph)
    except (SoftTimeLimitExceeded, Exception) as error:
        _mark_assessment_failed(assessment_id, error, task_id)
        raise

    assessment.stage = "stage_2"
    assessment.gap_profile = asdict(gap_profile)
    assessment.stage_two_questions = questions
    assessment.questions = questions
    assessment.responses = []
    assessment.ai_processing_status = "completed"
    assessment.ai_processed_at = timezone.now()
    assessment.ai_processing_error = ""
    assessment.ai_trace_id = metadata.trace_id
    _update_generation_metadata(
        assessment,
        "stage_two",
        {
            "task_id": task_id,
            "trace_id": metadata.trace_id,
            "source": metadata.source,
            "fallback_used": metadata.fallback_used,
            "model": metadata.model,
            "provider": metadata.provider,
            "processing_time_ms": metadata.processing_time_ms,
            "error_code": metadata.error_code,
            "ready_at": timezone.now().isoformat(),
        },
    )
    assessment.save(
        update_fields=[
            "stage",
            "gap_profile",
            "stage_two_questions",
            "questions",
            "responses",
            "generation_metadata",
            "ai_processing_status",
            "ai_processed_at",
            "ai_processing_error",
            "ai_trace_id",
            "updated_at",
        ]
    )
    return str(assessment.id)


def run_process_final_evaluation(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)

    try:
        evaluation = AssessmentAIService.evaluate_staged_assessment(assessment)
    except (SoftTimeLimitExceeded, Exception) as error:
        _mark_assessment_failed(assessment_id, error, task_id)
        raise

    AssessmentResultService.create_assessment_result(
        assessment=assessment,
        overall_score=evaluation.analysis.overall_score,
        skill_scores=evaluation.analysis.skill_scores,
        strengths=evaluation.analysis.strengths,
        areas_for_improvement=evaluation.analysis.areas_for_improvement,
        recommended_careers=evaluation.analysis.recommended_careers,
        recommended_learning_paths=evaluation.analysis.recommended_learning_paths,
        ai_insights=evaluation.analysis.ai_insights,
        ai_confidence_score=evaluation.analysis.ai_confidence_score,
        llm_model_used=evaluation.analysis.metadata.model or "",
        llm_prompt_tokens=evaluation.prompt_tokens,
        llm_completion_tokens=evaluation.completion_tokens,
        processing_time_seconds=evaluation.analysis.metadata.processing_time_ms / 1000,
        version=evaluation.analysis.metadata.version or "staged-v1",
        roadmap_signal=asdict(evaluation.roadmap_signal),
    )

    assessment.stage = "completed"
    assessment.status = "completed"
    assessment.questions = []
    assessment.responses = []
    assessment.roadmap_signal = asdict(evaluation.roadmap_signal)
    assessment.ai_processing_status = "completed"
    assessment.ai_processed_at = timezone.now()
    assessment.ai_processing_error = ""
    assessment.ai_trace_id = evaluation.analysis.metadata.trace_id
    _update_generation_metadata(
        assessment,
        "final_evaluation",
        {
            "task_id": task_id,
            "trace_id": evaluation.analysis.metadata.trace_id,
            "source": evaluation.analysis.metadata.source,
            "fallback_used": evaluation.analysis.metadata.fallback_used,
            "model": evaluation.analysis.metadata.model,
            "provider": evaluation.analysis.metadata.provider,
            "processing_time_ms": evaluation.analysis.metadata.processing_time_ms,
            "error_code": evaluation.analysis.metadata.error_code,
            "completed_at": timezone.now().isoformat(),
        },
    )
    assessment.save(
        update_fields=[
            "stage",
            "status",
            "questions",
            "responses",
            "roadmap_signal",
            "generation_metadata",
            "ai_processing_status",
            "ai_processed_at",
            "ai_processing_error",
            "ai_trace_id",
            "updated_at",
        ]
    )
    return str(assessment.id)


def run_generate_assessment_questions(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
    if assessment.is_staged:
        return run_generate_stage_one(assessment_id, task_id=task_id)

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
    if assessment.is_staged:
        return run_process_final_evaluation(assessment_id, task_id=task_id)

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
def generate_stage_one_task(self, assessment_id: str) -> str:
    return run_generate_stage_one(assessment_id, task_id=self.request.id or "")


@shared_task(
    bind=True,
    soft_time_limit=AI_TASK_SOFT_TIME_LIMIT,
    time_limit=AI_TASK_HARD_TIME_LIMIT,
)
def process_stage_one_submission_task(self, assessment_id: str) -> str:
    return run_process_stage_one_submission(assessment_id, task_id=self.request.id or "")


@shared_task(
    bind=True,
    soft_time_limit=AI_TASK_SOFT_TIME_LIMIT,
    time_limit=AI_TASK_HARD_TIME_LIMIT,
)
def process_final_evaluation_task(self, assessment_id: str) -> str:
    return run_process_final_evaluation(assessment_id, task_id=self.request.id or "")


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
