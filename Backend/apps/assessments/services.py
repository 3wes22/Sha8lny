"""
Assessments Service Layer

Handles skill assessment creation, submission, and AI-powered analysis.
"""

from dataclasses import asdict
from time import monotonic
from decimal import Decimal
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Assessment, AssessmentResult
from .role_graph import load_role_graph, resolve_role_key
from apps.users.models import User
from apps.core.ai_contracts import (
    AIInvocationMetadata,
    AssessmentAnalysisInput,
    AssessmentAnalysisResult,
)


class BaselineAssessmentAnalyzer:
    """Deterministic analyzer with dimension-weighted scoring.

    Covers 6 assessment dimensions with configurable weights:
      - technical_depth (25%), tooling (15%), problem_solving (20%),
        experience (20%), goals (10%), commitment (10%)
    """

    MODEL_NAME = "baseline-assessment-v2"
    VERSION = "baseline-2026-04"

    DIMENSION_WEIGHTS: Dict[str, float] = {
        "technical_depth": 0.25,
        "tooling": 0.15,
        "problem_solving": 0.20,
        "experience": 0.20,
        "goals": 0.10,
        "commitment": 0.10,
    }

    # Dimension labels used in human-readable output
    DIMENSION_LABELS: Dict[str, str] = {
        "technical_depth": "Core technical skills",
        "tooling": "Tooling & ecosystem knowledge",
        "problem_solving": "Problem-solving & debugging",
        "experience": "Hands-on project experience",
        "goals": "Goal clarity",
        "commitment": "Learning commitment",
    }

    @classmethod
    def _score_by_dimension(
        cls, responses: List[Dict[str, Any]], questions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Score each dimension on a 0-100 scale from response scores."""
        dimension_scores: Dict[str, List[float]] = {}

        # Build question lookup for dimension mapping
        question_map: Dict[Any, Dict[str, Any]] = {}
        for q in questions:
            question_map[q.get("id")] = q
            question_map[str(q.get("id"))] = q

        for resp in responses:
            qid = resp.get("question_id")
            question = question_map.get(qid) or question_map.get(str(qid)) or {}
            dimension = question.get("dimension", "technical_depth")

            answer = resp.get("answer", "")
            raw_score = 0.0

            if isinstance(answer, (int, float)):
                raw_score = float(answer)
            elif isinstance(answer, str):
                # For text answers, give a moderate score (goal clarity)
                stripped = answer.strip()
                if stripped.isdigit():
                    raw_score = float(stripped)
                elif len(stripped) > 10:
                    raw_score = 3.0  # meaningful text answer
                else:
                    raw_score = 2.0  # very short text

                # Check if the answer has a score in options
                options = question.get("options", [])
                for opt in options:
                    if isinstance(opt, dict) and opt.get("value") == stripped:
                        raw_score = float(opt.get("score", raw_score))
                        break

            # Normalize to 0-100 (scores are on 1-5 scale)
            normalized = min(100.0, max(0.0, (raw_score / 5.0) * 100.0))
            dimension_scores.setdefault(dimension, []).append(normalized)

        # Average scores per dimension, default to 50 if missing
        result: Dict[str, float] = {}
        for dim in cls.DIMENSION_WEIGHTS:
            scores = dimension_scores.get(dim, [])
            result[dim] = round(sum(scores) / len(scores), 1) if scores else 50.0

        return result

    @classmethod
    def _weighted_overall(cls, dimension_scores: Dict[str, float]) -> Decimal:
        """Compute weighted overall score from dimension scores."""
        total = 0.0
        for dim, weight in cls.DIMENSION_WEIGHTS.items():
            total += dimension_scores.get(dim, 50.0) * weight
        return Decimal(str(round(total, 2)))

    @classmethod
    def _derive_strengths(cls, dimension_scores: Dict[str, float]) -> List[str]:
        """Identify top 2-3 strengths from highest-scoring dimensions."""
        sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = []
        for dim, score in sorted_dims[:3]:
            if score >= 60:
                strengths.append(cls.DIMENSION_LABELS.get(dim, dim))
        if not strengths:
            strengths = ["Commitment to a clear target path", "Willingness to self-assess"]
        return strengths

    @classmethod
    def _derive_gaps(cls, dimension_scores: Dict[str, float]) -> List[str]:
        """Identify top 2-3 weakness areas from lowest-scoring dimensions."""
        sorted_dims = sorted(dimension_scores.items(), key=lambda x: x[1])
        gaps = []
        for dim, score in sorted_dims[:3]:
            if score < 70:
                gaps.append(cls.DIMENSION_LABELS.get(dim, dim))
        if not gaps:
            gaps = ["Advanced specialization", "Production-scale project experience"]
        return gaps

    @staticmethod
    def _career_aliases(target_career: str) -> List[Dict[str, Any]]:
        normalized = target_career or "Software Engineer"
        lowered = normalized.lower()

        career_map = {
            "frontend": ("UI/UX Developer", 72, "Frontend skills transfer directly to UI/UX roles with design thinking."),
            "backend": ("Full Stack Developer", 74, "Backend depth expands naturally toward full-stack execution."),
            "data": ("Machine Learning Engineer", 71, "Data science foundations extend into model delivery and MLOps."),
            "fullstack": ("Backend Developer", 73, "Strong backend focus can deepen your full-stack expertise."),
            "full stack": ("Backend Developer", 73, "Strong backend focus can deepen your full-stack expertise."),
            "mobile": ("Frontend Developer", 70, "Mobile experience translates well to responsive web development."),
            "devops": ("Cloud Architect", 72, "DevOps experience is the natural path to cloud architecture roles."),
            "cloud": ("DevOps Engineer", 73, "Cloud skills directly complement DevOps and SRE workflows."),
        }

        adjacent_title = "Full Stack Developer"
        adjacent_score = 72
        adjacent_reason = "This role stays adjacent while you build broader execution skills."

        for keyword, (title, score, reason) in career_map.items():
            if keyword in lowered:
                adjacent_title = title
                adjacent_score = score
                adjacent_reason = reason
                break

        return [
            {"title": normalized, "match_score": 87, "reasoning": "Your selected career path remains your primary recommendation."},
            {"title": adjacent_title, "match_score": adjacent_score, "reasoning": adjacent_reason},
        ]

    @staticmethod
    def _learning_paths(target_career: str) -> List[Dict[str, Any]]:
        lowered = (target_career or "").lower()

        paths_map: Dict[str, List[Dict[str, Any]]] = {
            "frontend": [
                {"skill": "React & component architecture", "priority": "high", "resources": []},
                {"skill": "TypeScript", "priority": "high", "resources": []},
                {"skill": "Testing (Jest & React Testing Library)", "priority": "medium", "resources": []},
            ],
            "backend": [
                {"skill": "REST API design & Django", "priority": "high", "resources": []},
                {"skill": "Database design & SQL optimization", "priority": "high", "resources": []},
                {"skill": "Testing (pytest & integration tests)", "priority": "medium", "resources": []},
            ],
            "data": [
                {"skill": "Python data stack (Pandas, NumPy, Scikit-learn)", "priority": "high", "resources": []},
                {"skill": "Statistics & probability", "priority": "high", "resources": []},
                {"skill": "Data visualization & storytelling", "priority": "medium", "resources": []},
            ],
            "fullstack": [
                {"skill": "Full-stack integration (React + Django)", "priority": "high", "resources": []},
                {"skill": "Authentication & authorization flows", "priority": "high", "resources": []},
                {"skill": "Deployment & DevOps basics (Docker)", "priority": "medium", "resources": []},
            ],
            "mobile": [
                {"skill": "Flutter or React Native", "priority": "high", "resources": []},
                {"skill": "State management & navigation", "priority": "high", "resources": []},
                {"skill": "Publishing to App Store / Play Store", "priority": "medium", "resources": []},
            ],
            "devops": [
                {"skill": "Docker & containerization", "priority": "high", "resources": []},
                {"skill": "CI/CD pipelines (GitHub Actions)", "priority": "high", "resources": []},
                {"skill": "Cloud platform (AWS or GCP fundamentals)", "priority": "medium", "resources": []},
            ],
        }

        for keyword, paths in paths_map.items():
            if keyword in lowered:
                return paths

        # Generic fallback
        return [
            {"skill": "Core technical depth in your chosen area", "priority": "high", "resources": []},
            {"skill": "Project execution & portfolio building", "priority": "high", "resources": []},
            {"skill": "Testing discipline", "priority": "medium", "resources": []},
        ]

    @staticmethod
    def staged_role_recommendations(role_graph) -> List[Dict[str, Any]]:
        focus_areas = ", ".join(dimension.label.lower() for dimension in role_graph.dimensions[:2])
        return [
            {
                "title": role_graph.role_label,
                "match_score": 92,
                "reasoning": (
                    f"This staged result is calibrated against the curated {role_graph.role_label.lower()} "
                    f"graph, with strong emphasis on {focus_areas}."
                ),
            }
        ]

    @classmethod
    def analyze(cls, payload: AssessmentAnalysisInput) -> AssessmentAnalysisResult:
        started_at = monotonic()
        target_career = (payload.target_career or "Software Engineer").strip() or "Software Engineer"

        # Use questions from the contract — they carry dimension metadata.
        questions = payload.questions or []
        dimension_scores = cls._score_by_dimension(payload.responses, questions)
        overall = cls._weighted_overall(dimension_scores)
        strengths = cls._derive_strengths(dimension_scores)
        gaps = cls._derive_gaps(dimension_scores)

        return AssessmentAnalysisResult(
            overall_score=overall,
            skill_scores=dimension_scores,
            strengths=strengths,
            areas_for_improvement=gaps,
            recommended_careers=cls._career_aliases(target_career),
            recommended_learning_paths=cls._learning_paths(target_career),
            ai_insights=(
                f"Based on your self-assessment for {target_career}, your strongest area is "
                f"{strengths[0].lower() if strengths else 'your commitment'}, while "
                f"{gaps[0].lower() if gaps else 'advanced specialization'} is the most impactful "
                f"area to focus on next."
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
    def is_staged_assessment(assessment: Assessment) -> bool:
        return assessment.is_staged

    @staticmethod
    def get_active_questions(assessment: Assessment) -> List[Dict[str, Any]]:
        if not assessment.is_staged:
            return assessment.questions or []
        if assessment.stage == 'stage_2':
            return assessment.stage_two_questions or []
        if assessment.stage == 'completed':
            return []
        return assessment.stage_one_questions or []

    @staticmethod
    def get_active_responses(assessment: Assessment) -> List[Dict[str, Any]]:
        if not assessment.is_staged:
            return assessment.responses or []
        if assessment.stage == 'stage_2':
            return assessment.stage_two_responses or []
        if assessment.stage == 'completed':
            return []
        return assessment.stage_one_responses or []

    @staticmethod
    def build_gap_profile_summary(assessment: Assessment) -> Optional[Dict[str, Any]]:
        gap_profile = assessment.gap_profile or {}
        if not isinstance(gap_profile, dict) or not gap_profile:
            return None
        return {
            'high_priority_count': len(gap_profile.get('high_priority_gaps', [])),
            'uncertain_count': len(gap_profile.get('uncertain_areas', [])),
            'overall_calibration': gap_profile.get('overall_calibration', 0),
        }

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

        if assessment_type == 'skills':
            assessment = Assessment.objects.create(
                user=user,
                assessment_type=assessment_type,
                target_career=target_career,
                questions=[],
                responses=[],
                stage='stage_1',
                stage_one_questions=[],
                stage_one_responses=[],
                stage_two_questions=[],
                stage_two_responses=[],
                gap_profile={},
                roadmap_signal={},
                generation_metadata={
                    'role_key': resolve_role_key(target_career),
                    'graph_version': load_role_graph(resolve_role_key(target_career)).version,
                },
                total_questions=10,
                answered_questions=0,
                status='draft',
                ai_processing_status='pending',
            )
            return assessment

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

    @staticmethod
    @transaction.atomic
    def submit_stage_one(
        assessment_id: str,
        user: User,
        responses: List[Dict[str, Any]],
    ) -> Assessment:
        assessment = Assessment.objects.select_for_update().get(
            id=assessment_id,
            user=user,
            is_deleted=False,
        )

        if not assessment.is_staged or assessment.stage != 'stage_1':
            raise ValidationError("Assessment is not ready for stage one submission")

        assessment.stage_one_responses = responses
        assessment.responses = responses
        assessment.answered_questions = len(responses)
        assessment.status = 'in_progress'
        assessment.started_at = assessment.started_at or timezone.now()
        assessment.ai_processing_status = 'processing'
        assessment.ai_processing_error = ''
        assessment.save(
            update_fields=[
                'stage_one_responses',
                'responses',
                'answered_questions',
                'status',
                'started_at',
                'ai_processing_status',
                'ai_processing_error',
                'updated_at',
            ]
        )
        return assessment

    @staticmethod
    @transaction.atomic
    def submit_stage_two(
        assessment_id: str,
        user: User,
        responses: List[Dict[str, Any]],
    ) -> Assessment:
        assessment = Assessment.objects.select_for_update().get(
            id=assessment_id,
            user=user,
            is_deleted=False,
        )

        if not assessment.is_staged or assessment.stage != 'stage_2':
            raise ValidationError("Assessment is not ready for stage two submission")

        assessment.stage_two_responses = responses
        assessment.responses = responses
        assessment.answered_questions = len(assessment.stage_one_responses or []) + len(responses)
        assessment.status = 'completed'
        assessment.completed_at = timezone.now()
        assessment.ai_processing_status = 'processing'
        assessment.ai_processing_error = ''
        assessment.save(
            update_fields=[
                'stage_two_responses',
                'responses',
                'answered_questions',
                'status',
                'completed_at',
                'ai_processing_status',
                'ai_processing_error',
                'updated_at',
            ]
        )
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
        processing_time_seconds: Optional[float] = None,
        version: str = "1.0",
        roadmap_signal: Optional[Dict[str, Any]] = None,
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
            existing.version = version
            existing.roadmap_signal = roadmap_signal or {}
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
            processing_time_seconds=processing_time_seconds,
            version=version,
            roadmap_signal=roadmap_signal or {},
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
