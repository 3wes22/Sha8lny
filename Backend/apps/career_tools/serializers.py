"""
Career Tools Service Serializers

Implements serializers for resume/CV builder and portfolio management.

SRS References:
- FR-22: Resume/CV Builder
- FR-23: ATS-Optimized Resume Generation
- FR-24: Portfolio Builder
"""

from rest_framework import serializers
from apps.career_tools.models import Resume, Portfolio


class ResumeListSerializer(serializers.ModelSerializer):
    """Minimal resume info for list views."""
    ats_grade = serializers.CharField(source='ats_grade_display', read_only=True)
    completeness = serializers.FloatField(source='completeness_percentage', read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id',
            'title',
            'template_name',
            'is_primary',
            'is_ats_optimized',
            'ats_score',
            'ats_grade',
            'completeness',
            'version',
            'created_at',
            'updated_at',
        ]


class ResumeSerializer(serializers.ModelSerializer):
    """Complete resume information."""
    ats_grade = serializers.CharField(source='ats_grade_display', read_only=True)
    completeness = serializers.FloatField(source='completeness_percentage', read_only=True)
    has_files = serializers.BooleanField(read_only=True)
    available_formats = serializers.CharField(source='file_formats_available', read_only=True)

    class Meta:
        model = Resume
        fields = [
            'id',
            'user',
            'title',
            'template_name',
            'personal_info',
            'work_experience',
            'education',
            'skills',
            'certifications',
            'projects',
            'languages',
            'is_ats_optimized',
            'ats_score',
            'ats_grade',
            'ats_suggestions',
            'pdf_file',
            'docx_file',
            'has_files',
            'available_formats',
            'is_primary',
            'version',
            'completeness',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'pdf_file', 'docx_file', 'created_at', 'updated_at']


class ResumeCreateSerializer(serializers.ModelSerializer):
    """Create/update resume."""

    class Meta:
        model = Resume
        fields = [
            'title',
            'template_name',
            'personal_info',
            'work_experience',
            'education',
            'skills',
            'certifications',
            'projects',
            'languages',
            'is_primary',
        ]

    def create(self, validated_data):
        """Create resume for current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PortfolioListSerializer(serializers.ModelSerializer):
    """Minimal portfolio info for list views."""

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'title',
            'custom_url_slug',
            'is_public',
            'view_count',
            'theme',
            'created_at',
            'updated_at',
        ]


class PortfolioSerializer(serializers.ModelSerializer):
    """Complete portfolio information."""

    class Meta:
        model = Portfolio
        fields = [
            'id',
            'user',
            'title',
            'description',
            'projects',
            'achievements',
            'testimonials',
            'theme',
            'custom_styles',
            'is_public',
            'custom_url_slug',
            'view_count',
            'last_viewed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'view_count', 'last_viewed_at', 'created_at', 'updated_at']


class PortfolioCreateSerializer(serializers.ModelSerializer):
    """Create/update portfolio."""

    class Meta:
        model = Portfolio
        fields = [
            'title',
            'description',
            'projects',
            'achievements',
            'testimonials',
            'theme',
            'custom_styles',
            'is_public',
            'custom_url_slug',
        ]

    def create(self, validated_data):
        """Create portfolio for current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
