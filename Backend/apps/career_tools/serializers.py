"""
Career Tools Service Serializers

Implements serializers for resume/CV builder and portfolio management.

SRS References:
- FR-22: Resume/CV Builder
- FR-23: ATS-Optimized Resume Generation
- FR-24: Portfolio Builder
"""

from rest_framework import serializers
from apps.career_tools.models import Resume, ResumeSection, Portfolio, PortfolioProject


class ResumeSectionSerializer(serializers.ModelSerializer):
    """Resume section serializer."""

    class Meta:
        model = ResumeSection
        fields = [
            'id',
            'section_type',
            'title',
            'content',
            'order',
            'is_visible',
        ]


class ResumeListSerializer(serializers.ModelSerializer):
    """Minimal resume info for list views."""

    class Meta:
        model = Resume
        fields = [
            'id',
            'title',
            'template',
            'is_primary',
            'is_ats_optimized',
            'last_generated_at',
            'created_at',
        ]


class ResumeSerializer(serializers.ModelSerializer):
    """Complete resume information."""
    sections = ResumeSectionSerializer(many=True, read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id',
            'user',
            'title',
            'template',
            'full_name',
            'email',
            'phone',
            'location',
            'professional_summary',
            'linkedin_url',
            'github_url',
            'website_url',
            'sections',
            'is_primary',
            'is_ats_optimized',
            'ats_score',
            'last_generated_at',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'ats_score', 'last_generated_at', 'created_at', 'updated_at']


class PortfolioProjectSerializer(serializers.ModelSerializer):
    """Portfolio project serializer."""

    class Meta:
        model = PortfolioProject
        fields = [
            'id',
            'title',
            'description',
            'technologies',
            'project_url',
            'github_url',
            'image_url',
            'start_date',
            'end_date',
            'is_featured',
            'order',
        ]


class PortfolioListSerializer(serializers.ModelSerializer):
    """Minimal portfolio info for list views."""

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'title',
            'slug',
            'is_public',
            'view_count',
            'created_at',
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    """Complete portfolio information."""
    projects = PortfolioProjectSerializer(many=True, read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'user',
            'title',
            'slug',
            'bio',
            'tagline',
            'profile_image_url',
            'theme',
            'custom_css',
            'projects',
            'is_public',
            'view_count',
            'seo_title',
            'seo_description',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'view_count', 'created_at', 'updated_at']
