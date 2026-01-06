"""
Courses Service Layer

Handles course aggregation, search, and recommendations from multiple platforms.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Avg, Count

from .models import Course, CourseProvider
from apps.users.models import User


class CourseProviderService:
    """Service for course provider management"""

    @staticmethod
    def get_all_providers() -> List[CourseProvider]:
        """Get all active course providers"""
        return list(CourseProvider.objects.filter(
            is_active=True,
            is_deleted=False
        ).order_by('name'))

    @staticmethod
    def get_provider_by_name(name: str) -> Optional[CourseProvider]:
        """Get provider by name"""
        try:
            return CourseProvider.objects.get(
                name__iexact=name,
                is_deleted=False
            )
        except CourseProvider.DoesNotExist:
            return None


class CourseService:
    """Service for course management and search"""

    @staticmethod
    def search_courses(
        query: str,
        provider: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        min_rating: Optional[float] = None,
        is_free: Optional[bool] = None,
        limit: int = 50
    ) -> List[Course]:
        """
        Search courses with filters.

        Args:
            query: Search query
            provider: Filter by provider name
            difficulty_level: Filter by difficulty
            min_rating: Minimum average rating
            is_free: Filter free/paid courses
            limit: Maximum results

        Returns:
            List[Course]: Matching courses
        """
        queryset = Course.objects.filter(is_deleted=False)

        # Text search
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(skills_covered__icontains=query)
            )

        # Provider filter
        if provider:
            queryset = queryset.filter(provider__name__iexact=provider)

        # Difficulty filter
        if difficulty_level:
            queryset = queryset.filter(difficulty_level=difficulty_level)

        # Rating filter
        if min_rating:
            queryset = queryset.filter(average_rating__gte=min_rating)

        # Price filter
        if is_free is not None:
            if is_free:
                queryset = queryset.filter(
                    Q(price=Decimal('0.00')) | Q(is_free=True)
                )
            else:
                queryset = queryset.filter(
                    price__gt=Decimal('0.00'),
                    is_free=False
                )

        return list(queryset.select_related('provider')[:limit])

    @staticmethod
    def get_course_by_id(course_id: str) -> Optional[Course]:
        """Get course by ID"""
        try:
            return Course.objects.select_related('provider').get(
                id=course_id,
                is_deleted=False
            )
        except Course.DoesNotExist:
            return None

    @staticmethod
    def get_courses_by_provider(provider_name: str) -> List[Course]:
        """Get all courses from a specific provider"""
        return list(Course.objects.filter(
            provider__name__iexact=provider_name,
            is_deleted=False
        ).select_related('provider'))

    @staticmethod
    def get_popular_courses(limit: int = 20) -> List[Course]:
        """Get popular courses by enrollment count"""
        return list(Course.objects.filter(
            is_deleted=False
        ).order_by('-enrollment_count')[:limit])

    @staticmethod
    def get_top_rated_courses(
        min_rating: float = 4.0,
        limit: int = 20
    ) -> List[Course]:
        """Get top-rated courses"""
        return list(Course.objects.filter(
            average_rating__gte=min_rating,
            is_deleted=False
        ).order_by('-average_rating', '-review_count')[:limit])

    @staticmethod
    def get_free_courses(limit: int = 50) -> List[Course]:
        """Get free courses"""
        return list(Course.objects.filter(
            Q(is_free=True) | Q(price=Decimal('0.00')),
            is_deleted=False
        )[:limit])

    @staticmethod
    def get_courses_by_skills(skills: List[str]) -> List[Course]:
        """
        Find courses that teach specific skills.

        Args:
            skills: List of skill names

        Returns:
            List[Course]: Courses covering those skills
        """
        queryset = Course.objects.filter(is_deleted=False)

        # Build OR query for skills
        skill_query = Q()
        for skill in skills:
            skill_query |= Q(skills_covered__icontains=skill)

        queryset = queryset.filter(skill_query)

        return list(queryset.select_related('provider')[:50])

    @staticmethod
    def recommend_courses_for_user(
        user: User,
        target_skills: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[Course]:
        """
        Recommend courses for user based on their profile and target skills.

        Args:
            user: User instance
            target_skills: Optional list of target skills
            limit: Maximum recommendations

        Returns:
            List[Course]: Recommended courses
        """
        # Get user's current skills from UserSkill
        from apps.users.models import UserSkill

        user_skills = UserSkill.objects.filter(
            user=user,
            is_deleted=False
        ).values_list('skill__name', flat=True)

        current_skills = set(user_skills)

        # If target skills provided, use those; otherwise get all available courses
        if target_skills:
            # Find courses teaching target skills user doesn't have
            missing_skills = set(target_skills) - current_skills
            courses = CourseService.get_courses_by_skills(list(missing_skills))
        else:
            # Get popular courses user might be interested in
            courses = CourseService.get_popular_courses(limit * 2)

        # TODO: Add collaborative filtering or ML-based recommendations

        return courses[:limit]

    @staticmethod
    @transaction.atomic
    def create_course(
        provider: CourseProvider,
        title: str,
        description: str,
        course_url: str,
        **kwargs
    ) -> Course:
        """
        Create a new course (usually from external API sync).

        Args:
            provider: CourseProvider instance
            title: Course title
            description: Course description
            course_url: URL to course page
            **kwargs: Additional course fields

        Returns:
            Course: Created course
        """
        course = Course.objects.create(
            provider=provider,
            title=title,
            description=description,
            course_url=course_url,
            **kwargs
        )
        return course

    @staticmethod
    def update_course_metadata(course: Course, **fields) -> Course:
        """Update course metadata (ratings, enrollment, etc.)"""
        allowed_fields = [
            'average_rating', 'review_count', 'enrollment_count',
            'last_updated', 'thumbnail_url', 'is_free', 'price',
            'currency', 'duration_hours', 'language'
        ]

        for field, value in fields.items():
            if field in allowed_fields:
                setattr(course, field, value)

        course.save()
        return course

    @staticmethod
    def get_course_statistics() -> Dict[str, Any]:
        """Get overall course statistics"""
        total_courses = Course.objects.filter(is_deleted=False).count()
        free_courses = Course.objects.filter(
            Q(is_free=True) | Q(price=Decimal('0.00')),
            is_deleted=False
        ).count()

        avg_rating = Course.objects.filter(
            is_deleted=False,
            average_rating__isnull=False
        ).aggregate(Avg('average_rating'))['average_rating__avg']

        by_provider = Course.objects.filter(
            is_deleted=False
        ).values('provider__name').annotate(
            count=Count('id')
        ).order_by('-count')

        by_difficulty = Course.objects.filter(
            is_deleted=False
        ).values('difficulty_level').annotate(
            count=Count('id')
        )

        return {
            'total_courses': total_courses,
            'free_courses': free_courses,
            'paid_courses': total_courses - free_courses,
            'average_rating': round(avg_rating or 0, 2),
            'by_provider': list(by_provider),
            'by_difficulty': list(by_difficulty)
        }
