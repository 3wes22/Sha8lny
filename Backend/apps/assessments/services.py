"""
Assessments Service Layer

Handles skill assessment creation, submission, and AI-powered analysis.
"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Assessment, AssessmentQuestion, AssessmentSubmission, AssessmentResult
from apps.users.models import User
from apps.notifications.signals import assessment_submitted, assessment_completed


class AssessmentService:
    """Service for assessment management"""

    @staticmethod
    def get_published_assessments(category: Optional[str] = None) -> List[Assessment]:
        """Get all published assessments, optionally filtered by category"""
        queryset = Assessment.objects.filter(
            is_published=True,
            is_deleted=False
        )

        if category:
            queryset = queryset.filter(category=category)

        return list(queryset.order_by('-created_at'))

    @staticmethod
    def get_assessment_by_id(assessment_id: str) -> Optional[Assessment]:
        """Get assessment by ID with questions"""
        try:
            return Assessment.objects.prefetch_related('questions').get(
                id=assessment_id,
                is_deleted=False
            )
        except Assessment.DoesNotExist:
            return None

    @staticmethod
    def get_assessment_questions(assessment: Assessment) -> List[AssessmentQuestion]:
        """Get all questions for an assessment in order"""
        return list(assessment.questions.filter(
            is_deleted=False
        ).order_by('order'))

    @staticmethod
    @transaction.atomic
    def create_assessment(
        title: str,
        description: str,
        assessment_type: str,
        category: str,
        difficulty_level: str,
        estimated_duration_minutes: int,
        passing_score: int = 70
    ) -> Assessment:
        """
        Create a new assessment.

        Args:
            title: Assessment title
            description: Assessment description
            assessment_type: Type (skill_evaluation, career_aptitude, knowledge_check)
            category: Category (programming, design, business, etc.)
            difficulty_level: Difficulty (beginner, intermediate, advanced)
            estimated_duration_minutes: Time estimate
            passing_score: Minimum score to pass (0-100)

        Returns:
            Assessment: Created assessment
        """
        assessment = Assessment.objects.create(
            title=title,
            description=description,
            assessment_type=assessment_type,
            category=category,
            difficulty_level=difficulty_level,
            estimated_duration_minutes=estimated_duration_minutes,
            passing_score=passing_score,
            is_published=False
        )
        return assessment

    @staticmethod
    @transaction.atomic
    def add_question_to_assessment(
        assessment: Assessment,
        question_text: str,
        question_type: str,
        order: int,
        options: Optional[List[Dict[str, Any]]] = None,
        correct_answer: Optional[str] = None,
        points: int = 1,
        explanation: str = ""
    ) -> AssessmentQuestion:
        """Add a question to assessment"""
        question = AssessmentQuestion.objects.create(
            assessment=assessment,
            question_text=question_text,
            question_type=question_type,
            order=order,
            options=options or [],
            correct_answer=correct_answer or '',
            points=points,
            explanation=explanation
        )
        return question


class AssessmentSubmissionService:
    """Service for assessment submission and grading"""

    @staticmethod
    @transaction.atomic
    def start_assessment(user: User, assessment: Assessment) -> AssessmentSubmission:
        """
        Start an assessment submission.

        Args:
            user: User taking assessment
            assessment: Assessment to take

        Returns:
            AssessmentSubmission: Created submission
        """
        # Check for existing incomplete submission
        existing = AssessmentSubmission.objects.filter(
            user=user,
            assessment=assessment,
            status='in_progress',
            is_deleted=False
        ).first()

        if existing:
            return existing

        submission = AssessmentSubmission.objects.create(
            user=user,
            assessment=assessment,
            status='in_progress',
            started_at=timezone.now()
        )

        return submission

    @staticmethod
    @transaction.atomic
    def submit_assessment(
        submission: AssessmentSubmission,
        answers: Dict[str, Any]
    ) -> AssessmentSubmission:
        """
        Submit assessment answers.

        Args:
            submission: AssessmentSubmission instance
            answers: Dict mapping question_id to answer

        Returns:
            AssessmentSubmission: Updated submission with score
        """
        submission.answers = answers
        submission.submitted_at = timezone.now()
        submission.status = 'submitted'

        # Calculate score
        questions = submission.assessment.questions.filter(is_deleted=False)
        total_points = sum(q.points for q in questions)
        earned_points = 0

        for question in questions:
            user_answer = answers.get(str(question.id))

            if question.question_type in ['multiple_choice', 'true_false']:
                if user_answer == question.correct_answer:
                    earned_points += question.points
            # TODO: Add grading logic for other question types

        if total_points > 0:
            submission.score = int((earned_points / total_points) * 100)
        else:
            submission.score = 0

        submission.save()

        # Emit signal
        assessment_submitted.send(
            sender=AssessmentSubmission,
            instance=submission,
            user=submission.user
        )

        return submission

    @staticmethod
    def get_user_submissions(user: User) -> List[AssessmentSubmission]:
        """Get all submissions for user"""
        return list(AssessmentSubmission.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('assessment').order_by('-submitted_at'))

    @staticmethod
    def get_submission_by_id(submission_id: str) -> Optional[AssessmentSubmission]:
        """Get submission by ID"""
        try:
            return AssessmentSubmission.objects.select_related('assessment').get(
                id=submission_id,
                is_deleted=False
            )
        except AssessmentSubmission.DoesNotExist:
            return None


class AssessmentResultService:
    """Service for assessment result analysis"""

    @staticmethod
    @transaction.atomic
    def generate_assessment_result(
        submission: AssessmentSubmission
    ) -> AssessmentResult:
        """
        Generate AI-powered assessment result with analysis.

        Args:
            submission: Completed assessment submission

        Returns:
            AssessmentResult: Created result with AI insights
        """
        # Check for existing result
        existing = AssessmentResult.objects.filter(
            submission=submission,
            is_deleted=False
        ).first()

        if existing:
            return existing

        result = AssessmentResult.objects.create(
            user=submission.user,
            assessment=submission.assessment,
            submission=submission,
            overall_score=submission.score,
            processing_status='pending'  # Will be processed by AI async
        )

        # TODO: Trigger async AI analysis task
        # tasks.analyze_assessment_result.delay(result.id)

        # Emit signal
        assessment_completed.send(
            sender=AssessmentResult,
            instance=result,
            user=submission.user
        )

        return result

    @staticmethod
    def get_user_results(user: User) -> List[AssessmentResult]:
        """Get all assessment results for user"""
        return list(AssessmentResult.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('assessment', 'submission').order_by('-created_at'))

    @staticmethod
    def get_result_by_id(result_id: str) -> Optional[AssessmentResult]:
        """Get result by ID"""
        try:
            return AssessmentResult.objects.select_related(
                'assessment', 'submission'
            ).get(id=result_id, is_deleted=False)
        except AssessmentResult.DoesNotExist:
            return None

    @staticmethod
    def get_skill_strengths_weaknesses(user: User) -> Dict[str, Any]:
        """
        Analyze user's skill strengths and weaknesses across all assessments.

        Returns:
            Dict with strengths, weaknesses, and recommendations
        """
        results = AssessmentResult.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('assessment')

        strengths = []
        weaknesses = []

        for result in results:
            if result.overall_score >= 80:
                strengths.append({
                    'category': result.assessment.category,
                    'score': result.overall_score,
                    'level': result.skill_level
                })
            elif result.overall_score < 60:
                weaknesses.append({
                    'category': result.assessment.category,
                    'score': result.overall_score,
                    'level': result.skill_level
                })

        return {
            'strengths': strengths,
            'weaknesses': weaknesses,
            'total_assessments': results.count()
        }
