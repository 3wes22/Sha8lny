"""
Course Service Admin Configuration

Provides comprehensive admin interface for managing course platforms,
courses, and course-skill relationships.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import CoursePlatform, Course, CourseSkill


@admin.register(CoursePlatform)
class CoursePlatformAdmin(admin.ModelAdmin):
    """Admin interface for Course Platforms"""

    list_display = [
        'name',
        'slug',
        'integration_type',
        'is_active_badge',
        'total_courses',
        'last_synced_display',
        'created_at'
    ]

    list_filter = [
        'integration_type',
        'is_active',
        'api_key_required',
        'created_at'
    ]

    search_fields = [
        'name',
        'slug',
        'description',
        'website_url'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'total_courses',
        'last_synced_at'
    ]

    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'name',
                'slug',
                'description',
                'website_url',
                'logo_url'
            )
        }),
        ('Integration Settings', {
            'fields': (
                'integration_type',
                'api_base_url',
                'api_key_required',
                'metadata'
            )
        }),
        ('Status & Metrics', {
            'fields': (
                'is_active',
                'total_courses',
                'last_synced_at'
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

    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">● Inactive</span>'
        )
    is_active_badge.short_description = 'Status'

    def last_synced_display(self, obj):
        """Display last sync time in readable format"""
        if obj.last_synced_at:
            return obj.last_synced_at.strftime('%Y-%m-%d %H:%M')
        return format_html('<span style="color: gray;">Never</span>')
    last_synced_display.short_description = 'Last Synced'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """Admin interface for Courses"""

    list_display = [
        'title',
        'platform',
        'level',
        'price_badge',
        'rating_display',
        'total_enrollments',
        'is_published_badge',
        'last_synced_at'
    ]

    list_filter = [
        'platform',
        'level',
        'course_type',
        'is_free',
        'is_published',
        'has_certificate',
        'language',
        'created_at'
    ]

    search_fields = [
        'title',
        'slug',
        'description',
        'external_id',
        'instructors'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_synced_at',
        'external_id',
        'instructor_names_display',
        'is_highly_rated',
        'is_popular'
    ]

    autocomplete_fields = ['platform']

    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'platform',
                'external_id',
                'title',
                'slug',
                'description',
                'short_description',
                'url',
                'thumbnail_url'
            )
        }),
        ('Course Details', {
            'fields': (
                'level',
                'course_type',
                'language',
                'duration_hours',
                'total_lectures',
                'total_resources'
            )
        }),
        ('Pricing', {
            'fields': (
                'is_free',
                'price',
                'currency'
            )
        }),
        ('Ratings & Popularity', {
            'fields': (
                'rating',
                'total_reviews',
                'total_enrollments',
                'is_highly_rated',
                'is_popular'
            )
        }),
        ('Instructors', {
            'fields': (
                'instructors',
                'instructor_names_display'
            )
        }),
        ('Learning Content', {
            'fields': (
                'learning_outcomes',
                'prerequisites',
                'curriculum'
            ),
            'classes': ('collapse',)
        }),
        ('Features', {
            'fields': (
                'has_certificate',
                'has_lifetime_access',
                'has_subtitles'
            )
        }),
        ('Availability', {
            'fields': (
                'is_published',
                'published_date',
                'last_updated'
            )
        }),
        ('Sync & Metadata', {
            'fields': (
                'last_synced_at',
                'sync_error',
                'metadata'
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

    def price_badge(self, obj):
        """Display price as colored badge"""
        if obj.is_free:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px;">FREE</span>'
            )
        if obj.price:
            return format_html(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
                obj.currency,
                obj.price
            )
        return format_html(
            '<span style="color: gray;">Varies</span>'
        )
    price_badge.short_description = 'Price'

    def rating_display(self, obj):
        """Display rating with stars"""
        if obj.rating:
            stars = '⭐' * int(obj.rating)
            return format_html(
                '{} <span style="color: #666;">({:.2f})</span>',
                stars,
                obj.rating
            )
        return format_html('<span style="color: gray;">No rating</span>')
    rating_display.short_description = 'Rating'

    def is_published_badge(self, obj):
        """Display published status as colored badge"""
        if obj.is_published:
            return format_html(
                '<span style="color: green;">✓ Published</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Unpublished</span>'
        )
    is_published_badge.short_description = 'Published'

    def instructor_names_display(self, obj):
        """Display instructor names in readable format"""
        names = obj.instructor_names
        if names:
            return ', '.join(names)
        return 'Unknown'
    instructor_names_display.short_description = 'Instructors'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('platform')


@admin.register(CourseSkill)
class CourseSkillAdmin(admin.ModelAdmin):
    """Admin interface for Course-Skill Relationships"""

    list_display = [
        'course',
        'skill',
        'proficiency_level',
        'is_primary_badge',
        'coverage_percentage_display',
        'created_at'
    ]

    list_filter = [
        'proficiency_level',
        'is_primary',
        'coverage_percentage',
        'created_at'
    ]

    search_fields = [
        'course__title',
        'skill__name'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at'
    ]

    autocomplete_fields = ['course', 'skill']

    fieldsets = (
        ('Relationship', {
            'fields': (
                'id',
                'course',
                'skill'
            )
        }),
        ('Skill Details', {
            'fields': (
                'proficiency_level',
                'is_primary',
                'coverage_percentage'
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

    def coverage_percentage_display(self, obj):
        """Display coverage as progress bar"""
        color = '#28a745' if obj.coverage_percentage >= 70 else '#ffc107' if obj.coverage_percentage >= 40 else '#dc3545'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; border-radius: 3px; padding: 2px;">{}%</div>'
            '</div>',
            obj.coverage_percentage,
            color,
            obj.coverage_percentage
        )
    coverage_percentage_display.short_description = 'Coverage'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('course', 'course__platform', 'skill')
