"""
Progress Module Models

Implements progress tracking for user learning journeys, including:
- UserProgress: Overall roadmap progress tracking
- CourseCompletion: Individual course completion tracking
- MilestoneAchievement: Milestone completion tracking
- TimeLog: Detailed time tracking by activity type
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.users.models import User
from apps.roadmaps.models import Roadmap, RoadmapPhase, RoadmapMilestone, RoadmapCourse
from apps.courses.models import Course


class UserProgressManager(models.Manager):
    """Custom manager for UserProgress model with optimized queries"""

    def with_related(self):
        """Prefetch related objects for API efficiency"""
        return self.select_related(
            'user',
            'roadmap',
            'current_phase',
            'current_milestone'
        )

    def for_user(self, user):
        """Get progress records for a specific user"""
        return self.filter(user=user, is_deleted=False)

    def active(self):
        """Get progress for active users (activity in last 30 days)"""
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        return self.filter(
            last_activity_date__gte=thirty_days_ago,
            is_deleted=False
        )

    def with_streaks(self):
        """Get users with active streaks"""
        return self.filter(current_streak_days__gt=0, is_deleted=False)


class UserProgress(BaseModel):
    """
    Tracks overall progress for a user on a specific roadmap.

    Includes completion percentages, streak tracking, time metrics,
    and current position in the roadmap hierarchy.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress_records',
        help_text="User whose progress is being tracked"
    )

    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        related_name='user_progress',
        help_text="Roadmap being tracked"
    )

    # Progress Metrics
    overall_completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall completion percentage (0-100)"
    )

    phases_completed = models.PositiveIntegerField(
        default=0,
        help_text="Number of phases completed"
    )

    milestones_completed = models.PositiveIntegerField(
        default=0,
        help_text="Number of milestones completed"
    )

    courses_completed = models.PositiveIntegerField(
        default=0,
        help_text="Number of courses completed"
    )

    # Time Tracking
    total_learning_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text="Total hours spent learning on this roadmap"
    )

    current_streak_days = models.PositiveIntegerField(
        default=0,
        help_text="Current consecutive days streak"
    )

    longest_streak_days = models.PositiveIntegerField(
        default=0,
        help_text="Longest streak achieved"
    )

    last_activity_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last learning activity"
    )

    # Current Position
    current_phase = models.ForeignKey(
        RoadmapPhase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        help_text="Current phase user is working on"
    )

    current_milestone = models.ForeignKey(
        RoadmapMilestone,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        help_text="Current milestone user is working on"
    )

    # Pace Tracking
    average_hours_per_week = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Average hours per week spent on this roadmap"
    )

    on_track = models.BooleanField(
        default=True,
        help_text="Whether user is on track to complete roadmap on time"
    )

    # Custom manager
    objects = UserProgressManager()

    class Meta:
        verbose_name = "User Progress"
        verbose_name_plural = "User Progress Records"
        ordering = ['-last_activity_date', '-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'roadmap'],
                condition=models.Q(is_deleted=False),
                name='unique_user_roadmap_progress'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-last_activity_date'], name='idx_prog_user_activity'),
            models.Index(fields=['roadmap', '-overall_completion_percentage'], name='idx_prog_roadmap_completion'),
            models.Index(fields=['-current_streak_days'], name='idx_prog_streak'),
            models.Index(fields=['on_track'], name='idx_prog_on_track'),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.roadmap.title} ({self.overall_completion_percentage}%)"

    @property
    def completion_display(self):
        """Display-friendly completion percentage"""
        return f"{self.overall_completion_percentage}%"

    @property
    def streak_display(self):
        """Display current streak with emoji"""
        if self.current_streak_days == 0:
            return "No streak"
        return f"{self.current_streak_days} days"

    @property
    def hours_display(self):
        """Display total hours in friendly format"""
        hours = float(self.total_learning_hours)
        if hours < 1:
            return f"{int(hours * 60)} minutes"
        return f"{hours:.1f} hours"


