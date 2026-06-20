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
from apps.roadmaps.models import Roadmap, RoadmapPhase, RoadmapMilestone, RoadmapCourse
from apps.courses.models import Course
from apps.notifications.signals import (
    milestone_achieved, course_completed, phase_completed,
    roadmap_completed, streak_updated
)


class ProgressService:
    """Service for user progress management"""

    @staticmethod
    def _resolve_current_focus_from_phases(
        phases: list[RoadmapPhase],
    ) -> tuple[Optional[RoadmapMilestone], Optional[RoadmapPhase]]:
        current_phase = next(
            (phase for phase in phases if phase.status == RoadmapPhase.IN_PROGRESS),
            None,
        )
        if current_phase is None:
            current_phase = next(
                (phase for phase in phases if phase.status == RoadmapPhase.NOT_STARTED),
                None,
            )
        if current_phase is None and phases:
            current_phase = phases[-1]

        if current_phase is None:
            return None, None

        milestones = list(current_phase.milestones.all().order_by("order"))
        current_milestone = next(
            (
                milestone
                for milestone in milestones
                if milestone.status in {RoadmapMilestone.IN_PROGRESS, RoadmapMilestone.NOT_STARTED}
            ),
            None,
        )

        return current_milestone, current_phase

    @staticmethod
    def _resolve_current_focus(roadmap: Roadmap) -> tuple[Optional[RoadmapMilestone], Optional[RoadmapPhase]]:
        phases = list(roadmap.phases.all().order_by("order"))
        return ProgressService._resolve_current_focus_from_phases(phases)

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
    def _calculate_progress_state(
        user: User,
        roadmap: Roadmap,
        progress: Optional[UserProgress] = None,
    ) -> Dict[str, Any]:
        """Calculate roadmap progress without writing to the database."""
        now = timezone.now()
        phases = list(roadmap.phases.all().order_by("order").prefetch_related("milestones"))
        total_phases = len(phases)
        total_milestones = 0
        completed_milestones = 0
        phase_states = []

        for phase in phases:
            milestones = list(phase.milestones.all().order_by("order"))
            total = len(milestones)
            total_milestones += total
            completed = sum(1 for milestone in milestones if milestone.status == RoadmapMilestone.COMPLETED)
            completed_milestones += completed
            has_active_work = phase.status == RoadmapPhase.IN_PROGRESS or any(
                milestone.status in {RoadmapMilestone.IN_PROGRESS, RoadmapMilestone.COMPLETED}
                for milestone in milestones
            )
            phase_completion = round((completed / total) * 100, 2) if total > 0 else 0

            desired_status = RoadmapPhase.NOT_STARTED
            desired_started_at = phase.started_at
            desired_completed_at = None

            if total > 0 and completed == total:
                desired_status = RoadmapPhase.COMPLETED
                desired_started_at = phase.started_at or now
                desired_completed_at = phase.completed_at or now
            elif has_active_work:
                desired_status = RoadmapPhase.IN_PROGRESS
                desired_started_at = phase.started_at or now

            phase.completion_percentage = Decimal(str(phase_completion))
            phase.status = desired_status
            phase.started_at = desired_started_at
            phase.completed_at = desired_completed_at
            phase_states.append(
                {
                    "phase": phase,
                    "completion_percentage": Decimal(str(phase_completion)),
                    "status": desired_status,
                    "started_at": desired_started_at,
                    "completed_at": desired_completed_at,
                }
            )

        completed_phases = sum(1 for phase in phases if phase.status == RoadmapPhase.COMPLETED)

        completed_courses = CourseCompletion.objects.filter(
            user=user,
            roadmap_course__milestone__phase__roadmap=roadmap,
            is_deleted=False
        ).count()

        completion = round((completed_milestones / total_milestones) * 100, 2) if total_milestones > 0 else 0
        current_milestone, current_phase = ProgressService._resolve_current_focus_from_phases(phases)

        total_learning_hours = (
            Decimal(str(progress.total_learning_hours or 0))
            if progress
            else Decimal("0.00")
        )
        average_hours_per_week = None
        progress_created_at = progress.created_at if progress and progress.created_at else roadmap.created_at
        if progress_created_at:
            weeks = max(1, (now.date() - progress_created_at.date()).days / 7)
            average_hours_per_week = total_learning_hours / Decimal(str(weeks))

        if roadmap.started_at and roadmap.estimated_duration_weeks:
            elapsed_weeks = max(1, (now.date() - roadmap.started_at.date()).days / 7)
            expected_completion = min(100, (elapsed_weeks / roadmap.estimated_duration_weeks) * 100)
            on_track = completion + 5 >= expected_completion
        else:
            on_track = True

        roadmap_status = roadmap.status
        roadmap_started_at = roadmap.started_at
        roadmap_completed_at = roadmap.completed_at
        if completion >= 100:
            roadmap_status = Roadmap.COMPLETED
            roadmap_completed_at = roadmap.completed_at or now
        elif completion > 0:
            if roadmap.status == Roadmap.DRAFT:
                roadmap_status = Roadmap.IN_PROGRESS
            roadmap_started_at = roadmap.started_at or now
            roadmap_completed_at = None
        elif roadmap.status == Roadmap.COMPLETED:
            roadmap_status = Roadmap.IN_PROGRESS
            roadmap_completed_at = None

        return {
            "phase_states": phase_states,
            "total_phases": total_phases,
            "phases_completed": completed_phases,
            "total_milestones": total_milestones,
            "milestones_completed": completed_milestones,
            "courses_completed": completed_courses,
            "current_phase": current_phase,
            "current_milestone": current_milestone,
            "overall_completion_percentage": Decimal(str(completion)),
            "average_hours_per_week": average_hours_per_week,
            "on_track": on_track,
            "roadmap_status": roadmap_status,
            "roadmap_started_at": roadmap_started_at,
            "roadmap_completed_at": roadmap_completed_at,
        }

    @staticmethod
    def get_progress_snapshot(user: User, roadmap: Roadmap) -> UserProgress:
        """Return calculated progress for read paths without persisting side effects."""
        progress = ProgressService.get_user_roadmap_progress(user, roadmap)
        if progress is None:
            progress = UserProgress(user=user, roadmap=roadmap)
            progress.created_at = roadmap.created_at
            progress.updated_at = timezone.now()

        state = ProgressService._calculate_progress_state(user, roadmap, progress)
        progress.phases_completed = state["phases_completed"]
        progress.milestones_completed = state["milestones_completed"]
        progress.courses_completed = state["courses_completed"]
        progress.current_phase = state["current_phase"]
        progress.current_milestone = state["current_milestone"]
        progress.overall_completion_percentage = state["overall_completion_percentage"]
        progress.average_hours_per_week = state["average_hours_per_week"]
        progress.on_track = state["on_track"]
        return progress

    @staticmethod
    def get_derived_roadmap_status(user: User, roadmap: Roadmap) -> str:
        """Return the calculated roadmap status without writing it."""
        progress = ProgressService.get_user_roadmap_progress(user, roadmap)
        return ProgressService._calculate_progress_state(user, roadmap, progress)["roadmap_status"]

    @staticmethod
    def update_progress_metrics(user: User, roadmap: Roadmap) -> UserProgress:
        """
        Recalculate and persist all progress metrics for a roadmap.

        This should be called after completing courses, milestones, or phases.
        """
        progress = ProgressService.get_or_create_progress(user, roadmap)
        state = ProgressService._calculate_progress_state(user, roadmap, progress)

        for phase_state in state["phase_states"]:
            phase = phase_state["phase"]
            for field in ("completion_percentage", "status", "started_at", "completed_at"):
                setattr(phase, field, phase_state[field])
            phase.save(update_fields=["completion_percentage", "status", "started_at", "completed_at", "updated_at"])

        progress.phases_completed = state["phases_completed"]
        progress.milestones_completed = state["milestones_completed"]
        progress.courses_completed = state["courses_completed"]
        progress.current_phase = state["current_phase"]
        progress.current_milestone = state["current_milestone"]
        progress.overall_completion_percentage = state["overall_completion_percentage"]
        progress.average_hours_per_week = state["average_hours_per_week"]
        progress.on_track = state["on_track"]
        progress.save()

        roadmap_update_fields = []
        completion_decimal = state["overall_completion_percentage"]
        if completion_decimal != roadmap.completion_percentage:
            roadmap.completion_percentage = completion_decimal
            roadmap_update_fields.append("completion_percentage")

        previous_roadmap_status = roadmap.status
        for field, state_key in (
            ("status", "roadmap_status"),
            ("started_at", "roadmap_started_at"),
            ("completed_at", "roadmap_completed_at"),
        ):
            if getattr(roadmap, field) != state[state_key]:
                setattr(roadmap, field, state[state_key])
                roadmap_update_fields.append(field)

        if roadmap_update_fields:
            roadmap.save(update_fields=[*roadmap_update_fields, "updated_at"])

        if previous_roadmap_status != Roadmap.COMPLETED and roadmap.status == Roadmap.COMPLETED:
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
    @transaction.atomic
    def record_completion(
        user: User,
        course: Course,
        started_at: datetime,
        completed_at: datetime,
        roadmap_course: Optional[RoadmapCourse] = None,
        time_spent_hours: Optional[Decimal] = None,
        user_rating: Optional[int] = None,
        user_review: str = "",
        would_recommend: Optional[bool] = None,
        certificate_url: str = "",
    ) -> CourseCompletion:
        """Record a course completion with explicit start/end timestamps."""
        existing = CourseCompletion.objects.filter(
            user=user,
            course=course,
            is_deleted=False,
        ).first()

        if existing:
            if user_rating is not None:
                existing.user_rating = user_rating
            if user_review:
                existing.user_review = user_review
            if would_recommend is not None:
                existing.would_recommend = would_recommend
            if certificate_url:
                existing.certificate_url = certificate_url
                existing.has_certificate = True
            existing.save()
            return existing

        completion = CourseCompletion.objects.create(
            user=user,
            course=course,
            roadmap_course=roadmap_course,
            started_at=started_at,
            completed_at=completed_at,
            time_spent_hours=time_spent_hours,
            completion_percentage=Decimal("100.00"),
            user_rating=user_rating,
            user_review=user_review,
            would_recommend=would_recommend,
            has_certificate=bool(certificate_url),
            certificate_url=certificate_url,
        )

        if roadmap_course and roadmap_course.milestone:
            roadmap = roadmap_course.milestone.phase.roadmap
            ProgressService.update_progress_metrics(user, roadmap)
            ProgressService.update_streak(user, roadmap)

        course_completed.send(
            sender=CourseCompletion,
            instance=completion,
            user=user,
            course=course,
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
            if milestone.status != RoadmapMilestone.COMPLETED or milestone.completed_at is None:
                milestone.status = RoadmapMilestone.COMPLETED
                milestone.completed_at = timezone.now()
                milestone.save(update_fields=["status", "completed_at", "updated_at"])
                ProgressService.update_progress_metrics(user, milestone.phase.roadmap)
                ProgressService.update_streak(user, milestone.phase.roadmap)
            from apps.users.milestone_skills import MilestoneSkillService

            MilestoneSkillService.grant_milestone_skills(user, milestone)
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

        from apps.users.milestone_skills import MilestoneSkillService

        MilestoneSkillService.grant_milestone_skills(user, milestone)

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
    @transaction.atomic
    def update_milestone_status(
        user: User,
        milestone: RoadmapMilestone,
        status: str,
    ) -> RoadmapMilestone:
        """Update milestone status and keep achievement rows consistent."""
        if status == RoadmapMilestone.COMPLETED:
            MilestoneService.achieve_milestone(user, milestone)
            milestone.refresh_from_db()
            return milestone

        milestone.status = status
        if status == RoadmapMilestone.NOT_STARTED:
            milestone.completed_at = None
        # Leaving "completed" means the learner is redoing it: drop the
        # assessment-baseline marker so it reads as real in-plan work.
        milestone.completed_from_assessment = False
        milestone.save(update_fields=[
            "status", "completed_at", "completed_from_assessment", "updated_at",
        ])

        MilestoneAchievement.objects.filter(
            user=user,
            milestone=milestone,
            is_deleted=False,
        ).update(
            is_deleted=True,
            deleted_at=timezone.now(),
        )

        roadmap = milestone.phase.roadmap
        if status == RoadmapMilestone.IN_PROGRESS:
            ProgressService.update_streak(user, roadmap)
        ProgressService.update_progress_metrics(user, roadmap)
        return milestone

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
    def log_time(
        user: User,
        started_at: datetime,
        ended_at: datetime,
        activity_type: str,
        course: Optional[Course] = None,
        roadmap: Optional[Roadmap] = None,
        duration_minutes: Optional[int] = None,
    ) -> TimeLog:
        """Create a time log entry from API payload."""
        if duration_minutes is not None:
            time_log = TimeLog.objects.create(
                user=user,
                course=course,
                roadmap=roadmap,
                started_at=started_at,
                ended_at=ended_at,
                duration_minutes=duration_minutes,
                activity_type=activity_type,
            )
            if roadmap:
                progress = ProgressService.update_streak(user, roadmap)
                progress.total_learning_hours += Decimal(str(time_log.duration_hours))
                if progress.last_activity_date and progress.created_at:
                    weeks = max(
                        1,
                        (timezone.now().date() - progress.created_at.date()).days / 7,
                    )
                    progress.average_hours_per_week = (
                        progress.total_learning_hours / Decimal(str(weeks))
                    )
                progress.save()
            return time_log

        return TimeLogService.log_learning_session(
            user=user,
            started_at=started_at,
            ended_at=ended_at,
            activity_type=activity_type,
            course=course,
            roadmap=roadmap,
        )

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
            progress = ProgressService.update_streak(user, roadmap)
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
