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
from apps.jobs.models import JobPlatform, Job, JobSkillRequirement, SkillDemandInsight


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


class JobSkillRequirementSerializer(serializers.ModelSerializer):
    """Job skill requirement details."""

    class Meta:
        model = JobSkillRequirement
        fields = [
            'id',
            'skill',
            'proficiency_level',
            'years_required',
            'is_required',
            'priority',
        ]


class JobListSerializer(serializers.ModelSerializer):
    """Minimal job info for list views."""
    platform_name = serializers.CharField(source='platform.name', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'title',
            'company_name',
            'platform',
            'platform_name',
            'location',
            'job_type',
            'experience_level',
            'salary_min',
            'salary_max',
            'currency',
            'is_remote',
            'posted_date',
        ]


class JobSerializer(serializers.ModelSerializer):
    """Complete job information."""
    platform = JobPlatformSerializer(read_only=True)
    skill_requirements = JobSkillRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = [
            'id',
            'platform',
            'title',
            'company_name',
            'company_website',
            'location',
            'job_type',
            'experience_level',
            'description',
            'requirements',
            'benefits',
            'salary_min',
            'salary_max',
            'currency',
            'is_remote',
            'application_url',
            'posted_date',
            'expiry_date',
            'skill_requirements',
            'normalized_at',
            'created_at',
        ]


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


class SkillDemandInsightSerializer(serializers.ModelSerializer):
    """Skill demand analytics."""

    class Meta:
        model = SkillDemandInsight
        fields = [
            'id',
            'skill',
            'demand_score',
            'job_count',
            'average_salary',
            'growth_percentage',
            'trending',
            'top_job_titles',
            'top_companies',
            'period_start',
            'period_end',
        ]
