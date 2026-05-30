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
from apps.jobs.models import JobPlatform, Job, JobSkill, SavedJob, SkillDemand, MarketInsight
from apps.jobs.services import JobService


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
    is_saved = serializers.SerializerMethodField()
    external_action_available = serializers.SerializerMethodField()
    skill_match_summary = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()

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
            'is_saved',
            'external_action_available',
            'skill_match_summary',
            'match_score',
        ]

    def get_location(self, obj):
        """Return formatted location string."""
        if obj.location_city and obj.location_country:
            return f"{obj.location_city}, {obj.location_country}"
        return obj.location_city or obj.location_country or "Not specified"

    def get_is_saved(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return SavedJob.objects.filter(user=user, job=obj, is_deleted=False).exists()

    def get_external_action_available(self, obj):
        return bool(obj.external_url)

    def get_skill_match_summary(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return "Sign in to compare this role with your skills."

        user_skill_names = set(
            user.user_skills.filter(is_deleted=False).values_list('skill__name', flat=True)
        )
        if not user_skill_names:
            return "Add skills to your profile to see a better match signal."

        job_skill_names = set(obj.job_skills.values_list('skill__name', flat=True))
        overlap = user_skill_names.intersection(job_skill_names)
        if overlap:
            return f"Matches {len(overlap)} of your tracked skills."
        return "Few direct matches yet. Review this role against your roadmap focus."

    def get_match_score(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        return JobService.compute_match_score(obj, user)["match_score"]


class JobSerializer(serializers.ModelSerializer):
    """Complete job information."""
    platform = JobPlatformSerializer(read_only=True)
    skills = JobSkillSerializer(many=True, read_only=True, source='job_skills')
    location = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    external_action_available = serializers.SerializerMethodField()
    skill_match_summary = serializers.SerializerMethodField()

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
            'is_saved',
            'external_action_available',
            'skill_match_summary',
            'created_at',
        ]

    def get_location(self, obj):
        """Return formatted location string."""
        if obj.location_city and obj.location_country:
            return f"{obj.location_city}, {obj.location_country}"
        return obj.location_city or obj.location_country or "Not specified"

    def get_is_saved(self, obj):
        return JobListSerializer(context=self.context).get_is_saved(obj)

    def get_external_action_available(self, obj):
        return bool(obj.external_url)

    def get_skill_match_summary(self, obj):
        return JobListSerializer(context=self.context).get_skill_match_summary(obj)


class SavedJobSerializer(serializers.ModelSerializer):
    """Saved job with full job details."""
    job = JobListSerializer(read_only=True)

    class Meta:
        model = SavedJob
        fields = [
            'id',
            'job',
            'notes',
            'created_at',
        ]
        read_only_fields = ['created_at']


class SavedJobCreateSerializer(serializers.ModelSerializer):
    """Create a saved job."""

    class Meta:
        model = SavedJob
        fields = ['job', 'notes']

    def create(self, validated_data):
        # Add user from request context
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


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
