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
from apps.assessments.ai_pipeline import get_default_questions


class AssessmentSerializer(serializers.ModelSerializer):
    """Assessment instance serializer."""
    completion_percentage = serializers.IntegerField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    has_result = serializers.BooleanField(read_only=True)
    presentation = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id',
            'assessment_type',
            'target_career',
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
            'presentation',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'ai_processing_status',
            'ai_processed_at',
            'created_at',
        ]

    def get_presentation(self, obj):
        question_types = []
        for question in obj.questions or []:
            mode = question.get('interaction_mode') or question.get('type')
            if mode and mode not in question_types:
                question_types.append(mode)

        question_count = obj.total_questions or len(obj.questions or [])

        submission_state = 'draft'
        if obj.status == 'draft' and obj.ai_processing_status in ['pending', 'processing'] and question_count == 0:
            submission_state = 'generating'
        elif obj.status == 'draft' and question_count > 0:
            submission_state = 'ready'
        elif obj.status == 'completed' and obj.ai_processing_status == 'completed':
            submission_state = 'completed'
        elif obj.status == 'completed':
            submission_state = 'processing'
        elif obj.status == 'in_progress':
            submission_state = 'submitting'

        return {
            'question_count': question_count,
            'current_index': min(obj.answered_questions or 0, question_count),
            'progress_ratio': obj.completion_percentage,
            'interaction_modes': question_types,
            'submission_state': submission_state,
            'result_summary_available': obj.has_result,
            'estimated_minutes': max(5, question_count * 2),
        }


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
    target_career = serializers.CharField(required=False, allow_blank=True)

    def _generate_questions(self, assessment_type):
        """Return the deterministic fallback question set."""
        return get_default_questions(assessment_type)

    def create(self, validated_data):
        """Create assessment with predefined questions."""
        user = self.context['request'].user
        assessment_type = validated_data['assessment_type']

        # Generate questions
        # Create assessment
        assessment = Assessment.objects.create(
            user=user,
            assessment_type=assessment_type,
            target_career=(validated_data.get('target_career') or '').strip(),
            questions=[],
            status='draft',
            total_questions=0,
            answered_questions=0,
            ai_processing_status='pending',
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
    ai_metadata = serializers.SerializerMethodField()

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
            'ai_metadata',
            'top_skills',
            'version',
            'is_shared',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_ai_metadata(self, obj):
        assessment = getattr(obj, 'assessment', None)
        return {
            'source': 'baseline',
            'processing_time_ms': int(float(obj.processing_time_seconds or 0) * 1000),
            'model': obj.llm_model_used or None,
            'provider': 'ollama' if obj.llm_model_used else 'sha8alny',
            'version': obj.version,
            'trace_id': assessment.ai_trace_id if assessment else None,
            'fallback_used': bool(assessment and obj.llm_model_used == 'baseline-assessment-v1'),
            'error_code': assessment.ai_processing_error if assessment and assessment.ai_processing_status == 'failed' else None,
        }


class AssessmentListSerializer(serializers.ModelSerializer):
    """Minimal assessment info for list views."""

    class Meta:
        model = Assessment
        fields = [
            'id',
            'assessment_type',
            'target_career',
            'status',
            'completion_percentage',
            'created_at',
        ]
