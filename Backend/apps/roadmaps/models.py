"""
Roadmap Service Models

Handles personalized learning roadmap generation, career path templates,
and progress-based roadmap adjustments for the Sha8alny platform.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel


class RoadmapTemplate(BaseModel):
    """
    Pre-built career path templates for common career goals.

    Templates serve as starting points for AI-personalized roadmaps.
    Examples: "Backend Developer", "Data Scientist", "DevOps Engineer"
    """

    # Career levels
    ENTRY_LEVEL = 'entry_level'
    MID_LEVEL = 'mid_level'
    SENIOR_LEVEL = 'senior_level'
    LEAD_LEVEL = 'lead_level'

    LEVEL_CHOICES = [
        (ENTRY_LEVEL, 'Entry Level'),
        (MID_LEVEL, 'Mid Level'),
        (SENIOR_LEVEL, 'Senior Level'),
        (LEAD_LEVEL, 'Lead/Principal'),
    ]

    title = models.CharField(
        max_length=255,
        unique=True,
        help_text="Template name (e.g., 'Backend Developer Roadmap')"
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-friendly identifier"
    )

    description = models.TextField(
        help_text="Detailed description of this career path"
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief one-liner description"
    )

    target_career = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Target job title (e.g., 'Backend Developer', 'Data Scientist')"
    )

    career_level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default=ENTRY_LEVEL,
        help_text="Target career level for this roadmap"
    )

    estimated_duration_weeks = models.PositiveIntegerField(
        help_text="Estimated total duration in weeks"
    )

    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='beginner',
        help_text="Overall difficulty level"
    )

    # Prerequisites (stored as JSONB array)
    prerequisites = models.JSONField(
        default=list,
        blank=True,
        help_text="List of prerequisites: [prerequisite1, prerequisite2, ...]"
    )
    # Example: ["Basic programming knowledge", "Familiarity with command line"]

    # Learning outcomes (stored as JSONB array)
    learning_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text="Expected outcomes: [outcome1, outcome2, ...]"
    )
    # Example: ["Build production-ready APIs", "Master database design"]

    # Skill UUIDs (references to users.Skill)
    required_skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of required skill UUIDs: [uuid1, uuid2, ...]"
    )

    is_published = models.BooleanField(
        default=False,
        help_text="Whether this template is available for users"
    )

    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times this template was used"
    )

    # Template metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional template data (tags, categories, industry, etc.)"
    )
    # Example: {
    #     "tags": ["backend", "api", "python"],
    #     "industry": "Technology",
    #     "salary_range": "60k-120k"
    # }

    class Meta:
        verbose_name = "Roadmap Template"
        verbose_name_plural = "Roadmap Templates"
        ordering = ['-usage_count', 'title']
        indexes = [
            models.Index(fields=['target_career'], name='idx_template_career'),
            models.Index(fields=['career_level'], name='idx_template_level'),
            models.Index(fields=['is_published'], name='idx_template_published'),
            models.Index(fields=['-usage_count'], name='idx_template_usage'),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_career_level_display()})"

    def __repr__(self):
        return f"<RoadmapTemplate: {self.title}>"

    @property
    def required_skill_objects(self):
        """Get Skill objects from UUIDs"""
        if not self.required_skills:
            return []
        from apps.users.models import Skill
        return Skill.objects.filter(id__in=self.required_skills)


class RoadmapManager(models.Manager):
    """Custom manager for Roadmap model with optimized queries"""

    def with_hierarchy(self):
        """Prefetch full roadmap hierarchy for API efficiency"""
        return self.prefetch_related(
            'phases',
            'phases__milestones',
            'phases__milestones__courses'
        )

    def for_user(self, user):
        """Get roadmaps for a specific user"""
        return self.filter(user=user, is_deleted=False)

    def active(self):
        """Get active roadmaps only"""
        return self.filter(
            status__in=['active', 'in_progress'],
            is_deleted=False
        )

    def completed(self):
        """Get completed roadmaps"""
        return self.filter(status='completed', is_deleted=False)


class Roadmap(BaseModel):
    """
    Personalized learning roadmap for a specific user.

    Generated by AI based on user's assessment results, goals, and preferences.
    Can be based on a RoadmapTemplate or fully custom.
    """

    # Roadmap status
    DRAFT = 'draft'
    ACTIVE = 'active'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    PAUSED = 'paused'
    ARCHIVED = 'archived'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (ACTIVE, 'Active'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (PAUSED, 'Paused'),
        (ARCHIVED, 'Archived'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='roadmaps',
        help_text="User who owns this roadmap"
    )

    template = models.ForeignKey(
        RoadmapTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roadmaps',
        help_text="Template this roadmap was based on (if any)"
    )

    assessment = models.ForeignKey(
        'assessments.AssessmentResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roadmaps',
        help_text="Assessment result that triggered this roadmap generation"
    )

    title = models.CharField(
        max_length=255,
        help_text="Roadmap title (personalized for the user)"
    )

    description = models.TextField(
        blank=True,
        help_text="AI-generated description tailored to user's needs"
    )

    target_career = models.CharField(
        max_length=255,
        help_text="User's target job title/career goal"
    )

    current_level = models.CharField(
        max_length=255,
        blank=True,
        help_text="User's current skill level/position"
    )

    target_level = models.CharField(
        max_length=255,
        help_text="Target skill level/position to achieve"
    )

    estimated_duration_weeks = models.PositiveIntegerField(
        help_text="AI-estimated duration based on user's pace and commitment"
    )

    weekly_hours_commitment = models.PositiveIntegerField(
        default=10,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        help_text="Expected weekly hours user will dedicate (1-168)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT,
        db_index=True,
        help_text="Current roadmap status"
    )

    # Progress tracking
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text="Overall completion percentage (0-100)"
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user started following this roadmap"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user completed this roadmap"
    )

    # AI generation tracking
    ai_processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Status of AI roadmap generation"
    )

    ai_processed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When AI processing completed"
    )

    ai_processing_error = models.TextField(
        blank=True,
        help_text="Error message if AI processing failed"
    )

    llm_model_used = models.CharField(
        max_length=100,
        blank=True,
        help_text="LLM model used for generation (e.g., 'gpt-4', 'claude-3')"
    )

    llm_prompt_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Number of prompt tokens used"
    )

    llm_completion_tokens = models.PositiveIntegerField(
        default=0,
        help_text="Number of completion tokens used"
    )

    processing_time_seconds = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Time taken for AI processing in seconds"
    )

    # AI recommendations and insights
    ai_insights = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI-generated insights about user's learning path"
    )
    # Example: {
    #     "strengths": ["Strong Python skills", "Good problem-solving"],
    #     "gaps": ["Limited backend experience", "No cloud knowledge"],
    #     "recommendations": ["Focus on FastAPI first", "Start with AWS basics"]
    # }

    # Roadmap metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional roadmap data (preferences, adjustments, etc.)"
    )

    # Custom manager
    objects = RoadmapManager()

    class Meta:
        verbose_name = "Roadmap"
        verbose_name_plural = "Roadmaps"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='idx_roadmap_user'),
            models.Index(fields=['status'], name='idx_roadmap_status'),
            models.Index(fields=['target_career'], name='idx_roadmap_career'),
            models.Index(fields=['-created_at'], name='idx_roadmap_created'),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.email}"

    def __repr__(self):
        return f"<Roadmap: {self.title} ({self.get_status_display()})>"

    @property
    def is_active(self):
        """Check if roadmap is currently active"""
        return self.status in [self.ACTIVE, self.IN_PROGRESS]

    @property
    def is_complete(self):
        """Check if roadmap is completed"""
        return self.status == self.COMPLETED or self.completion_percentage >= Decimal('100.00')

    @property
    def total_phases(self):
        """Get total number of phases"""
        return self.phases.count()

    @property
    def completed_phases(self):
        """Get number of completed phases"""
        return self.phases.filter(status='completed').count()


class RoadmapPhase(BaseModel):
    """
    A major phase/stage in a learning roadmap.

    Each roadmap consists of multiple sequential phases.
    Example: "Fundamentals" → "Backend Development" → "Advanced Topics"
    """

    # Phase status
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (SKIPPED, 'Skipped'),
    ]

    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name='phases',
        help_text="Roadmap this phase belongs to"
    )

    title = models.CharField(
        max_length=255,
        help_text="Phase title (e.g., 'Backend Fundamentals')"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of this phase"
    )

    order = models.PositiveIntegerField(
        help_text="Sequential order of this phase in the roadmap"
    )

    estimated_duration_weeks = models.PositiveIntegerField(
        help_text="Estimated duration for this phase in weeks"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=NOT_STARTED,
        help_text="Current phase status"
    )

    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text="Phase completion percentage (0-100)"
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user started this phase"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user completed this phase"
    )

    # Learning objectives
    objectives = models.JSONField(
        default=list,
        blank=True,
        help_text="Learning objectives for this phase: [objective1, objective2, ...]"
    )

    class Meta:
        verbose_name = "Roadmap Phase"
        verbose_name_plural = "Roadmap Phases"
        ordering = ['roadmap', 'order']
        unique_together = [['roadmap', 'order']]
        indexes = [
            models.Index(fields=['roadmap', 'order'], name='idx_phase_roadmap_order'),
            models.Index(fields=['status'], name='idx_phase_status'),
        ]

    def __str__(self):
        return f"{self.roadmap.title} - Phase {self.order}: {self.title}"

    def __repr__(self):
        return f"<RoadmapPhase: {self.title} (Order {self.order})>"

    @property
    def is_complete(self):
        """Check if phase is completed"""
        return self.status == self.COMPLETED

    @property
    def total_milestones(self):
        """Get total number of milestones"""
        return self.milestones.count()

    @property
    def completed_milestones(self):
        """Get number of completed milestones"""
        return self.milestones.filter(status='completed').count()


class RoadmapMilestone(BaseModel):
    """
    A specific milestone/checkpoint within a roadmap phase.

    Each phase contains multiple milestones representing concrete learning goals.
    Example: "Complete Python basics course", "Build a REST API project"
    """

    # Milestone types
    COURSE = 'course'
    PROJECT = 'project'
    READING = 'reading'
    PRACTICE = 'practice'
    ASSESSMENT = 'assessment'

    TYPE_CHOICES = [
        (COURSE, 'Course/Tutorial'),
        (PROJECT, 'Project/Practice'),
        (READING, 'Reading/Documentation'),
        (PRACTICE, 'Coding Practice'),
        (ASSESSMENT, 'Assessment/Quiz'),
    ]

    # Milestone status
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    SKIPPED = 'skipped'

    STATUS_CHOICES = [
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
        (SKIPPED, 'Skipped'),
    ]

    phase = models.ForeignKey(
        RoadmapPhase,
        on_delete=models.CASCADE,
        related_name='milestones',
        help_text="Phase this milestone belongs to"
    )

    title = models.CharField(
        max_length=500,
        help_text="Milestone title/description"
    )

    description = models.TextField(
        blank=True,
        help_text="Detailed description of what to achieve"
    )

    milestone_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=COURSE,
        help_text="Type of milestone activity"
    )

    order = models.PositiveIntegerField(
        help_text="Sequential order within the phase"
    )

    estimated_duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Estimated time to complete this milestone (hours)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=NOT_STARTED,
        help_text="Current milestone status"
    )

    is_required = models.BooleanField(
        default=True,
        help_text="Whether this milestone is required or optional"
    )

    # Skill UUIDs that will be gained from this milestone
    skills = models.JSONField(
        default=list,
        blank=True,
        help_text="List of skill UUIDs learned: [uuid1, uuid2, ...]"
    )

    # Resources and links
    resources = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional resources: [{title, url, type}, ...]"
    )
    # Example: [
    #     {"title": "Python Documentation", "url": "https://...", "type": "docs"},
    #     {"title": "Tutorial Video", "url": "https://...", "type": "video"}
    # ]

    completed_from_assessment = models.BooleanField(
        default=False,
        help_text="True when this milestone was marked complete from the user's "
                  "assessment baseline (already-mastered), not finished in-plan",
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user completed this milestone"
    )

    class Meta:
        verbose_name = "Roadmap Milestone"
        verbose_name_plural = "Roadmap Milestones"
        ordering = ['phase', 'order']
        unique_together = [['phase', 'order']]
        indexes = [
            models.Index(fields=['phase', 'order'], name='idx_milestone_phase_order'),
            models.Index(fields=['status'], name='idx_milestone_status'),
            models.Index(fields=['milestone_type'], name='idx_milestone_type'),
        ]

    def __str__(self):
        return f"{self.phase.title} - Milestone {self.order}: {self.title}"

    def __repr__(self):
        return f"<RoadmapMilestone: {self.title}>"

    @property
    def is_complete(self):
        """Check if milestone is completed"""
        return self.status == self.COMPLETED

    @property
    def skill_objects(self):
        """Get Skill objects from UUIDs"""
        if not self.skills:
            return []
        from apps.users.models import Skill
        return Skill.objects.filter(id__in=self.skills)

    @property
    def total_courses(self):
        """Get total number of recommended courses"""
        return self.courses.count()


class RoadmapCourse(BaseModel):
    """
    Links recommended courses to roadmap milestones.

    THIS MODEL BENEFITS FROM CLEAN COURSE FK - NO WORKAROUNDS!
    Each milestone can have multiple recommended courses.
    """

    milestone = models.ForeignKey(
        RoadmapMilestone,
        on_delete=models.CASCADE,
        related_name='courses',
        help_text="Milestone this course is recommended for"
    )

    # CLEAN FK TO COURSE MODEL - NO TEMPORARY FIELDS NEEDED!
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='roadmap_milestones',
        help_text="Recommended course from Course model"
    )

    order = models.PositiveIntegerField(
        default=1,
        help_text="Order of recommendation (1 = highest priority)"
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the primary recommended course for this milestone"
    )

    match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        help_text="AI-calculated match score (0-100) for this recommendation"
    )

    recommendation_reason = models.TextField(
        blank=True,
        help_text="AI-generated explanation of why this course is recommended"
    )

    # User interaction tracking
    is_enrolled = models.BooleanField(
        default=False,
        help_text="Whether user has enrolled in this course"
    )

    is_completed = models.BooleanField(
        default=False,
        help_text="Whether user has completed this course"
    )

    enrolled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user enrolled in this course"
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user completed this course"
    )

    class Meta:
        verbose_name = "Roadmap Course"
        verbose_name_plural = "Roadmap Courses"
        ordering = ['milestone', 'order', '-is_primary', '-match_score']
        unique_together = [['milestone', 'course']]
        indexes = [
            models.Index(fields=['milestone'], name='idx_roadmapcourse_milestone'),
            models.Index(fields=['course'], name='idx_roadmapcourse_course'),
            models.Index(fields=['is_primary'], name='idx_roadmapcourse_primary'),
            models.Index(fields=['-match_score'], name='idx_roadmapcourse_score'),
        ]

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.milestone.title} → {self.course.title}{primary}"

    def __repr__(self):
        return f"<RoadmapCourse: {self.course.title} for {self.milestone.title}>"

    @property
    def is_high_match(self):
        """Check if match score is high (80+)"""
        return self.match_score >= Decimal('80.00')
