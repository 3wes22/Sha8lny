"""
Progress Module Admin Configuration

Provides comprehensive admin interface for user progress tracking,
course completions, milestone achievements, and time logs.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Avg
from .models import UserProgress, CourseCompletion, MilestoneAchievement, TimeLog


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """Admin interface for User Progress"""

    list_display = [
        'user_email',
        'roadmap_title',
        'completion_badge',
        'progress_metrics',
        'streak_badge',
        'total_hours',
        'on_track_badge',
        'last_activity_date',
    ]

    list_filter = [
        'on_track',
        'last_activity_date',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'roadmap__title',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'completion_display',
        'streak_display',
        'hours_display',
    ]

    autocomplete_fields = ['user', 'roadmap', 'current_phase', 'current_milestone']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'roadmap',
            )
        }),
        ('Progress Metrics', {
            'fields': (
                'overall_completion_percentage',
                'completion_display',
                'phases_completed',
                'milestones_completed',
                'courses_completed',
            )
        }),
        ('Current Position', {
            'fields': (
                'current_phase',
                'current_milestone',
            )
        }),
        ('Time Tracking', {
            'fields': (
                'total_learning_hours',
                'hours_display',
                'average_hours_per_week',
                'last_activity_date',
            )
        }),
        ('Streak Tracking', {
            'fields': (
                'current_streak_days',
                'longest_streak_days',
                'streak_display',
            )
        }),
        ('Status', {
            'fields': ('on_track',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def roadmap_title(self, obj):
        """Display roadmap title"""
        return obj.roadmap.title[:50]
    roadmap_title.short_description = 'Roadmap'
    roadmap_title.admin_order_field = 'roadmap__title'

    def completion_badge(self, obj):
        """Display completion percentage as progress bar"""
        percentage = float(obj.overall_completion_percentage)
        if percentage >= 100:
            color = '#27ae60'
        elif percentage >= 75:
            color = '#3498db'
        elif percentage >= 50:
            color = '#f39c12'
        elif percentage >= 25:
            color = '#e67e22'
        else:
            color = '#e74c3c'

        return format_html(
            '<div style="width: 100px; background-color: #ecf0f1; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; padding: 3px 0; font-size: 11px; font-weight: bold;">'
            '{}%'
            '</div></div>',
            percentage,
            color,
            int(percentage)
        )
    completion_badge.short_description = 'Completion'

    def progress_metrics(self, obj):
        """Display progress metrics summary"""
        return format_html(
            '<span title="Phases/Milestones/Courses">'
            'P:{} M:{} C:{}'
            '</span>',
            obj.phases_completed,
            obj.milestones_completed,
            obj.courses_completed
        )
    progress_metrics.short_description = 'Progress (P/M/C)'

    def streak_badge(self, obj):
        """Display streak with fire emoji"""
        if obj.current_streak_days == 0:
            return format_html('<span style="color: gray;">No streak</span>')
        elif obj.current_streak_days >= 30:
            color = '#e74c3c'
            icon = '🔥🔥🔥'
        elif obj.current_streak_days >= 7:
            color = '#e67e22'
            icon = '🔥🔥'
        else:
            color = '#f39c12'
            icon = '🔥'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {} days</span>',
            color,
            icon,
            obj.current_streak_days
        )
    streak_badge.short_description = 'Streak'

    def total_hours(self, obj):
        """Display total learning hours"""
        hours = float(obj.total_learning_hours)
        return f"{hours:.1f} hr"
    total_hours.short_description = 'Total Hours'
    total_hours.admin_order_field = 'total_learning_hours'

    def on_track_badge(self, obj):
        """Display on-track status"""
        if obj.on_track:
            return format_html('<span style="color: green; font-weight: bold;">✓ On Track</span>')
        return format_html('<span style="color: red; font-weight: bold;">✗ Behind</span>')
    on_track_badge.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'roadmap', 'current_phase', 'current_milestone')


@admin.register(CourseCompletion)
class CourseCompletionAdmin(admin.ModelAdmin):
    """Admin interface for Course Completions"""

    list_display = [
        'user_email',
        'course_title',
        'completion_percentage_badge',
        'rating_badge',
        'duration_info',
        'certificate_badge',
        'completed_at',
    ]

    list_filter = [
        'user_rating',
        'would_recommend',
        'has_certificate',
        'completed_at',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'course__title',
        'user_review',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'rating_display',
        'duration_display',
    ]

    autocomplete_fields = ['user', 'course', 'roadmap_course']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'course',
                'roadmap_course',
            )
        }),
        ('Completion Details', {
            'fields': (
                'started_at',
                'completed_at',
                'duration_display',
                'time_spent_hours',
                'completion_percentage',
            )
        }),
        ('User Feedback', {
            'fields': (
                'user_rating',
                'rating_display',
                'user_review',
                'would_recommend',
            )
        }),
        ('Certificate', {
            'fields': (
                'has_certificate',
                'certificate_url',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def course_title(self, obj):
        """Display course title"""
        return obj.course.title[:50]
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'

    def completion_percentage_badge(self, obj):
        """Display completion percentage"""
        percentage = float(obj.completion_percentage)
        if percentage >= 100:
            color = '#27ae60'
            icon = '✓'
        elif percentage >= 75:
            color = '#3498db'
            icon = '◐'
        else:
            color = '#f39c12'
            icon = '◔'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}%</span>',
            color,
            icon,
            int(percentage)
        )
    completion_percentage_badge.short_description = 'Completion'
    completion_percentage_badge.admin_order_field = 'completion_percentage'

    def rating_badge(self, obj):
        """Display rating with stars"""
        if not obj.user_rating:
            return format_html('<span style="color: gray;">No rating</span>')

        stars = '⭐' * obj.user_rating
        color = '#f39c12' if obj.user_rating >= 4 else '#95a5a6'

        return format_html(
            '<span style="color: {};">{} ({})</span>',
            color,
            stars,
            obj.user_rating
        )
    rating_badge.short_description = 'Rating'
    rating_badge.admin_order_field = 'user_rating'

    def duration_info(self, obj):
        """Display time spent and duration"""
        time_info = obj.duration_display
        if obj.time_spent_hours:
            time_info += f" ({float(obj.time_spent_hours):.1f}h)"
        return time_info
    duration_info.short_description = 'Duration'

    def certificate_badge(self, obj):
        """Display certificate status"""
        if obj.has_certificate:
            if obj.certificate_url:
                return format_html(
                    '<a href="{}" target="_blank" style="color: green; font-weight: bold;">🎓 View</a>',
                    obj.certificate_url
                )
            return format_html('<span style="color: green; font-weight: bold;">🎓 Yes</span>')
        return format_html('<span style="color: gray;">No</span>')
    certificate_badge.short_description = 'Certificate'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'course', 'roadmap_course')


@admin.register(MilestoneAchievement)
class MilestoneAchievementAdmin(admin.ModelAdmin):
    """Admin interface for Milestone Achievements"""

    list_display = [
        'user_email',
        'milestone_title',
        'achieved_at',
        'completion_speed',
        'badge_display',
    ]

    list_filter = [
        'badge_awarded',
        'achieved_at',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'milestone__title',
        'badge_type',
    ]

    readonly_fields = [
        'id',
        'achieved_at',
        'created_at',
        'updated_at',
        'completion_speed_display',
    ]

    autocomplete_fields = ['user', 'milestone']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'milestone',
            )
        }),
        ('Achievement Details', {
            'fields': (
                'achieved_at',
                'time_to_complete_days',
                'completion_speed_display',
            )
        }),
        ('Badge/Gamification', {
            'fields': (
                'badge_awarded',
                'badge_type',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def milestone_title(self, obj):
        """Display milestone title"""
        return obj.milestone.title[:50]
    milestone_title.short_description = 'Milestone'
    milestone_title.admin_order_field = 'milestone__title'

    def completion_speed(self, obj):
        """Display completion speed"""
        if not obj.time_to_complete_days:
            return format_html('<span style="color: gray;">Unknown</span>')

        days = obj.time_to_complete_days
        if days <= 7:
            color = '#27ae60'
            icon = '⚡'
        elif days <= 30:
            color = '#3498db'
            icon = '→'
        else:
            color = '#95a5a6'
            icon = '→'

        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            icon,
            obj.completion_speed_display
        )
    completion_speed.short_description = 'Speed'
    completion_speed.admin_order_field = 'time_to_complete_days'

    def badge_display(self, obj):
        """Display badge information"""
        if not obj.badge_awarded:
            return format_html('<span style="color: gray;">No badge</span>')

        badge_icon = '🏆' if obj.badge_type else '🎖️'
        badge_text = obj.badge_type if obj.badge_type else 'Badge Earned'

        return format_html(
            '<span style="color: #f39c12; font-weight: bold;">{} {}</span>',
            badge_icon,
            badge_text
        )
    badge_display.short_description = 'Badge'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'milestone', 'milestone__phase', 'milestone__phase__roadmap')


@admin.register(TimeLog)
class TimeLogAdmin(admin.ModelAdmin):
    """Admin interface for Time Logs"""

    list_display = [
        'user_email',
        'activity_type_badge',
        'duration_badge',
        'course_title',
        'roadmap_title',
        'started_at',
    ]

    list_filter = [
        'activity_type',
        'started_at',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'course__title',
        'roadmap__title',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duration_display',
        'duration_hours',
    ]

    autocomplete_fields = ['user', 'course', 'roadmap']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'activity_type',
            )
        }),
        ('Associated Resources', {
            'fields': (
                'course',
                'roadmap',
            )
        }),
        ('Time Details', {
            'fields': (
                'started_at',
                'ended_at',
                'duration_minutes',
                'duration_display',
                'duration_hours',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def activity_type_badge(self, obj):
        """Display activity type as badge"""
        colors = {
            'course': '#3498db',
            'practice': '#9b59b6',
            'reading': '#27ae60',
            'project': '#e67e22',
        }
        color = colors.get(obj.activity_type, 'gray')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_activity_type_display()
        )
    activity_type_badge.short_description = 'Activity'
    activity_type_badge.admin_order_field = 'activity_type'

    def duration_badge(self, obj):
        """Display duration with color coding"""
        minutes = obj.duration_minutes
        if minutes >= 120:  # 2+ hours
            color = '#27ae60'
            icon = '🔥'
        elif minutes >= 60:  # 1+ hour
            color = '#3498db'
            icon = '✓'
        else:
            color = '#95a5a6'
            icon = '→'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.duration_display
        )
    duration_badge.short_description = 'Duration'
    duration_badge.admin_order_field = 'duration_minutes'

    def course_title(self, obj):
        """Display course title"""
        if not obj.course:
            return format_html('<span style="color: gray;">N/A</span>')
        return obj.course.title[:40]
    course_title.short_description = 'Course'

    def roadmap_title(self, obj):
        """Display roadmap title"""
        if not obj.roadmap:
            return format_html('<span style="color: gray;">N/A</span>')
        return obj.roadmap.title[:40]
    roadmap_title.short_description = 'Roadmap'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'course', 'roadmap')
