"""
Assessments Service Layer

Handles skill assessment creation, submission, and AI-powered analysis.
"""

from time import monotonic
from decimal import Decimal
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Assessment, AssessmentResult
from apps.users.models import User
from apps.core.ai_contracts import (
    AIInvocationMetadata,
    AssessmentAnalysisInput,
    AssessmentAnalysisResult,
)


class BaselineAssessmentAnalyzer:
    """Deterministic analyzer behind a model-safe contract."""

    MODEL_NAME = "baseline-assessment-v1"
    VERSION = "baseline-2026-04"

    @staticmethod
    def _score_responses(responses: List[Dict[str, Any]]) -> Decimal:
        score_sum = 0.0
        scored_responses = 0

        for response in responses:
            answer = response.get("answer", "")
            if isinstance(answer, (int, float)):
                score_sum += float(answer)
                scored_responses += 1
            elif isinstance(answer, str) and answer.strip().isdigit():
                score_sum += float(answer.strip())
                scored_responses += 1

        overall = (score_sum / scored_responses * 20) if scored_responses > 0 else 50
        return Decimal(str(round(overall, 2)))

    @staticmethod
    def _career_aliases(target_career: str) -> List[Dict[str, Any]]:
        normalized = target_career or "Software Engineer"
        lowered = normalized.lower()
        if "frontend" in lowered:
            return [
                {"title": normalized, "match_score": 88, "reasoning": "Your selected path remains the primary recommendation."},
                {"title": "Software Engineer", "match_score": 73, "reasoning": "Broader engineering roles stay adjacent to frontend growth."},
            ]
        if "backend" in lowered:
            return [
                {"title": normalized, "match_score": 88, "reasoning": "Your selected path remains the primary recommendation."},
                {"title": "Full Stack Developer", "match_score": 74, "reasoning": "Backend depth can expand toward full-stack execution later."},
            ]
        if "data" in lowered:
            return [
                {"title": normalized, "match_score": 86, "reasoning": "Your selected path remains the primary recommendation."},
                {"title": "Machine Learning Engineer", "match_score": 71, "reasoning": "The path can extend into model delivery and production work."},
            ]
        return [
            {"title": normalized, "match_score": 85, "reasoning": "Your selected path remains the primary recommendation."},
            {"title": "Full Stack Developer", "match_score": 72, "reasoning": "This stays nearby while you build broader execution skills."},
        ]

    @staticmethod
    def _learning_paths(target_career: str) -> List[Dict[str, Any]]:
        lowered = (target_career or "").lower()
        if "frontend" in lowered:
            return [
                {"skill": "React", "priority": "high", "resources": []},
                {"skill": "TypeScript", "priority": "high", "resources": []},
                {"skill": "Testing discipline", "priority": "medium", "resources": []},
            ]
        if "backend" in lowered:
            return [
                {"skill": "API design", "priority": "high", "resources": []},
                {"skill": "Databases", "priority": "high", "resources": []},
                {"skill": "Testing discipline", "priority": "medium", "resources": []},
            ]
        if "data" in lowered:
            return [
                {"skill": "Python", "priority": "high", "resources": []},
                {"skill": "Statistics", "priority": "high", "resources": []},
                {"skill": "Portfolio storytelling", "priority": "medium", "resources": []},
            ]
        return [
            {"skill": "Problem solving", "priority": "high", "resources": []},
            {"skill": "Project execution", "priority": "high", "resources": []},
            {"skill": "Testing discipline", "priority": "medium", "resources": []},
        ]

    @classmethod
    def analyze(cls, payload: AssessmentAnalysisInput) -> AssessmentAnalysisResult:
        started_at = monotonic()
        target_career = (payload.target_career or "Software Engineer").strip() or "Software Engineer"
        return AssessmentAnalysisResult(
            overall_score=cls._score_responses(payload.responses),
            skill_scores={},
            strengths=[
                "Commitment to a clear target path",
                "Structured self-assessment follow-through",
            ],
            areas_for_improvement=[
                "Project execution",
                "Testing discipline",
            ],
            recommended_careers=cls._career_aliases(target_career),
            recommended_learning_paths=cls._learning_paths(target_career),
            ai_insights=(
                f"This baseline analysis keeps {target_career} as the anchor role and turns your "
                "responses into immediate next-step guidance."
            ),
            ai_confidence_score=Decimal("78.00"),
            metadata=AIInvocationMetadata(
                source="baseline",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=cls.MODEL_NAME,
                provider="sha8alny",
                version=cls.VERSION,
            ),
        )


