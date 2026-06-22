"""
Progress Service Views

Implements REST API views for progress tracking, course completions,
milestone achievements, and time logging.

SRS Reference: Implied by FR-12 (Progress Tracking)
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Avg, Count, Q, Max
from django.db import models
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.progress.models import (
    UserProgress,
    CourseCompletion,
    MilestoneAchievement,
    TimeLog
)
from apps.progress.serializers import (
    UserProgressSerializer,
    UserProgressListSerializer,
    CourseCompletionSerializer,
    CourseCompletionListSerializer,
    CourseCompletionCreateSerializer,
    CourseReviewSerializer,
    MilestoneAchievementSerializer,
    MilestoneAchievementListSerializer,
    TimeLogSerializer,
    TimeLogListSerializer,
    TimeLogCreateSerializer,
    ProgressStatsSerializer,
)
from apps.progress.services import (
    ProgressService,
    CourseCompletionService,
    MilestoneService,
    TimeLogService,
)
from apps.courses.models import Course
from apps.roadmaps.models import Roadmap, RoadmapCourse


# ============================================================================
# USER PROGRESS VIEWS
# ============================================================================

class UserProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View user progress records.

    Endpoints:
    - GET /progress/ - List all user's progress records
    - GET /progress/{id}/ - Get specific progress record
    - GET /progress/roadmap/{roadmap_id}/ - Get progress for specific roadmap
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return progress for current user only."""
        return UserProgress.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('roadmap', 'current_phase', 'current_milestone')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return UserProgressListSerializer
        return UserProgressSerializer

    @action(detail=False, methods=['get'], url_path='roadmap/(?P<roadmap_id>[^/.]+)')
    def by_roadmap(self, request, roadmap_id=None):
        """
        Get progress for specific roadmap.

        GET /progress/roadmap/{roadmap_id}/
        """
        try:
            roadmap = Roadmap.objects.get(
                id=roadmap_id,
                user=request.user,
                is_deleted=False
            )
        except Roadmap.DoesNotExist:
            return Response(
                {'error': 'Roadmap not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        progress = ProgressService.get_progress_snapshot(request.user, roadmap)
        serializer = UserProgressSerializer(progress)
        return Response(serializer.data)


# ============================================================================
# COURSE COMPLETION VIEWS
# ============================================================================

class CourseCompletionViewSet(viewsets.ModelViewSet):
    """
    Manage course completions.

    Endpoints:
    - GET /completions/ - List user's course completions
    - GET /completions/{id}/ - Get specific completion
    - POST /completions/ - Record course completion
    - PUT /completions/{id}/review/ - Add/update review
    - DELETE /completions/{id}/ - Delete completion record
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return completions for current user only."""
        return CourseCompletion.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('course', 'roadmap_course').order_by('-completed_at')

    def get_serializer_class(self):
        """Use appropriate serializer per action."""
        if self.action == 'list':
            return CourseCompletionListSerializer
        elif self.action == 'create':
            return CourseCompletionCreateSerializer
        elif self.action == 'review':
            return CourseReviewSerializer
        return CourseCompletionSerializer

    def create(self, request, *args, **kwargs):
        """
        Record course completion.

        POST /completions/

        Request Body:
        {
            "course_id": "uuid",
            "roadmap_course_id": "uuid",  // optional
            "started_at": "2024-01-01T10:00:00Z",
            "completed_at": "2024-01-15T18:00:00Z",
            "time_spent_hours": 25.5,  // optional
            "user_rating": 5,  // optional
            "user_review": "Great course!",  // optional
            "would_recommend": true,  // optional
            "certificate_url": "https://..."  // optional
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get course
        try:
            course = Course.objects.get(
                id=serializer.validated_data['course_id'],
                is_published=True
            )
        except Course.DoesNotExist:
            return Response(
                {'error': 'Course not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get roadmap course if provided
        roadmap_course = None
        if serializer.validated_data.get('roadmap_course_id'):
            try:
                roadmap_course = RoadmapCourse.objects.get(
                    id=serializer.validated_data['roadmap_course_id'],
                    milestone__phase__roadmap__user=request.user
                )
            except RoadmapCourse.DoesNotExist:
                return Response(
                    {'error': 'Roadmap course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Create completion using service
        completion = CourseCompletionService.record_completion(
            user=request.user,
            course=course,
            roadmap_course=roadmap_course,
            started_at=serializer.validated_data['started_at'],
            completed_at=serializer.validated_data['completed_at'],
            time_spent_hours=serializer.validated_data.get('time_spent_hours'),
            user_rating=serializer.validated_data.get('user_rating'),
            user_review=serializer.validated_data.get('user_review', ''),
            would_recommend=serializer.validated_data.get('would_recommend'),
            certificate_url=serializer.validated_data.get('certificate_url', '')
        )

        return Response(
            CourseCompletionSerializer(completion).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['put', 'patch'])
    def review(self, request, pk=None):
        """
        Add or update course review.

        PUT /completions/{id}/review/

        Request Body:
        {
            "user_rating": 5,
            "user_review": "Excellent course!",
            "would_recommend": true
        }
        """
        completion = self.get_object()
        serializer = CourseReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        completion.user_rating = serializer.validated_data['user_rating']
        completion.user_review = serializer.validated_data.get('user_review', completion.user_review)
        completion.would_recommend = serializer.validated_data.get('would_recommend', completion.would_recommend)
        completion.save()

        return Response(
            CourseCompletionSerializer(completion).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """Soft delete completion record."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(
            {'message': 'Course completion deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================================
# MILESTONE ACHIEVEMENT VIEWS
# ============================================================================

class MilestoneAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    View milestone achievements.

    Endpoints:
    - GET /achievements/ - List user's achievements
    - GET /achievements/{id}/ - Get specific achievement
    - GET /achievements/recent/ - Get recent achievements
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return achievements for current user only."""
        return MilestoneAchievement.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('milestone').order_by('-achieved_at')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return MilestoneAchievementListSerializer
        return MilestoneAchievementSerializer

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent achievements (last 30 days).

        GET /achievements/recent/
        """
        thirty_days_ago = timezone.now() - timedelta(days=30)
        achievements = self.get_queryset().filter(achieved_at__gte=thirty_days_ago)

        serializer = MilestoneAchievementListSerializer(achievements, many=True)
        return Response(serializer.data)


# ============================================================================
# TIME LOG VIEWS
# ============================================================================

class TimeLogViewSet(viewsets.ModelViewSet):
    """
    Manage time logs.

    Endpoints:
    - GET /timelogs/ - List user's time logs
    - GET /timelogs/{id}/ - Get specific time log
    - POST /timelogs/ - Create time log
    - DELETE /timelogs/{id}/ - Delete time log
    - GET /timelogs/today/ - Get today's time logs
    - GET /timelogs/week/ - Get this week's time logs
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return time logs for current user only."""
        return TimeLog.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('course', 'roadmap').order_by('-started_at')

    def get_serializer_class(self):
        """Use appropriate serializer per action."""
        if self.action == 'list':
            return TimeLogListSerializer
        elif self.action == 'create':
            return TimeLogCreateSerializer
        return TimeLogSerializer

    def create(self, request, *args, **kwargs):
        """
        Create time log entry.

        POST /timelogs/

        Request Body:
        {
            "course_id": "uuid",  // optional
            "roadmap_id": "uuid",  // optional
            "started_at": "2024-01-01T10:00:00Z",
            "ended_at": "2024-01-01T11:30:00Z",
            "duration_minutes": 90,  // optional, auto-calculated
            "activity_type": "course"  // course, practice, reading, project
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get course if provided
        course = None
        if serializer.validated_data.get('course_id'):
            try:
                course = Course.objects.get(
                    id=serializer.validated_data['course_id'],
                    is_published=True
                )
            except Course.DoesNotExist:
                return Response(
                    {'error': 'Course not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Get roadmap if provided
        roadmap = None
        if serializer.validated_data.get('roadmap_id'):
            try:
                roadmap = Roadmap.objects.get(
                    id=serializer.validated_data['roadmap_id'],
                    user=request.user,
                    is_deleted=False
                )
            except Roadmap.DoesNotExist:
                return Response(
                    {'error': 'Roadmap not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Create time log using service
        time_log = TimeLogService.log_time(
            user=request.user,
            started_at=serializer.validated_data['started_at'],
            ended_at=serializer.validated_data['ended_at'],
            activity_type=serializer.validated_data['activity_type'],
            course=course,
            roadmap=roadmap,
            duration_minutes=serializer.validated_data.get('duration_minutes')
        )

        return Response(
            TimeLogSerializer(time_log).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get today's time logs.

        GET /timelogs/today/
        """
        today = timezone.now().date()
        logs = self.get_queryset().filter(
            started_at__date=today
        )

        serializer = TimeLogListSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def week(self, request):
        """
        Get this week's time logs.

        GET /timelogs/week/
        """
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        logs = self.get_queryset().filter(
            started_at__date__gte=week_start
        )

        # Calculate total hours
        total_minutes = logs.aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        total_hours = round(total_minutes / 60, 2)

        serializer = TimeLogListSerializer(logs, many=True)
        return Response({
            'logs': serializer.data,
            'total_hours': total_hours,
            'week_start': week_start
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete time log."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(
            {'message': 'Time log deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )


# ============================================================================
# STATISTICS VIEWS
# ============================================================================

class ProgressStatsView(APIView):
    """
    Get user's progress statistics.

    GET /progress/stats/

    Returns:
    - total_learning_hours: Total hours logged
    - total_courses_completed: Total courses finished
    - total_milestones_achieved: Total milestones achieved
    - current_streak_days: Current learning streak
    - longest_streak_days: Longest streak achieved
    - roadmaps_in_progress: Active roadmaps
    - roadmaps_completed: Completed roadmaps
    - average_daily_hours: Average hours per day
    - this_week_hours: Hours logged this week
    - last_activity_date: Last learning activity
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get comprehensive progress statistics."""
        user = request.user

        # Total learning hours from time logs
        total_hours = TimeLog.objects.filter(
            user=user,
            is_deleted=False
        ).aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        total_hours = Decimal(str(round(total_hours / 60, 2)))

        # Course completions
        total_courses = CourseCompletion.objects.filter(
            user=user,
            is_deleted=False
        ).count()

        # Milestone achievements
        total_milestones = MilestoneAchievement.objects.filter(
            user=user,
            is_deleted=False
        ).count()

        # Streak data from progress records
        progress_records = UserProgress.objects.filter(
            user=user,
            is_deleted=False
        )

        current_streak = progress_records.aggregate(
            max_streak=models.Max('current_streak_days')
        )['max_streak'] or 0

        longest_streak = progress_records.aggregate(
            max_longest=models.Max('longest_streak_days')
        )['max_longest'] or 0

        # Roadmap stats
        roadmaps_in_progress = progress_records.filter(
            roadmap__status__in=['active', 'in_progress']
        ).count()

        roadmaps_completed = progress_records.filter(
            roadmap__status='completed'
        ).count()

        # Average daily hours (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_hours = TimeLog.objects.filter(
            user=user,
            started_at__gte=thirty_days_ago,
            is_deleted=False
        ).aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        average_daily_hours = Decimal(str(round((recent_hours / 60) / 30, 2)))

        # This week hours
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        week_hours = TimeLog.objects.filter(
            user=user,
            started_at__date__gte=week_start,
            is_deleted=False
        ).aggregate(
            total=Sum('duration_minutes')
        )['total'] or 0
        this_week_hours = Decimal(str(round(week_hours / 60, 2)))

        # Last activity
        last_activity = progress_records.aggregate(
            last=models.Max('last_activity_date')
        )['last']

        stats = {
            'total_learning_hours': total_hours,
            'total_courses_completed': total_courses,
            'total_milestones_achieved': total_milestones,
            'current_streak_days': current_streak,
            'longest_streak_days': longest_streak,
            'roadmaps_in_progress': roadmaps_in_progress,
            'roadmaps_completed': roadmaps_completed,
            'average_daily_hours': average_daily_hours,
            'this_week_hours': this_week_hours,
            'last_activity_date': last_activity,
        }

        serializer = ProgressStatsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
