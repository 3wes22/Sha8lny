"""
Jobs Service Serializers

Implements job market data serializers for search, filtering, and insights.

SRS References:
- FR-18: Job Scraping and Normalization
- FR-19: Job-Skill Matching
- FR-20: Market Insights
- FR-21: Skill Demand Analysis
"""

from rest_framework import serializers
from apps.jobs.models import JobPlatform, Job, JobSkill, SkillDemand, MarketInsight


class JobPlatformSerializer(serializers.ModelSerializer):
    """Job platform information."""

    class Meta:
        model = JobPlatform
        fields = [
            'id',
            'name',
            'slug',
            'website_url',
            'logo_url',
            'is_active',
            'target_countries',
        ]


class JobSkillSerializer(serializers.ModelSerializer):
    """Job skill requirement details."""
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = JobSkill
        fields = [
            'id',
            'skill',
            'skill_name',
            'proficiency_level',
            'years_required',
            'is_required',
        ]


class JobListSerializer(serializers.ModelSerializer):
    """Minimal job info for list views."""
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    location = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'company_name',
            'platform',
            'platform_name',
            'location',
            'location_city',
            'location_country',
            'job_type',
            'experience_level',
            'salary_min',
            'salary_max',
            'salary_currency',
            'is_remote',
            'posted_date',
        ]

    def get_location(self, obj):
        """Return formatted location string."""
        if obj.location_city and obj.location_country:
            return f"{obj.location_city}, {obj.location_country}"
        return obj.location_city or obj.location_country or "Not specified"


class JobSerializer(serializers.ModelSerializer):
    """Complete job information."""
    platform = JobPlatformSerializer(read_only=True)
    skills = JobSkillSerializer(many=True, read_only=True, source='job_skills')
    location = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id',
            'platform',
            'title',
            'company_name',
            'company_logo_url',
            'location',
            'location_city',
            'location_country',
            'remote_type',
            'is_remote',
            'job_type',
            'experience_level',
            'experience_years_min',
            'experience_years_max',
            'description',
            'requirements',
            'responsibilities',
            'salary_min',
            'salary_max',
            'salary_currency',
            'salary_period',
            'salary_disclosed',
            'external_url',
            'application_deadline',
            'posted_date',
            'skills',
            'created_at',
        ]

    def get_location(self, obj):
        """Return formatted location string."""
        if obj.location_city and obj.location_country:
            return f"{obj.location_city}, {obj.location_country}"
        return obj.location_city or obj.location_country or "Not specified"


class JobSearchSerializer(serializers.Serializer):
    """Search and filter jobs."""
    query = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    job_type = serializers.ChoiceField(
        choices=['full_time', 'part_time', 'contract', 'internship', 'freelance'],
        required=False
    )
    experience_level = serializers.ChoiceField(
        choices=['entry', 'mid', 'senior', 'lead', 'executive'],
        required=False
    )
    is_remote = serializers.BooleanField(required=False)
    min_salary = serializers.IntegerField(required=False, min_value=0)
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )


class SkillDemandSerializer(serializers.ModelSerializer):
    """Skill demand analytics."""
    skill_name = serializers.CharField(source='skill.name', read_only=True)

    class Meta:
        model = SkillDemand
        fields = [
            'id',
            'skill',
            'skill_name',
            'country',
            'month',
            'demand_count',
            'trend_direction',
            'trend_percentage',
            'average_salary_min',
            'average_salary_max',
            'top_job_titles',
            'created_at',
        ]


class MarketInsightSerializer(serializers.ModelSerializer):
    """Market insights."""

    class Meta:
        model = MarketInsight
        fields = [
            'id',
            'insight_type',
            'career_field',
            'country',
            'data_period_start',
            'data_period_end',
            'insights_data',
            'total_jobs_analyzed',
            'generated_at',
            'created_at',
        ]
