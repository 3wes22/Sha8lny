"""
Career Tools Module Admin Configuration

Provides comprehensive admin interface for resumes and portfolios.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Resume, Portfolio


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    """Admin interface for Resumes"""

    list_display = [
        'user_email',
        'title_display',
        'primary_badge',
        'ats_score_badge',
        'completeness_badge',
        'file_formats_badge',
        'version',
        'updated_at',
    ]

    list_filter = [
        'is_primary',
        'is_ats_optimized',
        'template_name',
        'created_at',
        'updated_at',
    ]

    search_fields = [
        'title',
        'user__email',
        'user__first_name',
        'user__last_name',
        'template_name',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'ats_grade_display',
        'has_files',
        'file_formats_available',
        'completeness_percentage',
        'pdf_size_mb',
        'docx_size_mb',
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'title',
                'template_name',
            )
        }),
        ('Resume Data (JSONB)', {
            'fields': (
                'personal_info',
                'work_experience',
                'education',
                'skills',
                'certifications',
                'projects',
                'languages',
            ),
            'classes': ('collapse',)
        }),
        ('ATS Optimization', {
            'fields': (
                'is_ats_optimized',
                'ats_score',
                'ats_grade_display',
                'ats_suggestions',
            )
        }),
        ('File Storage', {
            'fields': (
                'pdf_file',
                'docx_file',
                'has_files',
                'file_formats_available',
                'pdf_size_mb',
                'docx_size_mb',
            ),
            'description': 'File storage for PDF and DOCX formats'
        }),
        ('Metadata', {
            'fields': (
                'is_primary',
                'version',
                'completeness_percentage',
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

    def title_display(self, obj):
        """Display resume title with truncation"""
        return obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
    title_display.short_description = 'Title'
    title_display.admin_order_field = 'title'

    def primary_badge(self, obj):
        """Display primary resume badge"""
        if obj.is_primary:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">⭐ PRIMARY</span>'
            )
        return format_html('<span style="color: gray;">Secondary</span>')
    primary_badge.short_description = 'Status'

    def ats_score_badge(self, obj):
        """Display ATS score with color coding"""
        if not obj.ats_score:
            return format_html('<span style="color: gray;">Not Scored</span>')

        score = float(obj.ats_score)
        grade = obj.ats_grade_display

        if score >= 90:
            color = '#27ae60'  # Green
        elif score >= 80:
            color = '#3498db'  # Blue
        elif score >= 70:
            color = '#f39c12'  # Orange
        elif score >= 60:
            color = '#e67e22'  # Dark orange
        else:
            color = '#e74c3c'  # Red

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} ({})</span>',
            color,
            grade,
            int(score)
        )
    ats_score_badge.short_description = 'ATS Score'
    ats_score_badge.admin_order_field = 'ats_score'

    def completeness_badge(self, obj):
        """Display resume completeness as progress bar"""
        percentage = obj.completeness_percentage

        if percentage >= 90:
            color = '#27ae60'
        elif percentage >= 70:
            color = '#3498db'
        elif percentage >= 50:
            color = '#f39c12'
        else:
            color = '#e74c3c'

        return format_html(
            '<div style="width: 80px; background-color: #ecf0f1; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; padding: 3px 0; font-size: 10px; font-weight: bold;">'
            '{}%'
            '</div></div>',
            percentage,
            color,
            int(percentage)
        )
    completeness_badge.short_description = 'Complete'

    def file_formats_badge(self, obj):
        """Display available file formats"""
        formats = []
        if obj.pdf_file:
            formats.append(format_html('<span style="background-color: #e74c3c; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">PDF</span>'))
        if obj.docx_file:
            formats.append(format_html('<span style="background-color: #2980b9; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">DOCX</span>'))

        if not formats:
            return format_html('<span style="color: gray;">None</span>')

        return format_html(' '.join(str(f) for f in formats))
    file_formats_badge.short_description = 'Files'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """Admin interface for Portfolios"""

    list_display = [
        'user_email',
        'title_display',
        'visibility_badge',
        'url_slug_display',
        'content_summary',
        'completeness_badge',
        'view_count_display',
        'updated_at',
    ]

    list_filter = [
        'is_public',
        'theme',
        'created_at',
        'updated_at',
    ]

    search_fields = [
        'title',
        'description',
        'custom_url_slug',
        'user__email',
        'user__first_name',
        'user__last_name',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'public_url',
        'project_count',
        'achievement_count',
        'has_testimonials',
        'completeness_percentage',
        'view_count',
        'last_viewed_at',
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'title',
                'description',
            )
        }),
        ('Portfolio Data (JSONB)', {
            'fields': (
                'projects',
                'achievements',
                'testimonials',
            ),
            'classes': ('collapse',)
        }),
        ('Customization', {
            'fields': (
                'theme',
                'custom_styles',
            )
        }),
        ('Visibility & Sharing', {
            'fields': (
                'is_public',
                'custom_url_slug',
                'public_url',
            )
        }),
        ('Analytics', {
            'fields': (
                'view_count',
                'last_viewed_at',
            )
        }),
        ('Content Summary', {
            'fields': (
                'project_count',
                'achievement_count',
                'has_testimonials',
                'completeness_percentage',
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

    def title_display(self, obj):
        """Display portfolio title with truncation"""
        return obj.title[:40] + '...' if len(obj.title) > 40 else obj.title
    title_display.short_description = 'Title'
    title_display.admin_order_field = 'title'

    def visibility_badge(self, obj):
        """Display visibility status"""
        if obj.is_public:
            return format_html(
                '<span style="background-color: #27ae60; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🌐 PUBLIC</span>'
            )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; padding: 3px 8px; border-radius: 3px;">🔒 PRIVATE</span>'
        )
    visibility_badge.short_description = 'Visibility'

    def url_slug_display(self, obj):
        """Display URL slug as clickable link if public"""
        if not obj.custom_url_slug:
            return format_html('<span style="color: gray;">No URL</span>')

        if obj.is_public:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3498db; text-decoration: none;">/{}</a>',
                obj.public_url,
                obj.custom_url_slug
            )
        return format_html(
            '<span style="color: gray;">/{}</span>',
            obj.custom_url_slug
        )
    url_slug_display.short_description = 'URL'

    def content_summary(self, obj):
        """Display content summary"""
        return format_html(
            '<span title="Projects / Achievements / Testimonials">'
            'P:{} A:{} T:{}'
            '</span>',
            obj.project_count,
            obj.achievement_count,
            '✓' if obj.has_testimonials else '✗'
        )
    content_summary.short_description = 'Content (P/A/T)'

    def completeness_badge(self, obj):
        """Display portfolio completeness as progress bar"""
        percentage = obj.completeness_percentage

        if percentage >= 90:
            color = '#27ae60'
        elif percentage >= 70:
            color = '#3498db'
        elif percentage >= 50:
            color = '#f39c12'
        else:
            color = '#e74c3c'

        return format_html(
            '<div style="width: 80px; background-color: #ecf0f1; border-radius: 3px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; padding: 3px 0; font-size: 10px; font-weight: bold;">'
            '{}%'
            '</div></div>',
            percentage,
            color,
            int(percentage)
        )
    completeness_badge.short_description = 'Complete'

    def view_count_display(self, obj):
        """Display view count with icon"""
        if obj.view_count == 0:
            return format_html('<span style="color: gray;">0 views</span>')

        if obj.view_count >= 1000:
            color = '#27ae60'
            icon = '👁️👁️'
        elif obj.view_count >= 100:
            color = '#3498db'
            icon = '👁️'
        else:
            color = '#95a5a6'
            icon = '👁️'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.view_count
        )
    view_count_display.short_description = 'Views'
    view_count_display.admin_order_field = 'view_count'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user')
