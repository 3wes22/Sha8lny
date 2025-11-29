"""
Roadmap Service Admin Configuration

Provides comprehensive admin interface for managing roadmap templates,
roadmaps, phases, milestones, and course recommendations.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import RoadmapTemplate, Roadmap, RoadmapPhase, RoadmapMilestone, RoadmapCourse


@admin.register(RoadmapTemplate)
class RoadmapTemplateAdmin(admin.ModelAdmin):
    """Admin interface for Roadmap Templates"""

    list_display = [
        'title',
        'target_career',
        'career_level',
        'difficulty_level',
        'estimated_duration_weeks',
        'is_published_badge',
        'usage_count',
        'created_at'
    ]

    list_filter = [
        'career_level',
        'difficulty_level',
        'is_published',
        'created_at'
    ]

    search_fields = [
        'title',
        'slug',
        'target_career',
        'description'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'usage_count'
    ]

    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'title',
                'slug',
                'description',
                'short_description',
                'target_career',
                'career_level'
            )
        }),
        ('Details', {
            'fields': (
                'difficulty_level',
                'estimated_duration_weeks',
                'prerequisites',
                'learning_outcomes',
                'required_skills'
            )
        }),
        ('Status & Metrics', {
            'fields': (
                'is_published',
                'usage_count'
            )
        }),
        ('Metadata', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def is_published_badge(self, obj):
        """Display published status as colored badge"""
        if obj.is_published:
            return format_html(
                '<span style="color: green;">&#10003; Published</span>'
            )
        return format_html(
            '<span style="color: gray;">&#10007; Draft</span>'
        )
    is_published_badge.short_description = 'Status'


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    """Admin interface for Roadmaps"""

    list_display = [
        'title',
        'user',
        'target_career',
        'status_badge',
        'completion_percentage',
        'estimated_duration_weeks',
        'ai_processing_status_badge',
        'created_at'
    ]

    list_filter = [
        'status',
        'ai_processing_status',
        'template',
        'created_at'
    ]

    search_fields = [
        'title',
        'user__email',
        'user__username',
        'target_career',
        'description'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'ai_processed_at',
        'llm_model_used',
        'llm_prompt_tokens',
        'llm_completion_tokens',
        'processing_time_seconds',
        'is_active',
        'is_complete',
        'total_phases',
        'completed_phases'
    ]

    autocomplete_fields = ['user', 'template']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'template',
                'assessment',
                'title',
                'description'
            )
        }),
        ('Career Goals', {
            'fields': (
                'target_career',
                'current_level',
                'target_level',
                'estimated_duration_weeks',
                'weekly_hours_commitment'
            )
        }),
        ('Status & Progress', {
            'fields': (
                'status',
                'completion_percentage',
                'started_at',
                'completed_at',
                'is_active',
                'is_complete',
                'total_phases',
                'completed_phases'
            )
        }),
        ('AI Processing', {
            'fields': (
                'ai_processing_status',
                'ai_processed_at',
                'ai_processing_error',
                'llm_model_used',
                'llm_prompt_tokens',
                'llm_completion_tokens',
                'processing_time_seconds',
                'ai_insights'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'draft': 'gray',
            'active': 'green',
            'in_progress': 'blue',
            'completed': 'darkgreen',
            'paused': 'orange',
            'archived': 'lightgray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def ai_processing_status_badge(self, obj):
        """Display AI processing status as badge"""
        colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red'
        }
        color = colors.get(obj.ai_processing_status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_ai_processing_status_display()
        )
    ai_processing_status_badge.short_description = 'AI Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'template', 'assessment')


@admin.register(RoadmapPhase)
class RoadmapPhaseAdmin(admin.ModelAdmin):
    """Admin interface for Roadmap Phases"""

    list_display = [
        'roadmap',
        'order',
        'title',
        'status_badge',
        'completion_percentage',
        'estimated_duration_weeks',
        'total_milestones',
        'completed_milestones'
    ]

    list_filter = [
        'status',
        'created_at'
    ]

    search_fields = [
        'title',
        'description',
        'roadmap__title',
        'roadmap__user__email'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'is_complete',
        'total_milestones',
        'completed_milestones'
    ]

    autocomplete_fields = ['roadmap']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'roadmap',
                'order',
                'title',
                'description'
            )
        }),
        ('Details', {
            'fields': (
                'estimated_duration_weeks',
                'objectives'
            )
        }),
        ('Status & Progress', {
            'fields': (
                'status',
                'completion_percentage',
                'started_at',
                'completed_at',
                'is_complete',
                'total_milestones',
                'completed_milestones'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'not_started': 'gray',
            'in_progress': 'blue',
            'completed': 'green',
            'skipped': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('roadmap', 'roadmap__user')


@admin.register(RoadmapMilestone)
class RoadmapMilestoneAdmin(admin.ModelAdmin):
    """Admin interface for Roadmap Milestones"""

    list_display = [
        'phase',
        'order',
        'title',
        'milestone_type',
        'status_badge',
        'estimated_duration_hours',
        'is_required_badge',
        'total_courses'
    ]

    list_filter = [
        'milestone_type',
        'status',
        'is_required',
        'created_at'
    ]

    search_fields = [
        'title',
        'description',
        'phase__title',
        'phase__roadmap__title'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'is_complete',
        'total_courses'
    ]

    autocomplete_fields = ['phase']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'phase',
                'order',
                'title',
                'description',
                'milestone_type'
            )
        }),
        ('Details', {
            'fields': (
                'estimated_duration_hours',
                'is_required',
                'skills',
                'resources'
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'completed_at',
                'is_complete',
                'total_courses'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'not_started': 'gray',
            'in_progress': 'blue',
            'completed': 'green',
            'skipped': 'orange'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def is_required_badge(self, obj):
        """Display required status as badge"""
        if obj.is_required:
            return format_html(
                '<span style="color: red; font-weight: bold;">Required</span>'
            )
        return format_html(
            '<span style="color: gray;">Optional</span>'
        )
    is_required_badge.short_description = 'Required'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('phase', 'phase__roadmap')


@admin.register(RoadmapCourse)
class RoadmapCourseAdmin(admin.ModelAdmin):
    """Admin interface for Roadmap Courses"""

    list_display = [
        'milestone',
        'course',
        'order',
        'is_primary_badge',
        'match_score_display',
        'enrollment_status',
        'created_at'
    ]

    list_filter = [
        'is_primary',
        'is_enrolled',
        'is_completed',
        'created_at'
    ]

    search_fields = [
        'milestone__title',
        'course__title',
        'recommendation_reason'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'is_high_match'
    ]

    autocomplete_fields = ['milestone', 'course']

    fieldsets = (
        ('Relationship', {
            'fields': (
                'id',
                'milestone',
                'course',
                'order',
                'is_primary'
            )
        }),
        ('Recommendation', {
            'fields': (
                'match_score',
                'is_high_match',
                'recommendation_reason'
            )
        }),
        ('User Interaction', {
            'fields': (
                'is_enrolled',
                'is_completed',
                'enrolled_at',
                'completed_at'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def is_primary_badge(self, obj):
        """Display primary status as badge"""
        if obj.is_primary:
            return format_html(
                '<span style="background-color: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-weight: bold;">PRIMARY</span>'
            )
        return format_html(
            '<span style="color: gray;">Secondary</span>'
        )
    is_primary_badge.short_description = 'Type'

    def match_score_display(self, obj):
        """Display match score with color coding"""
        if obj.match_score >= 80:
            color = '#28a745'
        elif obj.match_score >= 60:
            color = '#ffc107'
        else:
            color = '#dc3545'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            obj.match_score
        )
    match_score_display.short_description = 'Match Score'

    def enrollment_status(self, obj):
        """Display enrollment and completion status"""
        if obj.is_completed:
            return format_html(
                '<span style="color: green;">&#10003; Completed</span>'
            )
        elif obj.is_enrolled:
            return format_html(
                '<span style="color: blue;">Enrolled</span>'
            )
        return format_html(
            '<span style="color: gray;">Not Enrolled</span>'
        )
    enrollment_status.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('milestone', 'milestone__phase', 'course', 'course__platform')
