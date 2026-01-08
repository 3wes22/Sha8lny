"""
Progress Service Serializers

Implements serializers for progress tracking, course completions,
milestone achievements, and time logging.

SRS Reference: Implied by FR-12 (Progress Tracking)
"""

from rest_framework import serializers
from apps.progress.models import (
    UserProgress,
    CourseCompletion,
    MilestoneAchievement,
    TimeLog
)
from apps.courses.serializers import CourseListSerializer
from apps.roadmaps.serializers import RoadmapListSerializer


# ============================================================================
# USER PROGRESS SERIALIZERS
# ============================================================================

class UserProgressListSerializer(serializers.ModelSerializer):
    """Minimal progress info for list views."""
    roadmap_title = serializers.CharField(source='roadmap.title', read_only=True)
    completion_display = serializers.CharField(read_only=True)
    streak_display = serializers.CharField(read_only=True)
    hours_display = serializers.CharField(read_only=True)

    class Meta:
        model = UserProgress
        fields = [
            'id',
            'roadmap',
            'roadmap_title',
            'overall_completion_percentage',
            'completion_display',
            'phases_completed',
            'milestones_completed',
            'courses_completed',
            'current_streak_days',
            'streak_display',
            'total_learning_hours',
            'hours_display',
            'last_activity_date',
            'on_track',
        ]


class UserProgressSerializer(serializers.ModelSerializer):
    """Complete progress information."""
    roadmap = RoadmapListSerializer(read_only=True)
    completion_display = serializers.CharField(read_only=True)
    streak_display = serializers.CharField(read_only=True)
    hours_display = serializers.CharField(read_only=True)

    class Meta:
        model = UserProgress
        fields = [
            'id',
            'user',
            'roadmap',
            'overall_completion_percentage',
            'completion_display',
            'phases_completed',
            'milestones_completed',
            'courses_completed',
            'total_learning_hours',
            'hours_display',
            'current_streak_days',
            'longest_streak_days',
            'streak_display',
            'last_activity_date',
            'current_phase',
            'current_milestone',
            'average_hours_per_week',
            'on_track',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'overall_completion_percentage',
            'phases_completed',
            'milestones_completed',
            'courses_completed',
            'total_learning_hours',
            'current_streak_days',
            'longest_streak_days',
            'last_activity_date',
            'average_hours_per_week',
            'created_at',
            'updated_at',
        ]


# ============================================================================
# COURSE COMPLETION SERIALIZERS
# ============================================================================

class CourseCompletionListSerializer(serializers.ModelSerializer):
    """Minimal course completion info."""
    course_title = serializers.CharField(source='course.title', read_only=True)
    rating_display = serializers.CharField(read_only=True)

    class Meta:
        model = CourseCompletion
        fields = [
            'id',
            'course',
            'course_title',
            'started_at',
            'completed_at',
            'time_spent_hours',
            'completion_percentage',
            'user_rating',
            'rating_display',
            'has_certificate',
        ]


class CourseCompletionSerializer(serializers.ModelSerializer):
    """Complete course completion information."""
    course = CourseListSerializer(read_only=True)
    rating_display = serializers.CharField(read_only=True)
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model = CourseCompletion
        fields = [
            'id',
            'user',
            'course',
            'roadmap_course',
            'started_at',
            'completed_at',
            'time_spent_hours',
            'completion_percentage',
            'user_rating',
            'user_review',
            'would_recommend',
            'has_certificate',
            'certificate_url',
            'rating_display',
            'duration_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CourseCompletionCreateSerializer(serializers.Serializer):
    """Create course completion record."""
    course_id = serializers.UUIDField(required=True)
    roadmap_course_id = serializers.UUIDField(required=False, allow_null=True)
    started_at = serializers.DateTimeField(required=True)
    completed_at = serializers.DateTimeField(required=True)
    time_spent_hours = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0
    )
    user_rating = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=5
    )
    user_review = serializers.CharField(required=False, allow_blank=True)
    would_recommend = serializers.BooleanField(required=False, allow_null=True)
    certificate_url = serializers.URLField(required=False, allow_blank=True)

    def validate(self, data):
        """Validate completion dates."""
        if data['completed_at'] <= data['started_at']:
            raise serializers.ValidationError(
                "completed_at must be after started_at"
            )
        return data


