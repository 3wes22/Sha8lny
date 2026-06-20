"""
Seed evaluator-ready demo users for the graduation flow.

Usage:
    python3 manage.py seed_graduation_demo
    python3 manage.py seed_graduation_demo --reset
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.assessments.models import Assessment, AssessmentResult
from apps.courses.models import Course, CoursePlatform
from apps.progress.models import TimeLog, UserProgress
from apps.progress.services import CourseCompletionService, MilestoneService, ProgressService, TimeLogService
from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
from apps.roadmaps.services import RoadmapService
from apps.users.models import User


DEMO_PASSWORD = "DemoPass123!"
NEW_USER_EMAIL = "demo.new@sha8alny.local"
RETURNING_USER_EMAIL = "demo.progress@sha8alny.local"


class Command(BaseCommand):
    help = "Seed two evaluator-ready demo users for the assessment -> roadmap -> progress -> advisory flow"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Hard-delete existing demo accounts before recreating them.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Ensuring demo prerequisites are available...")
        call_command("create_sample_skills")
        call_command("seed_roadmap_templates")

        if options["reset"]:
            removed = self._hard_delete_demo_users()
            self.stdout.write(self.style.WARNING(f"Removed {removed} existing demo account(s)."))

        new_user = self._upsert_demo_user(
            email=NEW_USER_EMAIL,
            username="demo_new_user",
            full_name="Nour Newcomer",
            auth0_id="local|demo_new_user",
            onboarding_completed=False,
            onboarding_step=0,
        )
        self._clear_demo_journey(new_user)

        returning_user = self._upsert_demo_user(
            email=RETURNING_USER_EMAIL,
            username="demo_progress_user",
            full_name="Salma Progress",
            auth0_id="local|demo_progress_user",
            onboarding_completed=True,
            onboarding_step=3,
        )
        self._clear_demo_journey(returning_user)
        assessment_result = self._seed_assessment_result(returning_user)
        roadmap, progress = self._seed_returning_user_journey(returning_user, assessment_result)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Graduation demo users are ready."))
        self.stdout.write(f"- New user: {NEW_USER_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"- Returning user: {RETURNING_USER_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(
            f"- Returning user roadmap: {roadmap.title} ({progress.milestones_completed} milestones, "
            f"{progress.courses_completed} completed courses, {progress.current_streak_days}-day streak)"
        )

    def _demo_user_emails(self) -> list[str]:
        return [NEW_USER_EMAIL, RETURNING_USER_EMAIL]

    def _hard_delete_demo_users(self) -> int:
        queryset = User.all_objects.filter(email__in=self._demo_user_emails())
        deleted_count = queryset.count()
        queryset.delete()
        return deleted_count

    def _upsert_demo_user(
        self,
        *,
        email: str,
        username: str,
        full_name: str,
        auth0_id: str,
        onboarding_completed: bool,
        onboarding_step: int,
    ) -> User:
        user = User.all_objects.filter(email=email).first()

        if user is None:
            return User.objects.create_user(
                email=email,
                password=DEMO_PASSWORD,
                auth0_id=auth0_id,
                username=username,
                full_name=full_name,
                date_of_birth="1999-01-01",
                email_verified=True,
                onboarding_completed=onboarding_completed,
                onboarding_step=onboarding_step,
                preferred_language="en",
                timezone="Africa/Cairo",
            )

        user.auth0_id = auth0_id
        user.username = username
        user.full_name = full_name
        user.email_verified = True
        user.onboarding_completed = onboarding_completed
        user.onboarding_step = onboarding_step
        user.preferred_language = "en"
        user.timezone = "Africa/Cairo"
        user.account_status = "active"
        user.is_active = True
        user.is_deleted = False
        user.deleted_at = None
        user.set_password(DEMO_PASSWORD)
        user.save(
            update_fields=[
                "auth0_id",
                "username",
                "full_name",
                "email_verified",
                "onboarding_completed",
                "onboarding_step",
                "preferred_language",
                "timezone",
                "account_status",
                "is_active",
                "is_deleted",
                "deleted_at",
                "password",
                "updated_at",
            ]
        )
        return user

    def _clear_demo_journey(self, user: User) -> None:
        user.conversations.all().delete()
        user.time_logs.all().delete()
        user.course_completions.all().delete()
        user.milestone_achievements.all().delete()
        user.progress_records.all().delete()
        user.roadmaps.all().delete()
        user.assessments.all().delete()

    def _seed_assessment_result(self, user: User) -> AssessmentResult:
        now = timezone.now()
        assessment = Assessment.objects.create(
            user=user,
            assessment_type="skills",
            target_career="Backend Developer",
            stage="completed",
            questions=[
                {"id": "s1-q1", "prompt": "Which backend tasks feel most natural?"},
                {"id": "s2-q1", "prompt": "How would you strengthen production readiness?"},
            ],
            responses=[
                {"question_id": "s1-q1", "answer": ["APIs", "databases"]},
                {"question_id": "s2-q1", "answer": "More testing and deployment practice."},
            ],
            stage_one_questions=[
                {"id": "stage-1-1", "prompt": "Pick the backend topics you enjoy most."},
            ],
            stage_one_responses=[
                {"question_id": "stage-1-1", "answer": ["Python", "REST APIs", "SQL"]},
            ],
            stage_two_questions=[
                {"id": "stage-2-1", "prompt": "What would make you more job-ready this month?"},
            ],
            stage_two_responses=[
                {"question_id": "stage-2-1", "answer": "Ship one stronger API project and improve testing."},
            ],
            gap_profile={
                "strengths": ["Python fundamentals", "problem solving"],
                "gaps": ["system design", "testing discipline", "deployment confidence"],
            },
            roadmap_signal={
                "target_career": "Backend Developer",
                "focus_skills": ["Django", "PostgreSQL", "Testing"],
                "weekly_hours": 8,
            },
            generation_metadata={
                "source": "graduation-demo-seed",
                "fallback_used": False,
                "trace_id": "demo-assessment-trace",
            },
            ai_processing_status="completed",
            ai_processed_at=now - timedelta(days=18),
            status="completed",
            started_at=now - timedelta(days=20),
            completed_at=now - timedelta(days=18),
            total_questions=6,
            answered_questions=6,
            time_spent_seconds=18 * 60,
        )

        return AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=Decimal("82.00"),
            skill_scores={
                "technical": {"Python": 86, "Django": 78, "SQL": 74},
                "soft": {"Problem Solving": 88, "Communication": 72},
            },
            strengths=["Strong Python fundamentals", "Consistent project follow-through"],
            areas_for_improvement=["Deployment confidence", "Automated testing depth"],
            recommended_careers=[
                {
                    "title": "Backend Developer",
                    "match_score": 91,
                    "reasoning": "The user already has the right language and API baseline for a backend path.",
                }
            ],
            recommended_learning_paths=[
                {
                    "skill": "Django APIs",
                    "priority": "high",
                    "resources": ["Build one production-style CRUD API"],
                },
                {
                    "skill": "Testing with Pytest",
                    "priority": "medium",
                    "resources": ["Add API and service-layer coverage to existing projects"],
                },
            ],
            roadmap_signal={
                "target_career": "Backend Developer",
                "focus_skills": ["Django", "PostgreSQL", "Testing"],
                "weekly_hours": 8,
            },
            ai_insights=(
                "You have a strong backend base already. The next gains come from finishing one "
                "portfolio-grade API, tightening tests, and building deployment confidence."
            ),
            ai_confidence_score=Decimal("84.00"),
            llm_model_used="graduation-demo-assessment-v1",
            llm_prompt_tokens=1180,
            llm_completion_tokens=620,
            processing_time_seconds=Decimal("3.20"),
        )

    def _seed_returning_user_journey(
        self,
        user: User,
        assessment_result: AssessmentResult,
    ) -> tuple[Roadmap, UserProgress]:
        # Generate the roadmap through the real assessment -> AI ladder pipeline
        # (create_ai_roadmap_shell + populate_ai_roadmap) so the demo account
        # showcases assessment-derived "already mastered" greying: bands below the
        # learner's assessed level are pre-completed from the assessment, the rest
        # is the live plan. Gemini personalizes the copy when reachable and falls
        # back to the deterministic ladder offline.
        current_level = RoadmapService.derive_current_level_from_assessment(assessment_result)
        target_career = (
            RoadmapService.derive_target_career_from_assessment(assessment_result)
            or "Backend Developer"
        )

        roadmap = RoadmapService.create_ai_roadmap_shell(
            user=user,
            assessment=assessment_result,
            target_career=target_career,
            current_level=current_level,
            target_level="job-ready",
            weekly_hours=8,
        )
        RoadmapService.populate_ai_roadmap(roadmap)
        roadmap.refresh_from_db()

        now = timezone.now()
        metadata = roadmap.metadata if isinstance(roadmap.metadata, dict) else {}
        metadata["demo_seed"] = {
            "profile": "returning_user",
            "seeded_at": now.isoformat(),
        }
        roadmap.metadata = metadata
        roadmap.description = (
            "A focused roadmap generated from the latest assessment. Earlier bands "
            "are already marked complete from the assessment, with real progress "
            "continuing in the current phase."
        )
        existing_insights = roadmap.ai_insights if isinstance(roadmap.ai_insights, dict) else {}
        roadmap.ai_insights = {
            **existing_insights,
            "coach_note": "Foundations are behind you - keep momentum on the current phase.",
        }
        roadmap.started_at = now - timedelta(days=21)
        roadmap.ai_processed_at = now - timedelta(days=17)
        roadmap.save(
            update_fields=[
                "metadata",
                "description",
                "ai_insights",
                "started_at",
                "ai_processed_at",
                "updated_at",
            ]
        )

        # Layer real (non-assessment) progress on top of the greyed baseline by
        # working the current active band: complete its first course-milestone and
        # the real Coursera course that the matcher attached to it during
        # generation, then start the next one — so the account shows real courses,
        # a completion, and a streak alongside the assessment-derived greying.
        phases = list(
            roadmap.phases.order_by("order").prefetch_related("milestones__courses__course")
        )
        current_phase = next(
            (phase for phase in phases if phase.status != RoadmapPhase.COMPLETED),
            phases[-1],
        )
        active_course_milestones = [
            milestone
            for milestone in current_phase.milestones.order_by("order")
            if milestone.status != RoadmapMilestone.COMPLETED
            and milestone.milestone_type == RoadmapMilestone.COURSE
        ]

        completed_one = False
        for milestone in active_course_milestones:
            roadmap_course = milestone.courses.order_by("-is_primary", "order").first()
            if not completed_one:
                # First active milestone: complete it and its attached real course
                # (if matching found one) -> real, in-plan progress.
                if roadmap_course is not None:
                    CourseCompletionService.mark_course_complete(
                        user=user,
                        course=roadmap_course.course,
                        roadmap_course=roadmap_course,
                        time_spent_hours=Decimal("12.00"),
                        user_rating=5,
                        user_review="Exactly the push needed to clear this milestone.",
                        would_recommend=True,
                    )
                    roadmap_course.is_enrolled = True
                    roadmap_course.is_completed = True
                    roadmap_course.enrolled_at = now - timedelta(days=6)
                    roadmap_course.completed_at = now - timedelta(days=2)
                    roadmap_course.save(
                        update_fields=[
                            "is_enrolled", "is_completed", "enrolled_at", "completed_at", "updated_at",
                        ]
                    )
                # Real, in-plan completion (completed_from_assessment stays False).
                MilestoneService.achieve_milestone(user, milestone)
                completed_one = True
            elif roadmap_course is not None:
                # Next milestone: enrolled / in progress.
                roadmap_course.is_enrolled = True
                roadmap_course.enrolled_at = now - timedelta(days=1)
                roadmap_course.save(update_fields=["is_enrolled", "enrolled_at", "updated_at"])
                milestone.status = RoadmapMilestone.IN_PROGRESS
                milestone.save(update_fields=["status", "updated_at"])
                break

        progress = ProgressService.update_progress_metrics(user, roadmap)

        seed_created_at = now - timedelta(days=21)
        UserProgress.all_objects.filter(id=progress.id).update(created_at=seed_created_at)
        progress.refresh_from_db()

        historical_logs = [
            (
                now - timedelta(days=3, hours=2),
                now - timedelta(days=3, minutes=30),
                90,
                "course",
            ),
            (
                now - timedelta(days=2, hours=3),
                now - timedelta(days=2, hours=1),
                120,
                "practice",
            ),
            (
                now - timedelta(days=1, hours=4),
                now - timedelta(days=1, hours=2),
                120,
                "reading",
            ),
        ]
        for started_at, ended_at, duration_minutes, activity_type in historical_logs:
            TimeLog.objects.create(
                user=user,
                roadmap=roadmap,
                started_at=started_at,
                ended_at=ended_at,
                duration_minutes=duration_minutes,
                activity_type=activity_type,
            )

        TimeLogService.log_learning_session(
            user=user,
            roadmap=roadmap,
            started_at=now - timedelta(hours=2),
            ended_at=now,
            activity_type="project",
        )

        progress.refresh_from_db()
        progress.total_learning_hours = Decimal("7.50")
        progress.average_hours_per_week = Decimal("2.50")
        progress.current_streak_days = 4
        progress.longest_streak_days = 4
        progress.last_activity_date = timezone.now().date()
        progress.save(
            update_fields=[
                "total_learning_hours",
                "average_hours_per_week",
                "current_streak_days",
                "longest_streak_days",
                "last_activity_date",
                "updated_at",
            ]
        )

        RoadmapService.update_roadmap_status(roadmap, Roadmap.ACTIVE)
        progress = ProgressService.update_progress_metrics(user, roadmap)

        return roadmap, progress

    def _ensure_demo_course_platform(self) -> CoursePlatform:
        platform = CoursePlatform.all_objects.filter(slug="sha8alny-demo-library").first()

        if platform is None:
            return CoursePlatform.objects.create(
                name="Sha8alny Demo Library",
                slug="sha8alny-demo-library",
                website_url="https://demo.sha8alny.local/library",
                description="Manual demo platform for evaluator-ready roadmap recommendations.",
                integration_type=CoursePlatform.MANUAL,
                is_active=True,
                total_courses=0,
            )

        platform.name = "Sha8alny Demo Library"
        platform.website_url = "https://demo.sha8alny.local/library"
        platform.description = "Manual demo platform for evaluator-ready roadmap recommendations."
        platform.integration_type = CoursePlatform.MANUAL
        platform.is_active = True
        platform.is_deleted = False
        platform.deleted_at = None
        platform.save(
            update_fields=[
                "name",
                "website_url",
                "description",
                "integration_type",
                "is_active",
                "is_deleted",
                "deleted_at",
                "updated_at",
            ]
        )
        return platform

    def _upsert_demo_course(
        self,
        *,
        platform: CoursePlatform,
        external_id: str,
        title: str,
        short_description: str,
        url: str,
        duration_hours: Decimal,
        level: str,
    ) -> Course:
        course = Course.all_objects.filter(platform=platform, external_id=external_id).first()
        course_defaults = {
            "title": title,
            "slug": external_id,
            "description": short_description,
            "short_description": short_description,
            "url": url,
            "level": level,
            "course_type": Course.VIDEO,
            "language": "English",
            "is_free": True,
            "duration_hours": duration_hours,
            "rating": Decimal("4.70"),
            "total_reviews": 120,
            "total_enrollments": 2400,
            "has_certificate": False,
            "is_published": True,
            "learning_outcomes": [
                "Turn roadmap milestones into concrete practice",
                "Build portfolio-ready evidence for backend roles",
            ],
            "metadata": {"source": "graduation-demo-seed"},
        }

        if course is None:
            return Course.objects.create(
                platform=platform,
                external_id=external_id,
                **course_defaults,
            )

        for field, value in course_defaults.items():
            setattr(course, field, value)
        course.is_deleted = False
        course.deleted_at = None
        course.save(update_fields=[*course_defaults.keys(), "is_deleted", "deleted_at", "updated_at"])
        return course