class CourseCompletion(BaseModel):
    """
    Tracks individual course completions by users.

    Includes time spent, user ratings/reviews, and certificate information.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='course_completions',
        help_text="User who completed the course"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='completions',
        help_text="Course that was completed"
    )

    roadmap_course = models.ForeignKey(
        RoadmapCourse,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completions',
        help_text="Associated roadmap course (if part of roadmap)"
    )

    # Completion Details
    started_at = models.DateTimeField(
        help_text="When user started the course"
    )

    completed_at = models.DateTimeField(
        help_text="When user completed the course"
    )

    time_spent_hours = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Total hours spent on this course"
    )

    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Completion percentage (default 100% for full completion)"
    )

    # User Feedback
    user_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User rating (1-5 stars)"
    )

    user_review = models.TextField(
        blank=True,
        help_text="User's written review of the course"
    )

    would_recommend = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether user would recommend this course"
    )

    # Certificate
    has_certificate = models.BooleanField(
        default=False,
        help_text="Whether user earned a certificate"
    )

    certificate_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text="URL to certificate (if available)"
    )

    class Meta:
        verbose_name = "Course Completion"
        verbose_name_plural = "Course Completions"
        ordering = ['-completed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'course'],
                condition=models.Q(is_deleted=False),
                name='unique_user_course_completion'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-completed_at'], name='idx_compl_user_date'),
            models.Index(fields=['course', '-completed_at'], name='idx_compl_course_date'),
            models.Index(fields=['roadmap_course'], name='idx_compl_roadmap_course'),
            models.Index(fields=['-user_rating'], name='idx_compl_rating'),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.completed_at.date()})"

    @property
    def rating_display(self):
        """Display rating with stars"""
        if not self.user_rating:
            return "No rating"
        return f"{'⭐' * self.user_rating} ({self.user_rating}/5)"

    @property
    def duration_display(self):
        """Display time from start to completion"""
        duration = self.completed_at - self.started_at
        days = duration.days
        if days == 0:
            return "Same day"
        elif days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''}"


class MilestoneAchievement(BaseModel):
    """
    Tracks milestone completions by users.

    Includes achievement date, time to complete, and badge information.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='milestone_achievements',
        help_text="User who achieved the milestone"
    )

    milestone = models.ForeignKey(
        RoadmapMilestone,
        on_delete=models.CASCADE,
        related_name='achievements',
        help_text="Milestone that was achieved"
    )

    achieved_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When milestone was achieved"
    )

    time_to_complete_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of days taken to complete this milestone"
    )

    # Gamification
    badge_awarded = models.BooleanField(
        default=False,
        help_text="Whether a badge was awarded for this achievement"
    )

    badge_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of badge awarded (e.g., 'Speed Demon', 'Perfectionist')"
    )

    class Meta:
        verbose_name = "Milestone Achievement"
        verbose_name_plural = "Milestone Achievements"
        ordering = ['-achieved_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'milestone'],
                condition=models.Q(is_deleted=False),
                name='unique_user_milestone_achievement'
            )
        ]
        indexes = [
            models.Index(fields=['user', '-achieved_at'], name='idx_achv_user_date'),
            models.Index(fields=['milestone', '-achieved_at'], name='idx_achv_milestone_date'),
            models.Index(fields=['badge_awarded'], name='idx_achv_badge'),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.milestone.title} ({self.achieved_at.date()})"

    @property
    def completion_speed_display(self):
        """Display completion speed in friendly format"""
        if not self.time_to_complete_days:
            return "Unknown"
        days = self.time_to_complete_days
        if days == 1:
            return "1 day"
        elif days < 7:
            return f"{days} days"
        elif days < 30:
            weeks = days // 7
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            months = days // 30
            return f"{months} month{'s' if months > 1 else ''}"


class TimeLog(BaseModel):
    """
    Tracks detailed time logs for user learning activities.

    Supports different activity types and can be associated with
    courses and/or roadmaps.
    """

    ACTIVITY_TYPES = [
        ('course', 'Course Learning'),
        ('practice', 'Practice/Exercises'),
        ('reading', 'Reading Documentation'),
        ('project', 'Project Work'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_logs',
        help_text="User who logged the time"
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_logs',
        help_text="Course associated with this time log (optional)"
    )

    roadmap = models.ForeignKey(
        Roadmap,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='time_logs',
        help_text="Roadmap associated with this time log (optional)"
    )

    # Time Details
    started_at = models.DateTimeField(
        help_text="When learning session started"
    )

    ended_at = models.DateTimeField(
        help_text="When learning session ended"
    )

    duration_minutes = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text="Duration in minutes (1-1440, max 24 hours)"
    )

    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        help_text="Type of learning activity"
    )

    class Meta:
        verbose_name = "Time Log"
        verbose_name_plural = "Time Logs"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at'], name='idx_tlog_user_started'),
            models.Index(fields=['course', '-started_at'], name='idx_tlog_course_started'),
            models.Index(fields=['roadmap', '-started_at'], name='idx_tlog_roadmap_started'),
            models.Index(fields=['activity_type'], name='idx_tlog_activity_type'),
            models.Index(fields=['user', 'started_at'], name='idx_tlog_user_date'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(ended_at__gt=models.F('started_at')),
                name='chk_timelog_chronology'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.get_activity_type_display()} ({self.duration_display})"

    @property
    def duration_display(self):
        """Display duration in friendly format"""
        if self.duration_minutes < 60:
            return f"{self.duration_minutes} min"
        hours = self.duration_minutes / 60
        if hours == int(hours):
            return f"{int(hours)} hr"
        return f"{hours:.1f} hr"

    @property
    def duration_hours(self):
        """Get duration in hours as decimal"""
        return round(self.duration_minutes / 60, 2)

    def save(self, *args, **kwargs):
        """Auto-calculate duration_minutes if not provided"""
        if not self.duration_minutes and self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            self.duration_minutes = max(1, int(delta.total_seconds() / 60))
        super().save(*args, **kwargs)
