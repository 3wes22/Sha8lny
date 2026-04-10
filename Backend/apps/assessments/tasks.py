from __future__ import annotations

from celery import shared_task
from django.utils import timezone

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.models import Assessment
from apps.assessments.services import AssessmentResultService


def run_generate_assessment_questions(assessment_id: str, *, task_id: str = "") -> str:
    assessment = Assessment.objects.get(id=assessment_id, is_deleted=False)
    assessment.ai_processing_status = "processing"
    assessment.ai_task_id = task_id
    assessment.save(update_fields=["ai_processing_status", "ai_task_id", "updated_at"])

    questions, generation = AssessmentAIService.generate_questions(assessment)
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

    analysis = AssessmentAIService.evaluate_assessment(assessment)
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


@shared_task(bind=True)
def generate_assessment_questions_task(self, assessment_id: str) -> str:
    return run_generate_assessment_questions(assessment_id, task_id=self.request.id or "")


@shared_task(bind=True)
def evaluate_assessment_answers_task(self, assessment_id: str) -> str:
    return run_evaluate_assessment_answers(assessment_id, task_id=self.request.id or "")