class AssessmentService:
    """Service for assessment management"""

    @staticmethod
    def get_user_assessments(user: User, assessment_type: Optional[str] = None) -> List[Assessment]:
        """Get all assessments for a user, optionally filtered by type"""
        queryset = Assessment.objects.filter(
            user=user,
            is_deleted=False
        )

        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)

        return list(queryset.order_by('-created_at'))

    @staticmethod
    def get_assessment_by_id(assessment_id: str, user: Optional[User] = None) -> Optional[Assessment]:
        """Get assessment by ID"""
        try:
            queryset = Assessment.objects.filter(id=assessment_id, is_deleted=False)
            if user:
                queryset = queryset.filter(user=user)
            return queryset.first()
        except Assessment.DoesNotExist:
            return None

    @staticmethod
    def get_latest_assessment(user: User, assessment_type: Optional[str] = None) -> Optional[Assessment]:
        """Get user's latest assessment"""
        queryset = Assessment.objects.filter(
            user=user,
            is_deleted=False
        )

        if assessment_type:
            queryset = queryset.filter(assessment_type=assessment_type)

        return queryset.order_by('-created_at').first()

    @staticmethod
    @transaction.atomic
    def create_assessment(
        user: User,
        assessment_type: str,
        target_career: str = "",
        questions: Optional[List[Dict[str, Any]]] = None
    ) -> Assessment:
        """
        Create a new assessment.

        Args:
            user: User taking the assessment
            assessment_type: Type (skills, career_interests, personality, etc.)
            questions: List of question dicts (optional, can be generated later)

        Returns:
            Assessment: Created assessment
        """
        # Validate assessment type
        valid_types = [choice[0] for choice in Assessment.ASSESSMENT_TYPE_CHOICES]
        if assessment_type not in valid_types:
            raise ValidationError(f"Invalid assessment type. Must be one of: {', '.join(valid_types)}")

        # TODO: Generate questions using AI if not provided
        if questions is None:
            questions = []

        assessment = Assessment.objects.create(
            user=user,
            assessment_type=assessment_type,
            target_career=target_career,
            questions=questions,
            total_questions=len(questions),
            status='draft'
        )

        return assessment

    @staticmethod
    @transaction.atomic
    def start_assessment(assessment_id: str, user: User) -> Assessment:
        """
        Start an assessment (mark as in_progress).

        Args:
            assessment_id: Assessment ID
            user: User taking assessment

        Returns:
            Assessment: Updated assessment
        """
        assessment = Assessment.objects.select_for_update().get(
            id=assessment_id,
            user=user,
            is_deleted=False
        )

        if assessment.status != 'draft':
            raise ValidationError("Assessment has already been started")

        assessment.status = 'in_progress'
        assessment.started_at = timezone.now()
        assessment.save()

        return assessment

    @staticmethod
    @transaction.atomic
    def submit_response(
        assessment_id: str,
        user: User,
        question_id: int,
        answer: Any
    ) -> Assessment:
        """
        Submit a single question response.

        Args:
            assessment_id: Assessment ID
            user: User submitting response
            question_id: Question ID being answered
            answer: User's answer

        Returns:
            Assessment: Updated assessment
        """
        assessment = Assessment.objects.select_for_update().get(
            id=assessment_id,
            user=user,
            is_deleted=False
        )

        if assessment.status not in ['draft', 'in_progress']:
            raise ValidationError("Cannot submit responses to completed assessment")

        # Add response to responses list
        response_entry = {
            'question_id': question_id,
            'answer': answer,
            'timestamp': timezone.now().isoformat()
        }

        responses = assessment.responses or []

        # Update existing response or add new one
        existing_idx = next(
            (i for i, r in enumerate(responses) if r.get('question_id') == question_id),
            None
        )

        if existing_idx is not None:
            responses[existing_idx] = response_entry
        else:
            responses.append(response_entry)

        assessment.responses = responses
        assessment.answered_questions = len(responses)
        assessment.save()

        return assessment

    @staticmethod
    @transaction.atomic
    def complete_assessment(
        assessment_id: str,
        user: User,
        responses: Optional[List[Dict[str, Any]]] = None
    ) -> Assessment:
        """
        Complete an assessment and mark for AI processing.

        Args:
            assessment_id: Assessment ID
            user: User completing assessment
            responses: Complete list of responses (optional if already submitted individually)

        Returns:
            Assessment: Completed assessment
        """
        assessment = Assessment.objects.select_for_update().get(
            id=assessment_id,
            user=user,
            is_deleted=False
        )

        if assessment.status == 'completed':
            raise ValidationError("Assessment already completed")

        # Update responses if provided
        if responses is not None:
            assessment.responses = responses
            assessment.answered_questions = len(responses)

        assessment.status = 'completed'
        assessment.completed_at = timezone.now()
        assessment.ai_processing_status = 'pending'
        assessment.save()

        # TODO: Trigger async AI processing task
        # tasks.process_assessment_ai.delay(str(assessment.id))

        return assessment


