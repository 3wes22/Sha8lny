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
    target_career = serializers.CharField(required=False, allow_blank=True)

    def _generate_questions(self, assessment_type):
        """Generate predefined questions based on assessment type."""
        # In production, this would use AI to generate personalized questions
        # For MVP, we use predefined question sets

        base_questions = [
            {
                "id": 1,
                "type": "multiple_choice",
                "question": "How familiar are you with programming fundamentals (variables, loops, functions)?",
                "category": "Fundamentals",
                "options": [
                    {"value": "none", "label": "I've never written code before", "score": 1},
                    {"value": "basic", "label": "I've done some tutorials / small scripts", "score": 2},
                    {"value": "comfortable", "label": "I can build small apps/projects", "score": 4},
                    {"value": "advanced", "label": "I'm very comfortable and help others learn", "score": 5}
                ]
            },
            {
                "id": 2,
                "type": "scale",
                "question": "Rate your confidence in problem-solving and debugging.",
                "category": "Problem Solving",
                "min_value": 1,
                "max_value": 5,
                "labels": {"1": "Very low", "5": "Very high"}
            },
            {
                "id": 3,
                "type": "scale",
                "question": "Rate your familiarity with web technologies (HTML, CSS, JavaScript).",
                "category": "Web Development",
                "min_value": 1,
                "max_value": 5,
                "labels": {"1": "Not familiar", "5": "Expert"}
            },
            {
                "id": 4,
                "type": "multiple_choice",
                "question": "Which best describes your current experience level?",
                "category": "Experience",
                "options": [
                    {"value": "student", "label": "Student / completely new", "score": 1},
                    {"value": "junior", "label": "Junior / < 2 years experience", "score": 3},
                    {"value": "mid", "label": "Mid-level / 2-5 years", "score": 4},
                    {"value": "senior", "label": "Senior / 5+ years", "score": 5}
                ]
            },
            {
                "id": 5,
                "type": "text",
                "question": "What is your main goal with this career path?",
                "category": "Goals",
                "helper": "For example: get a first job, switch from another field, grow to senior, freelancing, etc."
            },
            {
                "id": 6,
                "type": "scale",
                "question": "How much time per week can you realistically dedicate to learning?",
                "category": "Commitment",
                "min_value": 1,
                "max_value": 5,
                "labels": {"1": "<3 hours", "5": "15+ hours"}
            }
        ]

        return base_questions

    def create(self, validated_data):
        """Create assessment with predefined questions."""
        user = self.context['request'].user
        assessment_type = validated_data['assessment_type']

        # Generate questions
        questions = self._generate_questions(assessment_type)

        # Create assessment
        assessment = Assessment.objects.create(
            user=user,
            assessment_type=assessment_type,
            questions=questions,
            status='draft',
            total_questions=len(questions),
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
