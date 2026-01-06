"""
Roadmaps Service Layer

Handles roadmap generation, template management, and roadmap operations.
This is where AI-powered roadmap generation will be integrated.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    RoadmapTemplate, Roadmap, RoadmapPhase,
    RoadmapMilestone, RoadmapCourse
)
from apps.users.models import User
from apps.assessments.models import AssessmentResult
from apps.courses.models import Course
from apps.notifications.signals import roadmap_generated, roadmap_updated


class RoadmapTemplateService:
    """Service for roadmap template management"""

    @staticmethod
    def get_published_templates() -> List[RoadmapTemplate]:
        """Get all published roadmap templates"""
        return list(RoadmapTemplate.objects.filter(
            is_published=True,
            is_deleted=False
        ).order_by('-usage_count'))

    @staticmethod
    def get_template_by_career(career: str) -> List[RoadmapTemplate]:
        """Get templates for a specific career path"""
        return list(RoadmapTemplate.objects.filter(
            target_career__icontains=career,
            is_published=True,
            is_deleted=False
        ))

    @staticmethod
    def get_template_by_id(template_id: str) -> Optional[RoadmapTemplate]:
        """Get template by ID"""
        try:
            return RoadmapTemplate.objects.get(id=template_id, is_deleted=False)
        except RoadmapTemplate.DoesNotExist:
            return None

    @staticmethod
    def increment_template_usage(template: RoadmapTemplate) -> None:
        """Increment usage count for template"""
        template.usage_count += 1
        template.save(update_fields=['usage_count', 'updated_at'])


class RoadmapService:
    """Service for roadmap management and AI generation"""

    @staticmethod
    @transaction.atomic
    def create_roadmap_from_template(
        user: User,
        template: RoadmapTemplate,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Roadmap:
        """
        Create a personalized roadmap from a template.

        Args:
            user: User instance
            template: RoadmapTemplate instance
            customizations: Optional customizations (weekly_hours, etc.)

        Returns:
            Roadmap: Created roadmap instance
        """
        customizations = customizations or {}

        roadmap = Roadmap.objects.create(
            user=user,
            template=template,
            title=f"{template.title} - {user.first_name or user.email}",
            description=template.description,
            target_career=template.target_career,
            current_level='beginner',
            target_level=template.get_career_level_display(),
            estimated_duration_weeks=template.estimated_duration_weeks,
            weekly_hours_commitment=customizations.get('weekly_hours', 10),
            status='draft',
            ai_processing_status='completed'
        )

        # Increment template usage
        RoadmapTemplateService.increment_template_usage(template)

        return roadmap

    @staticmethod
    @transaction.atomic
    def generate_ai_roadmap(
        user: User,
        assessment: Optional[AssessmentResult],
        target_career: str,
        current_level: str,
        target_level: str,
        weekly_hours: int = 10
    ) -> Roadmap:
        """
        Generate AI-powered personalized roadmap.

        This method will be integrated with OpenAI/Claude API for roadmap generation.
        For now, it creates a skeleton roadmap that can be populated.

        Args:
            user: User instance
            assessment: Optional assessment result
            target_career: Target career goal
            current_level: Current skill level
            target_level: Target skill level
            weekly_hours: Weekly time commitment

        Returns:
            Roadmap: Created roadmap with AI processing status
        """
        roadmap = Roadmap.objects.create(
            user=user,
            assessment=assessment,
            title=f"Personalized {target_career} Roadmap",
            description=f"AI-generated learning path to become a {target_career}",
            target_career=target_career,
            current_level=current_level,
            target_level=target_level,
            weekly_hours_commitment=weekly_hours,
            estimated_duration_weeks=24,  # Default, will be calculated by AI
            status='draft',
            ai_processing_status='pending'  # Will be updated by async task
        )

        # TODO: Trigger async Celery task for AI generation
        # For now, we mark it as pending
        # tasks.generate_roadmap_with_ai.delay(roadmap.id)

        # Emit signal
        roadmap_generated.send(
            sender=Roadmap,
            instance=roadmap,
            user=user
        )

        return roadmap

    @staticmethod
    def get_user_roadmaps(user: User, status: Optional[str] = None) -> List[Roadmap]:
        """
        Get roadmaps for user, optionally filtered by status.

        Args:
            user: User instance
            status: Optional status filter

        Returns:
            List[Roadmap]: List of roadmaps
        """
        queryset = Roadmap.objects.for_user(user).with_hierarchy()

        if status:
            if status == 'active':
                queryset = queryset.active()
            elif status == 'completed':
                queryset = queryset.completed()
            else:
                queryset = queryset.filter(status=status)

        return list(queryset)

    @staticmethod
    def get_roadmap_by_id(roadmap_id: str) -> Optional[Roadmap]:
        """Get roadmap by ID with hierarchy prefetched"""
        try:
            return Roadmap.objects.with_hierarchy().get(
                id=roadmap_id,
                is_deleted=False
            )
        except Roadmap.DoesNotExist:
            return None

    @staticmethod
    def update_roadmap_status(roadmap: Roadmap, status: str) -> Roadmap:
        """Update roadmap status"""
        valid_statuses = ['draft', 'active', 'in_progress', 'completed', 'paused', 'archived']

        if status not in valid_statuses:
            raise ValidationError(f"Invalid status: {status}")

        roadmap.status = status

        if status == 'active' and not roadmap.started_at:
            roadmap.started_at = timezone.now()
        elif status == 'completed' and not roadmap.completed_at:
            roadmap.completed_at = timezone.now()
            roadmap.completion_percentage = Decimal('100.00')

        roadmap.save()

        # Emit signal
        roadmap_updated.send(sender=Roadmap, instance=roadmap)

        return roadmap

    @staticmethod
    @transaction.atomic
    def add_phase_to_roadmap(
        roadmap: Roadmap,
        title: str,
        description: str,
        order: int,
        estimated_duration_weeks: int,
        objectives: Optional[List[str]] = None
    ) -> RoadmapPhase:
        """Add a phase to roadmap"""
        phase = RoadmapPhase.objects.create(
            roadmap=roadmap,
            title=title,
            description=description,
            order=order,
            estimated_duration_weeks=estimated_duration_weeks,
            status='not_started',
            objectives=objectives or []
        )
        return phase

    @staticmethod
    @transaction.atomic
    def add_milestone_to_phase(
        phase: RoadmapPhase,
        title: str,
        description: str,
        milestone_type: str,
        order: int,
        estimated_duration_hours: Decimal,
        is_required: bool = True,
        skills: Optional[List[str]] = None,
        resources: Optional[List[Dict[str, str]]] = None
    ) -> RoadmapMilestone:
        """Add a milestone to phase"""
        milestone = RoadmapMilestone.objects.create(
            phase=phase,
            title=title,
            description=description,
            milestone_type=milestone_type,
            order=order,
            estimated_duration_hours=estimated_duration_hours,
            status='not_started',
            is_required=is_required,
            skills=skills or [],
            resources=resources or []
        )
        return milestone

    @staticmethod
    @transaction.atomic
    def add_course_to_milestone(
        milestone: RoadmapMilestone,
        course: Course,
        order: int,
        is_required: bool = True,
        completion_criteria: Optional[str] = None
    ) -> RoadmapCourse:
        """Associate a course with a milestone"""
        roadmap_course = RoadmapCourse.objects.create(
            milestone=milestone,
            course=course,
            order=order,
            is_required=is_required,
            completion_criteria=completion_criteria or ''
        )
        return roadmap_course

    @staticmethod
    def search_roadmaps(
        query: str,
        user: Optional[User] = None
    ) -> List[Roadmap]:
        """Search roadmaps by title or target career"""
        queryset = Roadmap.objects.filter(
            is_deleted=False
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(target_career__icontains=query) |
            models.Q(description__icontains=query)
        )

        if user:
            queryset = queryset.filter(user=user)

        return list(queryset[:20])

    @staticmethod
    def get_roadmap_statistics(roadmap: Roadmap) -> Dict[str, Any]:
        """Get statistics for a roadmap"""
        total_phases = roadmap.phases.count()
        completed_phases = roadmap.phases.filter(status='completed').count()

        total_milestones = RoadmapMilestone.objects.filter(
            phase__roadmap=roadmap
        ).count()
        completed_milestones = RoadmapMilestone.objects.filter(
            phase__roadmap=roadmap,
            status='completed'
        ).count()

        total_courses = RoadmapCourse.objects.filter(
            milestone__phase__roadmap=roadmap
        ).count()

        estimated_hours = sum(
            float(m.estimated_duration_hours)
            for m in RoadmapMilestone.objects.filter(phase__roadmap=roadmap)
        )

        return {
            'total_phases': total_phases,
            'completed_phases': completed_phases,
            'total_milestones': total_milestones,
            'completed_milestones': completed_milestones,
            'total_courses': total_courses,
            'estimated_total_hours': round(estimated_hours, 2),
            'completion_percentage': float(roadmap.completion_percentage)
        }
