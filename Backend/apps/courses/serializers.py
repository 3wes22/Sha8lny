"""
Courses Service Serializers

Implements course aggregation, search, and recommendation serializers.

SRS Reference: Implied by FR-11 (Course Association)
"""

from rest_framework import serializers
from apps.courses.models import Course, CoursePlatform, CourseCategory, UserCourseEnrollment


class CoursePlatformSerializer(serializers.ModelSerializer):
    """Course platform serializer."""

    class Meta:
        model = CoursePlatform
        fields = [
            'id',
            'name',
            'slug',
            'website_url',
            'logo_url',
            'is_active',
        ]


class CourseCategorySerializer(serializers.ModelSerializer):
    """Course category serializer."""

    class Meta:
        model = CourseCategory
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'parent_category',
        ]


class CourseListSerializer(serializers.ModelSerializer):
    """Minimal course info for list views."""
    platform_name = serializers.CharField(source='platform.name', read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'platform_name',
            'price',
            'currency',
            'rating',
            'difficulty_level',
            'thumbnail_url',
        ]


class CourseSerializer(serializers.ModelSerializer):
    """Complete course information."""
    platform = CoursePlatformSerializer(read_only=True)
    categories = CourseCategorySerializer(many=True, read_only=True)
    skills_covered = serializers.ListField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'platform',
            'instructor',
            'course_url',
            'thumbnail_url',
            'price',
            'currency',
            'discount_price',
            'rating',
            'number_of_reviews',
            'number_of_students',
            'duration_hours',
            'difficulty_level',
            'language',
            'has_certificate',
            'is_active',
            'skills_covered',
            'categories',
            'last_updated',
            'created_at',
        ]


class UserCourseEnrollmentSerializer(serializers.ModelSerializer):
    """User course enrollment tracking."""
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = UserCourseEnrollment
        fields = [
            'id',
            'course',
            'enrollment_status',
            'progress_percentage',
            'started_at',
            'completed_at',
            'certificate_url',
            'notes',
        ]


class CourseEnrollSerializer(serializers.Serializer):
    """Enroll in a course."""
    course_id = serializers.UUIDField(required=True)

    def validate_course_id(self, value):
        """Validate course exists."""
        if not Course.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Course not found or inactive")
        return value


class CourseSearchSerializer(serializers.Serializer):
    """Search courses."""
    query = serializers.CharField(required=False, allow_blank=True)
    platform = serializers.CharField(required=False)
    difficulty = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'all_levels'],
        required=False
    )
    min_rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        required=False,
        min_value=0,
        max_value=5
    )
    is_free = serializers.BooleanField(required=False)
    has_certificate = serializers.BooleanField(required=False)
    language = serializers.CharField(required=False)
