"""
Assessment serializers for staged and legacy assessment flows.
"""

from __future__ import annotations

from rest_framework import serializers

from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.services import AssessmentService


class AssessmentSerializer(serializers.ModelSerializer):
    """Assessment instance serializer with staged compatibility fields."""

    questions = serializers.SerializerMethodField()
    responses = serializers.SerializerMethodField()
    completion_percentage = serializers.FloatField(read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    has_result = serializers.BooleanField(read_only=True)
    presentation = serializers.SerializerMethodField()
    generation_status = serializers.SerializerMethodField()
    active_questions = serializers.SerializerMethodField()
    gap_profile_summary = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = [
            'id',
            'assessment_type',
            'target_career',
            'stage',
            'generation_status',
            'active_questions',
            'gap_profile_summary',
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
            'generation_metadata',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'stage',
            'generation_status',
            'active_questions',
            'gap_profile_summary',
            'ai_processing_status',
            'ai_processed_at',
            'generation_metadata',
            'created_at',
        ]

    def get_questions(self, obj):
        return AssessmentService.get_active_questions(obj)

    def get_responses(self, obj):
        return AssessmentService.get_active_responses(obj)

    def get_generation_status(self, obj):
        return obj.ai_processing_status

    def get_active_questions(self, obj):
        return AssessmentService.get_active_questions(obj)

    def get_gap_profile_summary(self, obj):
        return AssessmentService.build_gap_profile_summary(obj)

    def get_presentation(self, obj):
        active_questions = AssessmentService.get_active_questions(obj)
        active_responses = AssessmentService.get_active_responses(obj)
        question_types = []
        for question in active_questions:
            mode = question.get('interaction_mode') or question.get('type')
            if mode and mode not in question_types:
                question_types.append(mode)

        question_count = len(active_questions)
        current_index = min(len(active_responses), question_count)
        estimated_minutes = max(5, question_count * 2)

        if obj.is_staged:
            submission_state = 'failed'
            if obj.ai_processing_status == 'failed':
                submission_state = 'failed'
            elif obj.stage == 'completed' and obj.ai_processing_status == 'completed':
                submission_state = 'completed'
            elif obj.stage == 'stage_1' and obj.ai_processing_status in ['pending', 'processing'] and not active_questions:
                submission_state = 'stage_1_generating'
            elif obj.stage == 'stage_1' and obj.ai_processing_status == 'processing' and obj.stage_one_responses:
                submission_state = 'stage_1_analyzing'
            elif obj.stage == 'stage_1':
                submission_state = 'stage_1_ready'
            elif obj.stage == 'stage_2' and obj.ai_processing_status == 'processing' and obj.stage_two_responses:
                submission_state = 'stage_2_analyzing'
            elif obj.stage == 'stage_2':
                submission_state = 'stage_2_ready'
            else:
                submission_state = 'stage_1_generating'

            progress_ratio = 0.0
            if obj.total_questions:
                progress_ratio = round((obj.answered_questions / obj.total_questions) * 100, 2)

            return {
                'question_count': question_count,
                'current_index': current_index,
                'progress_ratio': progress_ratio,
                'interaction_modes': question_types,
                'submission_state': submission_state,
                'result_summary_available': obj.has_result,
                'estimated_minutes': estimated_minutes,
            }

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
            'current_index': current_index,
            'progress_ratio': obj.completion_percentage,
            'interaction_modes': question_types,
            'submission_state': submission_state,
            'result_summary_available': obj.has_result,
            'estimated_minutes': estimated_minutes,
        }


class AssessmentCreateSerializer(serializers.Serializer):
    """Create a new assessment."""

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

    def create(self, validated_data):
        user = self.context['request'].user
        return AssessmentService.create_assessment(
            user=user,
            assessment_type=validated_data['assessment_type'],
            target_career=(validated_data.get('target_career') or '').strip(),
        )


class AssessmentResponseSerializer(serializers.Serializer):
    """Stage-aware assessment submission serializer."""

    responses = serializers.JSONField(required=True)

    def validate_responses(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Responses must be a list")
        return value


class AssessmentResultSerializer(serializers.ModelSerializer):
    """Assessment result serializer."""

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
            'roadmap_signal',
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
            'fallback_used': bool(assessment and (assessment.roadmap_signal or {}).get('generation_metadata', {}).get('fallback_used')),
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
