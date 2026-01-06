"""
Progress Service Layer

Handles progress tracking, course completions, milestone achievements,
and time logging for user learning journeys.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import UserProgress, CourseCompletion, MilestoneAchievement, TimeLog
from apps.users.models import User
from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapCourse
from apps.courses.models import Course
from apps.notifications.signals import (
    milestone_achieved, course_completed, phase_completed,
    roadmap_completed, streak_updated
)


class ProgressService:
    """Service for user progress management"""

    @staticmethod
    def get_or_create_progress(user: User, roadmap: Roadmap) -> UserProgress:
        """Get or create progress record for user on roadmap"""
        progress, created = UserProgress.objects.get_or_create(
            user=user,
            roadmap=roadmap,
            defaults={
                'overall_completion_percentage': Decimal('0.00'),
                'phases_completed': 0,
                'milestones_completed': 0,
                'courses_completed': 0,
                'total_learning_hours': Decimal('0.00'),
                'current_streak_days': 0,
                'longest_streak_days': 0,
                'on_track': True
            }
        )
        return progress

    @staticmethod
    def update_progress_metrics(user: User, roadmap: Roadmap) -> UserProgress:
        """
        Recalculate and update all progress metrics for a roadmap.

        This should be called after completing courses, milestones, or phases.
        """
        progress = ProgressService.get_or_create_progress(user, roadmap)

        # Count completed items
        total_phases = roadmap.phases.count()
        completed_phases = roadmap.phases.filter(status='completed').count()

        total_milestones = RoadmapMilestone.objects.filter(
            phase__roadmap=roadmap
        ).count()
        completed_milestones = MilestoneAchievement.objects.filter(
            user=user,
            milestone__phase__roadmap=roadmap,
            is_deleted=False
        ).count()

        completed_courses = CourseCompletion.objects.filter(
            user=user,
            roadmap_course__milestone__phase__roadmap=roadmap,
            is_deleted=False
        ).count()

        # Calculate overall completion percentage
        if total_milestones > 0:
            completion = (completed_milestones / total_milestones) * 100
        else:
            completion = 0

        # Update progress
        progress.phases_completed = completed_phases
        progress.milestones_completed = completed_milestones
        progress.courses_completed = completed_courses
        progress.overall_completion_percentage = Decimal(str(round(completion, 2)))
        progress.save()

        # Check if roadmap is completed
        if completion >= 100:
            roadmap.status = 'completed'
            roadmap.completed_at = timezone.now()
            roadmap.save(update_fields=['status', 'completed_at', 'updated_at'])

            # Emit signal
            roadmap_completed.send(sender=Roadmap, instance=roadmap, user=user)

        return progress

    @staticmethod
    def update_streak(user: User, roadmap: Roadmap) -> UserProgress:
        """Update learning streak for user on roadmap"""
        progress = ProgressService.get_or_create_progress(user, roadmap)
        today = timezone.now().date()

        if progress.last_activity_date:
            days_diff = (today - progress.last_activity_date).days

            if days_diff == 1:
                # Consecutive day - increment streak
                progress.current_streak_days += 1
            elif days_diff == 0:
                # Same day - no change
                pass
            else:
                # Streak broken - reset
                progress.current_streak_days = 1
        else:
            # First activity
            progress.current_streak_days = 1

        # Update longest streak
        if progress.current_streak_days > progress.longest_streak_days:
            progress.longest_streak_days = progress.current_streak_days

        progress.last_activity_date = today
        progress.save()

        # Emit signal
        streak_updated.send(
            sender=UserProgress,
            instance=progress,
            current_streak=progress.current_streak_days
        )

        return progress

    @staticmethod
    def get_user_roadmap_progress(user: User, roadmap: Roadmap) -> Optional[UserProgress]:
        """Get progress for specific user and roadmap"""
        try:
            return UserProgress.objects.with_related().get(
                user=user,
                roadmap=roadmap,
                is_deleted=False
            )
        except UserProgress.DoesNotExist:
            return None

    @staticmethod
    def get_all_user_progress(user: User) -> List[UserProgress]:
        """Get all progress records for user"""
        return list(UserProgress.objects.for_user(user).with_related())


class CourseCompletionService:
    """Service for course completion tracking"""

    @staticmethod
    @transaction.atomic
    def mark_course_complete(
        user: User,
        course: Course,
        roadmap_course: Optional[RoadmapCourse] = None,
        time_spent_hours: Optional[Decimal] = None,
        user_rating: Optional[int] = None,
        user_review: str = "",
        would_recommend: Optional[bool] = None
    ) -> CourseCompletion:
        """
        Mark a course as completed by user.

        Args:
            user: User instance
            course: Course instance
            roadmap_course: Optional RoadmapCourse if part of roadmap
            time_spent_hours: Hours spent on course
            user_rating: Rating 1-5
            user_review: Written review
            would_recommend: Whether user would recommend

        Returns:
            CourseCompletion: Created completion record
        """
        # Check if already completed
        existing = CourseCompletion.objects.filter(
            user=user,
            course=course,
            is_deleted=False
        ).first()

        if existing:
            # Update existing
            if user_rating:
                existing.user_rating = user_rating
            if user_review:
                existing.user_review = user_review
            if would_recommend is not None:
                existing.would_recommend = would_recommend
            existing.save()
            return existing

        # Create new completion
        now = timezone.now()
        completion = CourseCompletion.objects.create(
            user=user,
            course=course,
            roadmap_course=roadmap_course,
            started_at=now - timedelta(hours=float(time_spent_hours or 0)),
            completed_at=now,
            time_spent_hours=time_spent_hours,
            completion_percentage=Decimal('100.00'),
            user_rating=user_rating,
            user_review=user_review,
            would_recommend=would_recommend,
            has_certificate=False
        )

        # Update roadmap progress if applicable
        if roadmap_course and roadmap_course.milestone:
            roadmap = roadmap_course.milestone.phase.roadmap
            ProgressService.update_progress_metrics(user, roadmap)
            ProgressService.update_streak(user, roadmap)

        # Emit signal
        course_completed.send(
            sender=CourseCompletion,
            instance=completion,
            user=user,
            course=course
        )

        return completion

    @staticmethod
    def get_user_completions(user: User) -> List[CourseCompletion]:
        """Get all course completions for user"""
        return list(CourseCompletion.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('course', 'roadmap_course'))

    @staticmethod
    def add_course_review(
        completion_id: str,
        rating: int,
        review: str,
        would_recommend: bool
    ) -> Optional[CourseCompletion]:
        """Add or update review for completed course"""
        try:
            completion = CourseCompletion.objects.get(id=completion_id)
            completion.user_rating = rating
            completion.user_review = review
            completion.would_recommend = would_recommend
            completion.save()
            return completion
        except CourseCompletion.DoesNotExist:
            return None


class MilestoneService:
    """Service for milestone achievement tracking"""

    @staticmethod
    @transaction.atomic
    def achieve_milestone(
        user: User,
        milestone: RoadmapMilestone,
        award_badge: bool = False,
        badge_type: str = ""
    ) -> MilestoneAchievement:
        """
        Mark a milestone as achieved by user.

        Args:
            user: User instance
            milestone: RoadmapMilestone instance
            award_badge: Whether to award a badge
            badge_type: Type of badge to award

        Returns:
            MilestoneAchievement: Created achievement record
        """
        # Check if already achieved
        existing = MilestoneAchievement.objects.filter(
            user=user,
            milestone=milestone,
            is_deleted=False
        ).first()

        if existing:
            return existing

        # Calculate time to complete (if milestone has start tracking)
        time_to_complete = None
        roadmap = milestone.phase.roadmap
        progress = ProgressService.get_or_create_progress(user, roadmap)

        if progress.last_activity_date:
            time_to_complete = (timezone.now().date() - progress.last_activity_date).days

        # Create achievement
        achievement = MilestoneAchievement.objects.create(
            user=user,
            milestone=milestone,
            time_to_complete_days=time_to_complete,
            badge_awarded=award_badge,
            badge_type=badge_type
        )

        # Update milestone status
        milestone.status = 'completed'
        milestone.completed_at = timezone.now()
        milestone.save(update_fields=['status', 'completed_at', 'updated_at'])

        # Update roadmap progress
        ProgressService.update_progress_metrics(user, roadmap)
        ProgressService.update_streak(user, roadmap)

        # Check if phase is completed
        phase = milestone.phase
        phase_milestones_count = phase.milestones.count()
        phase_completed_count = phase.milestones.filter(status='completed').count()

        if phase_milestones_count > 0 and phase_completed_count == phase_milestones_count:
            phase.status = 'completed'
            phase.completed_at = timezone.now()
            phase.save(update_fields=['status', 'completed_at', 'updated_at'])

            # Emit phase completed signal
            phase_completed.send(sender=type(phase), instance=phase, user=user)

        # Emit milestone achieved signal
        milestone_achieved.send(
            sender=MilestoneAchievement,
            instance=achievement,
            user=user,
            milestone=milestone
        )

        return achievement

    @staticmethod
    def get_user_achievements(user: User) -> List[MilestoneAchievement]:
        """Get all milestone achievements for user"""
        return list(MilestoneAchievement.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('milestone', 'milestone__phase', 'milestone__phase__roadmap'))


class TimeLogService:
    """Service for time tracking"""

    @staticmethod
    def log_learning_session(
        user: User,
        started_at: datetime,
        ended_at: datetime,
        activity_type: str,
        course: Optional[Course] = None,
        roadmap: Optional[Roadmap] = None
    ) -> TimeLog:
        """
        Log a learning session.

        Args:
            user: User instance
            started_at: Session start time
            ended_at: Session end time
            activity_type: Type of activity (course, practice, reading, project)
            course: Optional course
            roadmap: Optional roadmap

        Returns:
            TimeLog: Created time log
        """
        # Calculate duration in minutes
        duration = (ended_at - started_at).total_seconds() / 60
        duration_minutes = max(1, min(int(duration), 1440))  # 1-1440 minutes

        time_log = TimeLog.objects.create(
            user=user,
            course=course,
            roadmap=roadmap,
            started_at=started_at,
            ended_at=ended_at,
            duration_minutes=duration_minutes,
            activity_type=activity_type
        )

        # Update total learning hours if roadmap specified
        if roadmap:
            progress = ProgressService.get_or_create_progress(user, roadmap)
            progress.total_learning_hours += Decimal(str(time_log.duration_hours))

            # Calculate average hours per week
            if progress.last_activity_date and progress.created_at:
                weeks = max(1, (timezone.now().date() - progress.created_at.date()).days / 7)
                progress.average_hours_per_week = progress.total_learning_hours / Decimal(str(weeks))

            progress.save()

        return time_log

    @staticmethod
    def get_user_time_logs(
        user: User,
        roadmap: Optional[Roadmap] = None,
        days: int = 30
    ) -> List[TimeLog]:
        """Get time logs for user, optionally filtered by roadmap"""
        cutoff = timezone.now() - timedelta(days=days)

        queryset = TimeLog.objects.filter(
            user=user,
            started_at__gte=cutoff,
            is_deleted=False
        )

        if roadmap:
            queryset = queryset.filter(roadmap=roadmap)

        return list(queryset.order_by('-started_at'))

    @staticmethod
    def get_weekly_learning_stats(user: User, roadmap: Optional[Roadmap] = None) -> Dict[str, Any]:
        """Get weekly learning statistics"""
        week_ago = timezone.now() - timedelta(days=7)

        queryset = TimeLog.objects.filter(
            user=user,
            started_at__gte=week_ago,
            is_deleted=False
        )

        if roadmap:
            queryset = queryset.filter(roadmap=roadmap)

        total_minutes = sum(log.duration_minutes for log in queryset)
        total_hours = total_minutes / 60

        # Group by activity type
        by_type = {}
        for log in queryset:
            activity = log.get_activity_type_display()
            by_type[activity] = by_type.get(activity, 0) + log.duration_minutes

        return {
            'total_hours': round(total_hours, 2),
            'total_sessions': queryset.count(),
            'by_activity_type': {k: round(v / 60, 2) for k, v in by_type.items()}
        }
