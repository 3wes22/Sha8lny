"""
Django admin configuration for Assessment Service models.

Provides customized admin interfaces for Assessment and AssessmentResult.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from apps.assessments.models import Assessment, AssessmentResult


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    """Admin interface for Assessment model."""

    list_display = [
        'id',
        'user',
        'assessment_type',
        'status',
        'ai_processing_status',
        'progress_display',
        'started_at',
        'completed_at',
        'created_at',
    ]

    list_filter = [
        'assessment_type',
        'status',
        'ai_processing_status',
        'created_at',
        'completed_at',
    ]

    search_fields = [
        'user__email',
        'user__username',
        'user__full_name',
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'completion_percentage',
        'is_complete',
        'has_result',
        'ai_processed_at',
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        (_('Assessment Information'), {
            'fields': (
                'id',
                'user',
                'assessment_type',
                'status',
            )
        }),
        (_('Questions & Responses'), {
            'fields': (
                'questions',
                'responses',
                'total_questions',
                'answered_questions',
                'completion_percentage',
            )
        }),
        (_('AI Processing'), {
            'fields': (
                'ai_processing_status',
                'ai_processed_at',
                'ai_processing_error',
            )
        }),
        (_('Progress & Timing'), {
            'fields': (
                'started_at',
                'completed_at',
                'time_spent_seconds',
                'is_complete',
                'has_result',
            )
        }),
        (_('Audit Information'), {
            'fields': (
                'created_at',
                'updated_at',
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def progress_display(self, obj):
        """Display progress as colored percentage."""
        percentage = obj.completion_percentage
        if percentage == 100:
            color = 'green'
        elif percentage >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            percentage
        )
    progress_display.short_description = _('Progress')

    def completion_percentage(self, obj):
        """Display calculated completion percentage."""
        return f'{obj.completion_percentage}%'
    completion_percentage.short_description = _('Completion %')

    def is_complete(self, obj):
        """Display completion status."""
        return obj.is_complete
    is_complete.short_description = _('Is Complete')
    is_complete.boolean = True

    def has_result(self, obj):
        """Display result existence."""
        return obj.has_result
    has_result.short_description = _('Has Result')
    has_result.boolean = True


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    """Admin interface for AssessmentResult model."""

    list_display = [
        'id',
        'assessment_user',
        'assessment_type',
        'overall_score_display',
        'ai_confidence_score',
        'llm_model_used',
        'total_tokens_used',
        'is_shared',
        'created_at',
    ]

    list_filter = [
        'llm_model_used',
        'is_shared',
        'version',
        'created_at',
    ]

    search_fields = [
        'assessment__user__email',
        'assessment__user__username',
        'assessment__user__full_name',
        'ai_insights',
    ]

    ordering = ['-created_at']

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'deleted_at',
        'total_tokens_used',
        'top_skills_display',
        'processing_time_seconds',
    ]

    autocomplete_fields = ['assessment']

    fieldsets = (
        (_('Assessment Link'), {
            'fields': (
                'id',
                'assessment',
            )
        }),
        (_('Overall Results'), {
            'fields': (
                'overall_score',
                'ai_confidence_score',
                'version',
            )
        }),
        (_('Skill Analysis'), {
            'fields': (
                'skill_scores',
                'top_skills_display',
                'strengths',
                'areas_for_improvement',
            )
        }),
        (_('Recommendations'), {
            'fields': (
                'recommended_careers',
                'recommended_learning_paths',
            )
        }),
        (_('AI Insights'), {
            'fields': (
                'ai_insights',
                'llm_model_used',
                'llm_prompt_tokens',
                'llm_completion_tokens',
                'total_tokens_used',
                'processing_time_seconds',
            )
        }),
        (_('Sharing'), {
            'fields': (
                'is_shared',
            )
        }),
        (_('Audit Information'), {
            'fields': (
                'created_at',
                'updated_at',
                'is_deleted',
                'deleted_at',
            ),
            'classes': ('collapse',),
        }),
    )

    def assessment_user(self, obj):
        """Display assessment user."""
        return obj.assessment.user.username
    assessment_user.short_description = _('User')
    assessment_user.admin_order_field = 'assessment__user__username'

    def assessment_type(self, obj):
        """Display assessment type."""
        return obj.assessment.get_assessment_type_display()
    assessment_type.short_description = _('Assessment Type')
    assessment_type.admin_order_field = 'assessment__assessment_type'

    def overall_score_display(self, obj):
        """Display overall score with color coding."""
        score = obj.overall_score
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            score
        )
    overall_score_display.short_description = _('Overall Score')
    overall_score_display.admin_order_field = 'overall_score'

    def total_tokens_used(self, obj):
        """Display total LLM tokens used."""
        return obj.total_tokens_used
    total_tokens_used.short_description = _('Total Tokens')

    def top_skills_display(self, obj):
        """Display top 5 skills in formatted list."""
        top_skills = obj.top_skills
        if not top_skills:
            return _('No skills analyzed')

        skills_html = '<ul style="margin: 0; padding-left: 20px;">'
        for skill_data in top_skills:
            skills_html += f'<li><strong>{skill_data["skill"]}</strong>: {skill_data["score"]}% ({skill_data["category"]})</li>'
        skills_html += '</ul>'
        return format_html(skills_html)
    top_skills_display.short_description = _('Top Skills')
