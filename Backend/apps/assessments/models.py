"""
Assessment Service models for Sha8alny platform.

Handles career assessments, skill evaluations, and AI-powered analysis.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from apps.core.models import BaseModel


class Assessment(BaseModel):
    """
    Career assessment instance.

    Stores assessment questions, user responses, and AI processing status.
    Uses JSONB for flexible question/response structures.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assessments',
        help_text=_('User taking the assessment')
    )

    ASSESSMENT_TYPE_CHOICES = [
        ('skills', _('Skills Assessment')),
        ('career_interests', _('Career Interests')),
        ('personality', _('Personality Assessment')),
        ('learning_style', _('Learning Style')),
        ('comprehensive', _('Comprehensive Assessment')),
    ]

    assessment_type = models.CharField(
        max_length=100,
        choices=ASSESSMENT_TYPE_CHOICES,
        db_index=True,
        help_text=_('Type of assessment')
    )

    target_career = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_('Selected target career path for this assessment')
    )

    # Questions structure: JSONB for flexibility
    # Example: [{"id": 1, "question": "...", "type": "multiple_choice", "options": [...]}]
    questions = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Assessment questions in structured format')
    )

    # Responses structure: JSONB for flexible response types
    # Example: [{"question_id": 1, "answer": "...", "timestamp": "..."}]
    responses = models.JSONField(
        default=list,
        blank=True,
        help_text=_('User responses to assessment questions')
    )

    # AI Processing
    AI_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
    ]

    ai_processing_status = models.CharField(
        max_length=50,
        choices=AI_STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text=_('AI processing status for analysis')
    )

    ai_processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When AI processing completed')
    )

    ai_task_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Celery task ID for question generation or evaluation')
    )

    ai_trace_id = models.CharField(
        max_length=64,
        blank=True,
        help_text=_('Trace ID for the latest AI invocation')
    )

    ai_processing_error = models.TextField(
        blank=True,
        null=True,
        help_text=_('Error message if AI processing failed')
    )

    # Assessment Status
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('abandoned', _('Abandoned')),
    ]

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text=_('Assessment completion status')
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When user started the assessment')
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text=_('When user completed the assessment')
    )

    # Progress tracking
    total_questions = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Total number of questions')
    )

    answered_questions = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Number of answered questions')
    )

    # Time tracking
    time_spent_seconds = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Total time spent on assessment in seconds')
    )

    class Meta:
        db_table = 'assessments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='idx_assessments_user'),
            models.Index(fields=['assessment_type'], name='idx_assessments_type'),
            models.Index(fields=['status'], name='idx_assessments_status'),
            models.Index(fields=['ai_processing_status'], name='idx_assessments_ai_status'),
            models.Index(fields=['-completed_at'], name='idx_assessments_completed'),
            models.Index(fields=['user', 'assessment_type'], name='idx_assessments_user_type'),
        ]
        verbose_name = _('Assessment')
        verbose_name_plural = _('Assessments')

    def __str__(self):
        """String representation using user and type."""
        return f'{self.user.username} - {self.get_assessment_type_display()}'

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Assessment id={self.id} user={self.user.username} type={self.assessment_type}>'

    @property
    def completion_percentage(self):
        """Calculate assessment completion percentage."""
        if self.total_questions == 0:
            return 0
        return round((self.answered_questions / self.total_questions) * 100, 2)

    @property
    def is_complete(self):
        """Check if assessment is completed."""
        return self.status == 'completed'

    @property
    def has_result(self):
        """Check if assessment has a result."""
        return hasattr(self, 'result') and self.result is not None


class AssessmentResult(BaseModel):
    """
    AI-analyzed results from career assessment.

    Stores skill scores, career recommendations, and AI-generated insights.
    OneToOne relationship with Assessment.
    """

    assessment = models.OneToOneField(
        Assessment,
        on_delete=models.CASCADE,
        related_name='result',
        help_text=_('Assessment this result belongs to')
    )

    # Overall Score
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Overall assessment score (0-100)')
    )

    # Skill Analysis - JSONB for flexible structure
    # Example: {"technical": {"python": 85, "javascript": 70}, "soft": {"communication": 90}}
    skill_scores = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Detailed skill scores by category')
    )

    # Strengths and Weaknesses
    # Example: ["Strong analytical thinking", "Good problem-solving"]
    strengths = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Identified strengths from assessment')
    )

    # Example: ["Needs improvement in public speaking", "Time management"]
    areas_for_improvement = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Areas needing improvement')
    )

    # Career Recommendations - JSONB
    # Example: [{"title": "Data Scientist", "match_score": 92, "reasoning": "..."}]
    recommended_careers = models.JSONField(
        default=list,
        blank=True,
        help_text=_('AI-recommended career paths')
    )

    # Learning Recommendations - JSONB
    # Example: [{"skill": "Python", "priority": "high", "resources": [...]}]
    recommended_learning_paths = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Recommended skills to learn')
    )

    # AI Insights
    ai_insights = models.TextField(
        blank=True,
        help_text=_('Natural language AI-generated insights')
    )

    ai_confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True,
        help_text=_('AI confidence in analysis (0-100)')
    )

    # LLM Processing Details
    llm_model_used = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('LLM model used for analysis (e.g., gpt-4, claude-3)')
    )

    llm_prompt_tokens = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Number of prompt tokens used')
    )

    llm_completion_tokens = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Number of completion tokens used')
    )

    processing_time_seconds = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Time taken for AI processing in seconds')
    )

    # Metadata
    version = models.CharField(
        max_length=50,
        default='1.0',
        help_text=_('Assessment algorithm version')
    )

    is_shared = models.BooleanField(
        default=False,
        help_text=_('Whether user has shared this result')
    )

    class Meta:
        db_table = 'assessment_results'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assessment'], name='idx_results_assessment'),
            models.Index(fields=['overall_score'], name='idx_results_score'),
            models.Index(fields=['-created_at'], name='idx_results_created'),
        ]
        verbose_name = _('Assessment Result')
        verbose_name_plural = _('Assessment Results')

    def __str__(self):
        """String representation using assessment and score."""
        return f'Result for {self.assessment.user.username} - {self.overall_score}%'

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<AssessmentResult id={self.id} score={self.overall_score}>'

    @property
    def total_tokens_used(self):
        """Calculate total LLM tokens used."""
        prompt = self.llm_prompt_tokens or 0
        completion = self.llm_completion_tokens or 0
        return prompt + completion

    @property
    def top_skills(self):
        """Get top 5 skills from skill_scores."""
        if not self.skill_scores:
            return []

        # Flatten nested skill scores
        all_skills = []
        for category, skills in self.skill_scores.items():
            if isinstance(skills, dict):
                for skill_name, score in skills.items():
                    all_skills.append({'skill': skill_name, 'score': score, 'category': category})

        # Sort by score and return top 5
        return sorted(all_skills, key=lambda x: x['score'], reverse=True)[:5]
