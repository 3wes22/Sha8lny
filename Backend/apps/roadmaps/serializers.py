"""
Roadmaps Service Serializers

Implements serializers for personalized learning roadmap generation,
career path templates, and progress tracking.

SRS References:
- FR-9: Generate Personalized Roadmap
- FR-10: Assessment-Based Roadmap Generation
- FR-11: Course Association with Roadmaps
"""

from rest_framework import serializers
from decimal import Decimal
from apps.roadmaps.models import (
    RoadmapTemplate,
    Roadmap,
    RoadmapPhase,
    RoadmapMilestone,
    RoadmapCourse
)
from apps.courses.serializers import CourseListSerializer
from apps.users.serializers import SkillSerializer


# ============================================================================
# ROADMAP TEMPLATE SERIALIZERS
# ============================================================================

class RoadmapTemplateListSerializer(serializers.ModelSerializer):
    """Minimal template info for list views."""

    class Meta:
        model = RoadmapTemplate
        fields = [
            'id',
            'title',
            'short_description',
            'target_career',
            'career_level',
            'estimated_duration_weeks',
            'difficulty_level',
            'usage_count',
        ]


class RoadmapTemplateSerializer(serializers.ModelSerializer):
    """Complete roadmap template information."""

    class Meta:
        model = RoadmapTemplate
        fields = [
            'id',
            'title',
            'slug',
            'description',
            'short_description',
            'target_career',
            'career_level',
            'estimated_duration_weeks',
            'difficulty_level',
            'prerequisites',
            'learning_outcomes',
            'required_skills',
            'is_published',
            'usage_count',
            'metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'usage_count', 'created_at']


# ============================================================================
# ROADMAP COURSE SERIALIZERS
# ============================================================================

class RoadmapCourseSerializer(serializers.ModelSerializer):
    """Course recommendation within a milestone."""
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = RoadmapCourse
        fields = [
            'id',
            'course',
            'order',
            'is_primary',
            'match_score',
            'recommendation_reason',
            'is_enrolled',
            'is_completed',
            'enrolled_at',
            'completed_at',
        ]


# ============================================================================
# ROADMAP MILESTONE SERIALIZERS
# ============================================================================

class RoadmapMilestoneListSerializer(serializers.ModelSerializer):
    """Minimal milestone info for nested views."""

    class Meta:
        model = RoadmapMilestone
        fields = [
            'id',
            'title',
            'milestone_type',
            'order',
            'status',
            'is_required',
            'estimated_duration_hours',
        ]


class RoadmapMilestoneSerializer(serializers.ModelSerializer):
    """Complete milestone information with courses."""
    courses = RoadmapCourseSerializer(many=True, read_only=True)
    total_courses = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoadmapMilestone
        fields = [
            'id',
            'title',
            'description',
            'milestone_type',
            'order',
            'estimated_duration_hours',
            'status',
            'is_required',
            'skills',
            'resources',
            'completed_at',
            'courses',
            'total_courses',
        ]


# ============================================================================
# ROADMAP PHASE SERIALIZERS
# ============================================================================

class RoadmapPhaseListSerializer(serializers.ModelSerializer):
    """Minimal phase info for nested views."""
    completed_milestones = serializers.IntegerField(read_only=True)
    total_milestones = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoadmapPhase
        fields = [
            'id',
            'title',
            'order',
            'status',
            'completion_percentage',
            'estimated_duration_weeks',
            'completed_milestones',
            'total_milestones',
        ]


class RoadmapPhaseSerializer(serializers.ModelSerializer):
    """Complete phase information with milestones."""
    milestones = RoadmapMilestoneSerializer(many=True, read_only=True)
    completed_milestones = serializers.IntegerField(read_only=True)
    total_milestones = serializers.IntegerField(read_only=True)

    class Meta:
        model = RoadmapPhase
        fields = [
            'id',
            'title',
            'description',
            'order',
            'estimated_duration_weeks',
            'status',
            'completion_percentage',
            'started_at',
            'completed_at',
            'objectives',
            'milestones',
            'completed_milestones',
            'total_milestones',
        ]


# ============================================================================
# ROADMAP SERIALIZERS
# ============================================================================

class RoadmapListSerializer(serializers.ModelSerializer):
    """Minimal roadmap info for list views."""

    class Meta:
        model = Roadmap
        fields = [
            'id',
            'title',
            'target_career',
            'status',
            'completion_percentage',
            'estimated_duration_weeks',
            'ai_processing_status',
            'created_at',
        ]


class RoadmapSerializer(serializers.ModelSerializer):
    """Complete roadmap information."""
    phases = RoadmapPhaseListSerializer(many=True, read_only=True)
    total_phases = serializers.IntegerField(read_only=True)
    completed_phases = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = Roadmap
        fields = [
            'id',
            'template',
            'assessment',
            'title',
            'description',
            'target_career',
            'current_level',
            'target_level',
            'estimated_duration_weeks',
            'weekly_hours_commitment',
            'status',
            'completion_percentage',
            'started_at',
            'completed_at',
            'ai_processing_status',
            'ai_processed_at',
            'ai_insights',
            'llm_model_used',
            'llm_prompt_tokens',
            'llm_completion_tokens',
            'processing_time_seconds',
            'metadata',
            'phases',
            'total_phases',
            'completed_phases',
            'is_active',
            'is_complete',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'ai_processing_status',
            'ai_processed_at',
            'llm_model_used',
            'llm_prompt_tokens',
            'llm_completion_tokens',
            'processing_time_seconds',
            'created_at',
            'updated_at',
        ]


class RoadmapDetailSerializer(RoadmapSerializer):
    """Full roadmap details with complete hierarchy."""
    phases = RoadmapPhaseSerializer(many=True, read_only=True)


# ============================================================================
# ROADMAP CREATION SERIALIZERS
# ============================================================================

class RoadmapCreateFromTemplateSerializer(serializers.Serializer):
    """
    Create roadmap from template.

    SRS FR-9: Use pre-built templates as starting point
    """
    template_id = serializers.UUIDField(required=True)
    weekly_hours_commitment = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=168
    )
    customizations = serializers.JSONField(required=False, default=dict)

    def validate_template_id(self, value):
        """Validate template exists and is published."""
        from apps.roadmaps.services import RoadmapTemplateService
        template = RoadmapTemplateService.get_template_by_id(str(value))
        if not template:
            raise serializers.ValidationError("Template not found")
        if not template.is_published:
            raise serializers.ValidationError("Template is not available")
        return value