class AssessmentResultService:
    """Service for assessment result analysis"""

    @staticmethod
    def get_user_results(user: User) -> List[AssessmentResult]:
        """Get all assessment results for user"""
        return list(AssessmentResult.objects.filter(
            assessment__user=user,
            is_deleted=False
        ).select_related('assessment').order_by('-created_at'))

    @staticmethod
    def get_result_by_assessment(assessment_id: str) -> Optional[AssessmentResult]:
        """Get result for a specific assessment"""
        try:
            return AssessmentResult.objects.select_related('assessment').get(
                assessment_id=assessment_id,
                is_deleted=False
            )
        except AssessmentResult.DoesNotExist:
            return None

    @staticmethod
    def get_result_by_id(result_id: str) -> Optional[AssessmentResult]:
        """Get result by ID"""
        try:
            return AssessmentResult.objects.select_related('assessment').get(
                id=result_id,
                is_deleted=False
            )
        except AssessmentResult.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def create_assessment_result(
        assessment: Assessment,
        overall_score: float,
        skill_scores: Optional[Dict[str, Any]] = None,
        strengths: Optional[List[str]] = None,
        areas_for_improvement: Optional[List[str]] = None,
        recommended_careers: Optional[List[Dict[str, Any]]] = None,
        recommended_learning_paths: Optional[List[Dict[str, Any]]] = None,
        ai_insights: str = "",
        ai_confidence_score: Optional[float] = None,
        llm_model_used: str = "",
        llm_prompt_tokens: Optional[int] = None,
        llm_completion_tokens: Optional[int] = None,
        processing_time_seconds: Optional[float] = None
    ) -> AssessmentResult:
        """
        Create AI-analyzed assessment result.

        Args:
            assessment: Assessment instance
            overall_score: Overall score (0-100)
            skill_scores: Detailed skill scores by category
            strengths: List of identified strengths
            areas_for_improvement: List of areas needing improvement
            recommended_careers: List of recommended career paths
            recommended_learning_paths: Recommended skills to learn
            ai_insights: Natural language AI insights
            ai_confidence_score: AI confidence (0-100)
            llm_model_used: LLM model name
            llm_prompt_tokens: Prompt tokens used
            llm_completion_tokens: Completion tokens used
            processing_time_seconds: Processing time

        Returns:
            AssessmentResult: Created result
        """
        # Check for existing result
        existing = AssessmentResult.objects.filter(
            assessment=assessment,
            is_deleted=False
        ).first()

        if existing:
            # Update existing result
            existing.overall_score = overall_score
            existing.skill_scores = skill_scores or {}
            existing.strengths = strengths or []
            existing.areas_for_improvement = areas_for_improvement or []
            existing.recommended_careers = recommended_careers or []
            existing.recommended_learning_paths = recommended_learning_paths or []
            existing.ai_insights = ai_insights
            existing.ai_confidence_score = ai_confidence_score
            existing.llm_model_used = llm_model_used
            existing.llm_prompt_tokens = llm_prompt_tokens
            existing.llm_completion_tokens = llm_completion_tokens
            existing.processing_time_seconds = processing_time_seconds
            existing.save()
            return existing

        # Create new result
        result = AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=overall_score,
            skill_scores=skill_scores or {},
            strengths=strengths or [],
            areas_for_improvement=areas_for_improvement or [],
            recommended_careers=recommended_careers or [],
            recommended_learning_paths=recommended_learning_paths or [],
            ai_insights=ai_insights,
            ai_confidence_score=ai_confidence_score,
            llm_model_used=llm_model_used,
            llm_prompt_tokens=llm_prompt_tokens,
            llm_completion_tokens=llm_completion_tokens,
            processing_time_seconds=processing_time_seconds
        )

        # Update assessment AI processing status
        assessment.ai_processing_status = 'completed'
        assessment.ai_processed_at = timezone.now()
        assessment.save()

        return result

    @staticmethod
    def get_skill_summary(user: User) -> Dict[str, Any]:
        """
        Get comprehensive skill summary across all assessments.

        Returns:
            Dict with skill categories, scores, strengths, weaknesses
        """
        results = AssessmentResult.objects.filter(
            assessment__user=user,
            is_deleted=False
        ).select_related('assessment')

        # Aggregate skill scores across all assessments
        all_skills = {}
        all_strengths = []
        all_weaknesses = []

        for result in results:
            # Collect skill scores
            for category, skills in result.skill_scores.items():
                if isinstance(skills, dict):
                    if category not in all_skills:
                        all_skills[category] = {}
                    for skill_name, score in skills.items():
                        # Keep highest score for each skill
                        if skill_name not in all_skills[category] or score > all_skills[category][skill_name]:
                            all_skills[category][skill_name] = score

            # Collect strengths and weaknesses
            all_strengths.extend(result.strengths)
            all_weaknesses.extend(result.areas_for_improvement)

        # Calculate average scores by category
        category_averages = {}
        for category, skills in all_skills.items():
            if skills:
                category_averages[category] = sum(skills.values()) / len(skills)

        return {
            'skill_scores': all_skills,
            'category_averages': category_averages,
            'strengths': list(set(all_strengths)),  # Deduplicate
            'areas_for_improvement': list(set(all_weaknesses)),
            'total_assessments': results.count()
        }

    @staticmethod
    def get_assessment_statistics(user: User) -> Dict[str, Any]:
        """
        Get statistics about user's assessments.

        Returns:
            Dict with counts, averages, and trends
        """
        assessments = Assessment.objects.filter(
            user=user,
            is_deleted=False
        )

        completed = assessments.filter(status='completed')
        in_progress = assessments.filter(status='in_progress')

        results = AssessmentResult.objects.filter(
            assessment__user=user,
            is_deleted=False
        )

        avg_score = 0
        if results.exists():
            total_score = sum(float(r.overall_score) for r in results)
            avg_score = total_score / results.count()

        return {
            'total_assessments': assessments.count(),
            'completed_assessments': completed.count(),
            'in_progress_assessments': in_progress.count(),
            'average_score': round(avg_score, 2),
            'results_count': results.count(),
            'latest_assessment': completed.order_by('-completed_at').first(),
        }
