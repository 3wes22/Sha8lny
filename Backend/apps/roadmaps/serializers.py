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
    node_type = serializers.SerializerMethodField()
    estimated_effort = serializers.SerializerMethodField()
    next_action = serializers.SerializerMethodField()

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
            'node_type',
            'estimated_effort',
            'next_action',
        ]

    def get_node_type(self, obj):
        return 'milestone'

    def get_estimated_effort(self, obj):
        if obj.estimated_duration_hours:
            return f"{obj.estimated_duration_hours} hours"
        return None

    def get_next_action(self, obj):
        if obj.status == RoadmapMilestone.COMPLETED:
            return "Use this milestone as reference while moving to the next node."
        if obj.status == RoadmapMilestone.IN_PROGRESS:
            return "Finish the active courses and mark this milestone complete."
        return "Start this milestone when you reach it in your roadmap."


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
    node_type = serializers.SerializerMethodField()
    estimated_effort = serializers.SerializerMethodField()
    next_action = serializers.SerializerMethodField()

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
            'node_type',
            'estimated_effort',
            'next_action',
        ]

    def get_node_type(self, obj):
        return 'phase'

    def get_estimated_effort(self, obj):
        if obj.estimated_duration_weeks:
            return f"{obj.estimated_duration_weeks} weeks"
        return None

    def get_next_action(self, obj):
        if obj.status == RoadmapPhase.COMPLETED:
            return "Review the completed outcomes and continue to the next phase."
        if obj.status == RoadmapPhase.IN_PROGRESS:
            return "Keep advancing the active milestones inside this phase."
        return "Activate this phase when the previous phase is complete."


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
    presentation_mode = serializers.SerializerMethodField()
    current_focus_node_id = serializers.SerializerMethodField()
    journey_summary = serializers.SerializerMethodField()
    journey_nodes = serializers.SerializerMethodField()
    ai_metadata = serializers.SerializerMethodField()

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
            'ai_metadata',
            'phases',
            'total_phases',
            'completed_phases',
            'is_active',
            'is_complete',
            'presentation_mode',
            'current_focus_node_id',
            'journey_summary',
            'journey_nodes',
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

    def _focus_target(self, obj):
        phases = list(obj.phases.all().order_by('order'))
        for phase in phases:
            milestones = list(phase.milestones.all().order_by('order'))
            for milestone in milestones:
                if milestone.status in [RoadmapMilestone.NOT_STARTED, RoadmapMilestone.IN_PROGRESS]:
                    return milestone
            if phase.status in [RoadmapPhase.NOT_STARTED, RoadmapPhase.IN_PROGRESS]:
                return phase
        return phases[0] if phases else None

    def get_presentation_mode(self, obj):
        return 'atlas'

    def get_current_focus_node_id(self, obj):
        focus = self._focus_target(obj)
        return str(focus.id) if focus else None

    def get_journey_summary(self, obj):
        focus = self._focus_target(obj)
        if focus is None:
            return {
                'focus_label': 'No roadmap phases yet',
                'next_action_title': 'Create a roadmap structure',
                'next_action_summary': 'Start by generating or selecting a roadmap template.',
                'next_action_type': 'roadmap',
                'next_action_id': None,
                'completion_ratio': float(obj.completion_percentage or 0),
            }

        is_milestone = isinstance(focus, RoadmapMilestone)
        next_action_type = 'milestone' if is_milestone else 'phase'

        return {
            'focus_label': 'Current focus',
            'next_action_title': focus.title,
            'next_action_summary': (
                f"Continue the active milestone in {focus.phase.title}."
                if is_milestone and focus.status == RoadmapMilestone.IN_PROGRESS
                else f"Unlock or begin {focus.title} next."
            ),
            'next_action_type': next_action_type,
            'next_action_id': str(focus.id),
            'completion_ratio': float(obj.completion_percentage or 0),
        }

    def get_journey_nodes(self, obj):
        nodes = []
        for phase in obj.phases.all().order_by('order'):
            phase_node = {
                'id': str(phase.id),
                'node_type': 'phase',
                'title': phase.title,
                'status': 'completed' if phase.status == RoadmapPhase.COMPLETED else 'active' if phase.status == RoadmapPhase.IN_PROGRESS else 'available',
                'completion_percentage': float(phase.completion_percentage or 0),
                'estimated_effort': f"{phase.estimated_duration_weeks} weeks" if phase.estimated_duration_weeks else None,
                'next_action': self.get_next_action_for_phase(phase),
                'children': [],
            }

            for milestone in phase.milestones.all().order_by('order'):
                phase_node['children'].append({
                    'id': str(milestone.id),
                    'node_type': 'milestone',
                    'title': milestone.title,
                    'parent_id': str(phase.id),
                    'status': 'completed' if milestone.status == RoadmapMilestone.COMPLETED else 'active' if milestone.status == RoadmapMilestone.IN_PROGRESS else 'available',
                    'estimated_effort': f"{milestone.estimated_duration_hours} hours" if milestone.estimated_duration_hours else None,
                    'next_action': RoadmapMilestoneSerializer().get_next_action(milestone),
                })

            nodes.append(phase_node)
        return nodes

    def get_ai_metadata(self, obj):
        generation = obj.metadata.get('generation', {}) if isinstance(obj.metadata, dict) else {}
        return {
            'source': generation.get('source', 'baseline'),
            'processing_time_ms': int(float(obj.processing_time_seconds or 0) * 1000),
            'model': obj.llm_model_used or None,
            'provider': 'sha8alny',
            'version': generation.get('version'),
            'trace_id': generation.get('trace_id') or str(obj.id),
            'fallback_used': False,
            'error_code': obj.ai_processing_error or None,
        }

    def get_next_action_for_phase(self, phase):
        return RoadmapPhaseSerializer().get_next_action(phase)


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
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Target job title/career goal"
    )
    current_level = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
        help_text="Current skill level"
    )
    target_level = serializers.CharField(
        required=False,
        allow_blank=True,
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

    def validate(self, data):
        """Derive missing creation fields from the assessment when available."""
        from apps.assessments.models import AssessmentResult
        from apps.roadmaps.services import RoadmapService

        assessment = None
        assessment_id = data.get('assessment_id')
        if assessment_id:
            assessment = AssessmentResult.objects.get(
                id=assessment_id,
                assessment__user=self.context['request'].user,
                is_deleted=False,
            )

        target_career = (data.get('target_career') or '').strip()
        current_level = (data.get('current_level') or '').strip()
        target_level = (data.get('target_level') or '').strip()

        if assessment:
            if not target_career:
                target_career = RoadmapService.derive_target_career_from_assessment(assessment) or ''
            if not current_level:
                current_level = RoadmapService.derive_current_level_from_assessment(assessment)
            if not target_level:
                target_level = RoadmapService.default_target_level(target_career)

        if not target_career:
            raise serializers.ValidationError(
                {'target_career': 'Provide a target career or use an assessment result with recommended careers.'}
            )

        data['assessment'] = assessment
        data['target_career'] = target_career
        data['current_level'] = current_level or 'beginner'
        data['target_level'] = target_level or RoadmapService.default_target_level(target_career)

        return data


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
    current_focus_node_id = serializers.UUIDField(required=False, allow_null=True)
    next_action = serializers.DictField(required=False)
