"""
Jobs Module Admin Configuration

Provides comprehensive admin interface for job platforms, job listings,
skill requirements, market insights, and skill demand analytics.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import JobPlatform, Job, JobSkill, SavedJob, MarketInsight, SkillDemand


@admin.register(JobPlatform)
class JobPlatformAdmin(admin.ModelAdmin):
    """Admin interface for Job Platforms"""

    list_display = [
        'name',
        'slug',
        'website_url_link',
        'has_api_badge',
        'scraping_enabled_badge',
        'is_active_badge',
        'job_count',
        'last_scraped_at',
    ]

    list_filter = [
        'has_api',
        'requires_scraping',
        'scraping_enabled',
        'is_active',
        'created_at',
    ]

    search_fields = [
        'name',
        'slug',
        'website_url',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_scraped_at',
        'job_count',
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'name',
                'slug',
                'website_url',
                'logo_url',
            )
        }),
        ('API/Scraping Configuration', {
            'fields': (
                'has_api',
                'api_endpoint',
                'requires_scraping',
                'scraping_enabled',
            )
        }),
        ('Geographic Focus', {
            'fields': ('target_countries',)
        }),
        ('Status', {
            'fields': (
                'is_active',
                'last_scraped_at',
                'job_count',
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

    prepopulated_fields = {'slug': ('name',)}

    def website_url_link(self, obj):
        """Display website URL as clickable link"""
        return format_html('<a href="{}" target="_blank">{}</a>', obj.website_url, obj.website_url[:50])
    website_url_link.short_description = 'Website'

    def has_api_badge(self, obj):
        """Display API status as badge"""
        if obj.has_api:
            return format_html('<span style="background-color: green; color: white; padding: 3px 8px; border-radius: 3px;">API</span>')
        return format_html('<span style="background-color: gray; color: white; padding: 3px 8px; border-radius: 3px;">No API</span>')
    has_api_badge.short_description = 'API'

    def scraping_enabled_badge(self, obj):
        """Display scraping status as badge"""
        if obj.scraping_enabled:
            return format_html('<span style="background-color: blue; color: white; padding: 3px 8px; border-radius: 3px;">Scraping ON</span>')
        return format_html('<span style="background-color: gray; color: white; padding: 3px 8px; border-radius: 3px;">Scraping OFF</span>')
    scraping_enabled_badge.short_description = 'Scraping'

    def is_active_badge(self, obj):
        """Display active status as badge"""
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">● Active</span>')
        return format_html('<span style="color: gray;">○ Inactive</span>')
    is_active_badge.short_description = 'Status'

    def job_count(self, obj):
        """Get number of jobs from this platform"""
        return obj.jobs.count()
    job_count.short_description = 'Jobs'

    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        qs = super().get_queryset(request)
        return qs.annotate(jobs_count=Count('jobs'))


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for Jobs"""

    list_display = [
        'title',
        'company_name',
        'platform_badge',
        'location_display',
        'job_type_badge',
        'experience_level_badge',
        'salary_display',
        'is_active_badge',
        'posted_date',
    ]

    list_filter = [
        'platform',
        'job_type',
        'experience_level',
        'is_remote',
        'location_country',
        'is_active',
        'posted_date',
        'created_at',
    ]

    search_fields = [
        'title',
        'company_name',
        'external_id',
        'description',
        'location_city',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_fetched_at',
        'cache_expires_at',
        'is_expired_display',
        'skill_count',
    ]

    autocomplete_fields = ['platform']

    fieldsets = (
        ('Job Identification', {
            'fields': (
                'id',
                'platform',
                'external_id',
                'external_url',
            )
        }),
        ('Job Information', {
            'fields': (
                'title',
                'company_name',
                'company_logo_url',
                'description',
                'requirements',
                'responsibilities',
            )
        }),
        ('Location', {
            'fields': (
                'location_city',
                'location_country',
                'is_remote',
                'remote_type',
            )
        }),
        ('Employment Details', {
            'fields': (
                'job_type',
                'experience_level',
                'experience_years_min',
                'experience_years_max',
            )
        }),
        ('Salary', {
            'fields': (
                'salary_min',
                'salary_max',
                'salary_currency',
                'salary_period',
                'salary_disclosed',
            )
        }),
        ('Application Details', {
            'fields': (
                'application_deadline',
                'posted_date',
            )
        }),
        ('Platform Metadata', {
            'fields': ('platform_metadata',),
            'classes': ('collapse',)
        }),
        ('Caching & Status', {
            'fields': (
                'is_active',
                'last_fetched_at',
                'cache_expires_at',
                'is_expired_display',
            )
        }),
        ('Skills', {
            'fields': ('skill_count',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def platform_badge(self, obj):
        """Display platform as badge"""
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            obj.platform.name
        )
    platform_badge.short_description = 'Platform'

    def location_display(self, obj):
        """Display location with remote badge"""
        location = f"{obj.location_city}, {obj.location_country}" if obj.location_city else obj.location_country
        if obj.is_remote:
            return format_html('{} <span style="color: green;">Remote</span>', location)
        return location
    location_display.short_description = 'Location'

    def job_type_badge(self, obj):
        """Display job type as badge"""
        colors = {
            'full_time': '#27ae60',
            'part_time': '#3498db',
            'contract': '#9b59b6',
            'internship': '#f39c12',
            'freelance': '#e74c3c',
        }
        color = colors.get(obj.job_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_job_type_display() if obj.job_type else 'N/A'
        )
    job_type_badge.short_description = 'Type'

    def experience_level_badge(self, obj):
        """Display experience level as badge"""
        colors = {
            'entry': '#27ae60',
            'mid': '#3498db',
            'senior': '#9b59b6',
            'lead': '#e67e22',
            'executive': '#e74c3c',
        }
        color = colors.get(obj.experience_level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_experience_level_display() if obj.experience_level else 'N/A'
        )
    experience_level_badge.short_description = 'Level'

    def salary_display(self, obj):
        """Display salary range"""
        return obj.salary_range_display
    salary_display.short_description = 'Salary'

    def is_active_badge(self, obj):
        """Display active status"""
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">● Active</span>')
        return format_html('<span style="color: gray;">○ Inactive</span>')
    is_active_badge.short_description = 'Status'

    def is_expired_display(self, obj):
        """Display cache expiry status"""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        return format_html('<span style="color: green;">Fresh</span>')
    is_expired_display.short_description = 'Cache Status'

    def skill_count(self, obj):
        """Get number of skills for this job"""
        return obj.job_skills.count()
    skill_count.short_description = 'Skills'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('platform')


@admin.register(JobSkill)
class JobSkillAdmin(admin.ModelAdmin):
    """Admin interface for Job Skills"""

    list_display = [
        'skill_name',
        'job_title',
        'is_required_badge',
        'proficiency_level_badge',
        'years_required',
        'created_at',
    ]

    list_filter = [
        'is_required',
        'proficiency_level',
        'created_at',
    ]

    search_fields = [
        'skill__name',
        'job__title',
        'job__company_name',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]

    autocomplete_fields = ['job', 'skill']

    fieldsets = (
        ('Relationships', {
            'fields': (
                'id',
                'job',
                'skill',
            )
        }),
        ('Skill Requirements', {
            'fields': (
                'is_required',
                'proficiency_level',
                'years_required',
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

    def skill_name(self, obj):
        """Get skill name"""
        return obj.skill.name
    skill_name.short_description = 'Skill'
    skill_name.admin_order_field = 'skill__name'

    def job_title(self, obj):
        """Get job title"""
        return obj.job.title[:50]
    job_title.short_description = 'Job'

    def is_required_badge(self, obj):
        """Display required status as badge"""
        if obj.is_required:
            return format_html('<span style="background-color: red; color: white; padding: 3px 8px; border-radius: 3px;">Required</span>')
        return format_html('<span style="background-color: gray; color: white; padding: 3px 8px; border-radius: 3px;">Nice-to-have</span>')
    is_required_badge.short_description = 'Required'

    def proficiency_level_badge(self, obj):
        """Display proficiency level as badge"""
        colors = {
            'beginner': '#27ae60',
            'intermediate': '#3498db',
            'advanced': '#9b59b6',
            'expert': '#e74c3c',
        }
        color = colors.get(obj.proficiency_level, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_proficiency_level_display() if obj.proficiency_level else 'N/A'
        )
    proficiency_level_badge.short_description = 'Proficiency'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('job', 'skill')


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    """Admin interface for Saved Jobs"""

    list_display = [
        'user_name',
        'job_title',
        'company_name',
        'created_at',
    ]

    list_filter = [
        'created_at',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'job__title',
        'job__company_name',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]

    autocomplete_fields = ['user', 'job']

    fieldsets = (
        ('Relationships', {
            'fields': (
                'id',
                'user',
                'job',
            )
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def user_name(self, obj):
        """Get user name"""
        return obj.user.username
    user_name.short_description = 'User'
    user_name.admin_order_field = 'user__username'

    def job_title(self, obj):
        """Get job title"""
        return obj.job.title[:50]
    job_title.short_description = 'Job'

    def company_name(self, obj):
        """Get company name"""
        return obj.job.company_name
    company_name.short_description = 'Company'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'job')


@admin.register(MarketInsight)
class MarketInsightAdmin(admin.ModelAdmin):
    """Admin interface for Market Insights"""

    list_display = [
        'insight_type_badge',
        'career_field',
        'country',
        'period_display',
        'total_jobs_analyzed',
        'generated_at',
    ]

    list_filter = [
        'insight_type',
        'career_field',
        'country',
        'generated_at',
    ]

    search_fields = [
        'career_field',
        'country',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'generated_at',
    ]

    fieldsets = (
        ('Insight Information', {
            'fields': (
                'id',
                'insight_type',
                'career_field',
                'country',
            )
        }),
        ('Data Period', {
            'fields': (
                'data_period_start',
                'data_period_end',
            )
        }),
        ('Analytics Data', {
            'fields': (
                'insights_data',
                'total_jobs_analyzed',
            )
        }),
        ('Timestamps', {
            'fields': (
                'generated_at',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def insight_type_badge(self, obj):
        """Display insight type as badge"""
        colors = {
            'job_demand': '#3498db',
            'salary_trend': '#27ae60',
            'skill_trend': '#9b59b6',
            'company_hiring': '#e67e22',
            'location_trend': '#f39c12',
        }
        color = colors.get(obj.insight_type, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_insight_type_display()
        )
    insight_type_badge.short_description = 'Type'

    def period_display(self, obj):
        """Display data period"""
        return f"{obj.data_period_start} to {obj.data_period_end}"
    period_display.short_description = 'Period'


@admin.register(SkillDemand)
class SkillDemandAdmin(admin.ModelAdmin):
    """Admin interface for Skill Demand"""

    list_display = [
        'skill_name',
        'country',
        'month',
        'demand_count',
        'trend_badge',
        'salary_range_display',
    ]

    list_filter = [
        'trend_direction',
        'country',
        'month',
    ]

    search_fields = [
        'skill__name',
        'country',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'trend_display_formatted',
    ]

    autocomplete_fields = ['skill']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'skill',
                'country',
                'month',
            )
        }),
        ('Demand Metrics', {
            'fields': (
                'demand_count',
                'trend_direction',
                'trend_percentage',
                'trend_display_formatted',
            )
        }),
        ('Salary Data', {
            'fields': (
                'average_salary_min',
                'average_salary_max',
            )
        }),
        ('Top Job Titles', {
            'fields': ('top_job_titles',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def skill_name(self, obj):
        """Get skill name"""
        return obj.skill.name
    skill_name.short_description = 'Skill'
    skill_name.admin_order_field = 'skill__name'

    def trend_badge(self, obj):
        """Display trend as badge with symbol"""
        colors = {
            'rising': '#27ae60',
            'stable': '#3498db',
            'declining': '#e74c3c',
        }
        color = colors.get(obj.trend_direction, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.trend_display
        )
    trend_badge.short_description = 'Trend'

    def salary_range_display(self, obj):
        """Display average salary range"""
        if not obj.average_salary_min and not obj.average_salary_max:
            return "N/A"
        if obj.average_salary_min and obj.average_salary_max:
            return f"EGP {obj.average_salary_min:,.0f} - {obj.average_salary_max:,.0f}"
        elif obj.average_salary_min:
            return f"EGP {obj.average_salary_min:,.0f}+"
        else:
            return f"Up to EGP {obj.average_salary_max:,.0f}"
    salary_range_display.short_description = 'Avg Salary'

    def trend_display_formatted(self, obj):
        """Get formatted trend display for readonly field"""
        return obj.trend_display
    trend_display_formatted.short_description = 'Trend Display'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('skill')
