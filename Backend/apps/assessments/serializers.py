"""
Assessment Service Serializers

Implements AI-powered skill assessment serializers.

SRS References:
- FR-6: Generate Skill Assessment
- FR-7: Assessment Versioning
- FR-8: AI Processing
"""

from rest_framework import serializers
from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.services import AssessmentService


class AssessmentSerializer(serializers.ModelSerializer):
    """Assessment instance serializer."""
    completion_percentage = serializers.IntegerField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    has_result = serializers.BooleanField(read_only=True)

    class Meta:
        model = Assessment
        fields = [
            'id',
            'assessment_type',
            'questions',
            'responses',
            'ai_processing_status',
            'ai_processed_at',
            'status',
            'started_at',
            'completed_at',
            'total_questions',
            'answered_questions',
            'completion_percentage',
            'time_spent_seconds',
            'is_complete',
            'has_result',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'ai_processing_status',
            'ai_processed_at',
            'created_at',
        ]


class AssessmentCreateSerializer(serializers.Serializer):
    """
    Create new assessment.

    SRS FR-6: System shall accept user input (CV text, Career goals, Skills)
    """
    assessment_type = serializers.ChoiceField(
        choices=['skills', 'career_interests', 'personality', 'learning_style', 'comprehensive'],
        default='skills'
    )
    cv_text = serializers.CharField(required=False, allow_blank=True)
    career_goals = serializers.CharField(required=False, allow_blank=True)
    current_skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list
    )

    def create(self, validated_data):
        """Create assessment using AssessmentService."""
        user = self.context['request'].user

        # TODO: Implement AssessmentService.create_assessment()
        # For now, create basic assessment
        assessment = Assessment.objects.create(
            user=user,
            assessment_type=validated_data['assessment_type'],
            status='draft',
            total_questions=0,
            answered_questions=0
        )

        return assessment


class AssessmentResponseSerializer(serializers.Serializer):
    """Submit assessment responses."""
    responses = serializers.JSONField(required=True)

    def validate_responses(self, value):
        """Validate responses format."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Responses must be a list")
        return value


class AssessmentResultSerializer(serializers.ModelSerializer):
    """
    Assessment result serializer.

    SRS FR-8: Parse response into Skills, Levels, Notes, Recommendations
    """
    top_skills = serializers.JSONField(read_only=True)
    total_tokens_used = serializers.IntegerField(read_only=True)

    class Meta:
        model = AssessmentResult
        fields = [
            'id',
            'assessment',
            'overall_score',
            'skill_scores',
            'strengths',
            'areas_for_improvement',
            'recommended_careers',
            'recommended_learning_paths',
            'ai_insights',
            'ai_confidence_score',
            'llm_model_used',
            'llm_prompt_tokens',
            'llm_completion_tokens',
            'total_tokens_used',
            'processing_time_seconds',
            'top_skills',
            'version',
            'is_shared',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AssessmentListSerializer(serializers.ModelSerializer):
    """Minimal assessment info for list views."""

    class Meta:
        model = Assessment
        fields = [
            'id',
            'assessment_type',
            'status',
            'completion_percentage',
            'created_at',
        ]