class RoadmapCreateAISerializer(serializers.Serializer):
    """
    Generate AI-powered personalized roadmap.

    SRS FR-9: Generate Personalized Roadmap
    SRS FR-10: Assessment-Based Roadmap Generation
    """
    assessment_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="Assessment result to base roadmap on"
    )
    target_career = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Target job title/career goal"
    )
    current_level = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Current skill level"
    )
    target_level = serializers.CharField(
        required=True,
        max_length=255,
        help_text="Target skill level to achieve"
    )
    weekly_hours_commitment = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=168,
        help_text="Weekly hours to dedicate"
    )

    def validate_assessment_id(self, value):
        """Validate assessment exists and belongs to user."""
        if value is None:
            return value

        from apps.assessments.models import AssessmentResult
        try:
            assessment = AssessmentResult.objects.get(
                id=value,
                assessment__user=self.context['request'].user,
                is_deleted=False
            )
            return value
        except AssessmentResult.DoesNotExist:
            raise serializers.ValidationError("Assessment result not found")


class RoadmapUpdateSerializer(serializers.ModelSerializer):
    """Update roadmap fields."""

    class Meta:
        model = Roadmap
        fields = [
            'title',
            'description',
            'target_career',
            'current_level',
            'target_level',
            'weekly_hours_commitment',
            'status',
        ]


class RoadmapProgressUpdateSerializer(serializers.Serializer):
    """
    Update roadmap progress.

    SRS Appendix B: PUT /roadmap/progress
    """
    phase_id = serializers.UUIDField(required=False)
    milestone_id = serializers.UUIDField(required=False)
    status = serializers.ChoiceField(
        choices=['not_started', 'in_progress', 'completed', 'skipped'],
        required=True
    )

    def validate(self, data):
        """Ensure either phase_id or milestone_id is provided."""
        if not data.get('phase_id') and not data.get('milestone_id'):
            raise serializers.ValidationError(
                "Either phase_id or milestone_id must be provided"
            )
        if data.get('phase_id') and data.get('milestone_id'):
            raise serializers.ValidationError(
                "Provide only one of phase_id or milestone_id, not both"
            )
        return data


# ============================================================================
# STATISTICS SERIALIZERS
# ============================================================================

class RoadmapStatsSerializer(serializers.Serializer):
    """Roadmap statistics."""
    total_phases = serializers.IntegerField()
    completed_phases = serializers.IntegerField()
    total_milestones = serializers.IntegerField()
    completed_milestones = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    estimated_total_hours = serializers.FloatField()
    completion_percentage = serializers.FloatField()
