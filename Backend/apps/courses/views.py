"""
Courses Service Views

Implements course aggregation, search, and recommendation APIs.
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q

from apps.courses.models import Course, CoursePlatform
from apps.courses.serializers import (
    CourseSerializer,
    CourseListSerializer,
    CoursePlatformSerializer,
    CourseSearchSerializer,
)


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Course listing and search.

    GET /courses/ - List all courses
    GET /courses/{id}/ - Get course details
    GET /courses/search/ - Search courses
    GET /courses/recommended/ - Get recommended courses
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Course.objects.filter(is_published=True, is_deleted=False)

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by platform
        platform = self.request.query_params.get('platform')
        if platform:
            queryset = queryset.filter(platform__slug=platform)

        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(level=difficulty)

        # Filter by free/paid
        is_free = self.request.query_params.get('is_free')
        if is_free == 'true':
            queryset = queryset.filter(price=0)

        return queryset.select_related('platform')

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search courses with filters."""
        serializer = CourseSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        queryset = self.get_queryset()

        # Text search
        query = serializer.validated_data.get('query')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(instructor__icontains=query)
            )

        # Apply filters
        if serializer.validated_data.get('min_rating'):
            queryset = queryset.filter(rating__gte=serializer.validated_data['min_rating'])

        if serializer.validated_data.get('has_certificate'):
            queryset = queryset.filter(has_certificate=True)

        page = self.paginate_queryset(queryset)
        if page is not None:
            result_serializer = CourseListSerializer(page, many=True)
            return self.get_paginated_response(result_serializer.data)

        result_serializer = CourseListSerializer(queryset, many=True)
        return Response(result_serializer.data)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        """Return popular published courses (roadmap course matching uses course_index)."""
        courses = self.get_queryset().order_by('-rating', '-total_enrollments')[:10]
        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)


class CoursePlatformViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List course platforms.

    GET /platforms/ - List all platforms
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CoursePlatformSerializer
    queryset = CoursePlatform.objects.filter(is_active=True, is_deleted=False)