class CourseReviewSerializer(serializers.Serializer):
    """Update course review."""
    user_rating = serializers.IntegerField(min_value=1, max_value=5)
    user_review = serializers.CharField(required=False, allow_blank=True)
    would_recommend = serializers.BooleanField(required=False)


# ============================================================================
# MILESTONE ACHIEVEMENT SERIALIZERS
# ============================================================================

class MilestoneAchievementListSerializer(serializers.ModelSerializer):
    """Minimal milestone achievement info."""
    milestone_title = serializers.CharField(source='milestone.title', read_only=True)
    completion_speed_display = serializers.CharField(read_only=True)

    class Meta:
        model = MilestoneAchievement
        fields = [
            'id',
            'milestone',
            'milestone_title',
            'achieved_at',
            'time_to_complete_days',
            'completion_speed_display',
            'badge_awarded',
            'badge_type',
        ]


class MilestoneAchievementSerializer(serializers.ModelSerializer):
    """Complete milestone achievement information."""
    completion_speed_display = serializers.CharField(read_only=True)

    class Meta:
        model = MilestoneAchievement
        fields = [
            'id',
            'user',
            'milestone',
            'achieved_at',
            'time_to_complete_days',
            'completion_speed_display',
            'badge_awarded',
            'badge_type',
            'created_at',
        ]
        read_only_fields = ['id', 'achieved_at', 'created_at']


# ============================================================================
# TIME LOG SERIALIZERS
# ============================================================================

class TimeLogListSerializer(serializers.ModelSerializer):
    """Minimal time log info."""
    activity_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    duration_display = serializers.CharField(read_only=True)

    class Meta:
        model = TimeLog
        fields = [
            'id',
            'activity_type',
            'activity_display',
            'started_at',
            'ended_at',
            'duration_minutes',
            'duration_display',
            'course',
            'roadmap',
        ]


class TimeLogSerializer(serializers.ModelSerializer):
    """Complete time log information."""
    duration_display = serializers.CharField(read_only=True)
    duration_hours = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = TimeLog
        fields = [
            'id',
            'user',
            'course',
            'roadmap',
            'started_at',
            'ended_at',
            'duration_minutes',
            'duration_display',
            'duration_hours',
            'activity_type',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class TimeLogCreateSerializer(serializers.Serializer):
    """Create time log entry."""
    course_id = serializers.UUIDField(required=False, allow_null=True)
    roadmap_id = serializers.UUIDField(required=False, allow_null=True)
    started_at = serializers.DateTimeField(required=True)
    ended_at = serializers.DateTimeField(required=True)
    duration_minutes = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=1440
    )
    activity_type = serializers.ChoiceField(
        choices=['course', 'practice', 'reading', 'project'],
        required=True
    )

    def validate(self, data):
        """Validate time log data."""
        if data['ended_at'] <= data['started_at']:
            raise serializers.ValidationError(
                "ended_at must be after started_at"
            )

        # Auto-calculate duration if not provided
        if 'duration_minutes' not in data:
            delta = data['ended_at'] - data['started_at']
            data['duration_minutes'] = max(1, int(delta.total_seconds() / 60))

        return data


# ============================================================================
# STATISTICS SERIALIZERS
# ============================================================================

class ProgressStatsSerializer(serializers.Serializer):
    """Progress statistics for dashboard."""
    total_learning_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_courses_completed = serializers.IntegerField()
    total_milestones_achieved = serializers.IntegerField()
    current_streak_days = serializers.IntegerField()
    longest_streak_days = serializers.IntegerField()
    roadmaps_in_progress = serializers.IntegerField()
    roadmaps_completed = serializers.IntegerField()
    average_daily_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    this_week_hours = serializers.DecimalField(max_digits=6, decimal_places=2)
    last_activity_date = serializers.DateField(allow_null=True)
