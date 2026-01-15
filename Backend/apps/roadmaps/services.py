"""
Roadmaps Service Layer

Handles roadmap generation, template management, and roadmap operations.
This is where AI-powered roadmap generation will be integrated.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction, models
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
            title=f"{template.title} - {user.full_name or user.email}",
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

        # Create MVP structure (phases and milestones)
        RoadmapService._create_mvp_structure(roadmap, template)

        return roadmap

    @staticmethod
    def _create_mvp_structure(roadmap: Roadmap, template: RoadmapTemplate) -> None:
        """
        Create MVP phase and milestone structure for a roadmap.

        This generates a basic learning path with 3 phases and multiple milestones
        tailored to the target career.
        """
        career_lower = template.target_career.lower()

        # Define career-specific phase structures
        if 'backend' in career_lower:
            phases_data = [
                {
                    'title': 'Fundamentals',
                    'description': 'Master the basics of programming and backend development',
                    'weeks': 8,
                    'objectives': ['Learn Python syntax', 'Understand OOP', 'Master Git basics'],
                    'milestones': [
                        {'title': 'Python Programming Basics', 'type': 'course', 'hours': 40, 'skills': ['Python']},
                        {'title': 'Build CLI Calculator Project', 'type': 'project', 'hours': 10, 'skills': ['Python']},
                        {'title': 'Learn Git & Version Control', 'type': 'course', 'hours': 8, 'skills': ['Git']},
                        {'title': 'Database Fundamentals (SQL)', 'type': 'course', 'hours': 20, 'skills': ['SQL']},
                    ]
                },
                {
                    'title': 'Backend Development',
                    'description': 'Build REST APIs and work with databases',
                    'weeks': 10,
                    'objectives': ['Build REST APIs', 'Work with databases', 'Understand authentication'],
                    'milestones': [
                        {'title': 'Django Framework Basics', 'type': 'course', 'hours': 30, 'skills': ['Django', 'Python']},
                        {'title': 'Build a Blog API', 'type': 'project', 'hours': 20, 'skills': ['Django', 'REST API']},
                        {'title': 'Authentication & Authorization', 'type': 'course', 'hours': 15, 'skills': ['JWT', 'Security']},
                        {'title': 'Database Design & Optimization', 'type': 'course', 'hours': 20, 'skills': ['PostgreSQL', 'SQL']},
                    ]
                },
                {
                    'title': 'Advanced & Deployment',
                    'description': 'Master advanced concepts and deploy applications',
                    'weeks': 6,
                    'objectives': ['Deploy applications', 'Write tests', 'Optimize performance'],
                    'milestones': [
                        {'title': 'Testing with Pytest', 'type': 'course', 'hours': 12, 'skills': ['Testing', 'Pytest']},
                        {'title': 'Docker & Containerization', 'type': 'course', 'hours': 15, 'skills': ['Docker']},
                        {'title': 'Deploy to AWS/Heroku', 'type': 'course', 'hours': 10, 'skills': ['DevOps', 'AWS']},
                        {'title': 'Build Full-Stack E-commerce API', 'type': 'project', 'hours': 40, 'skills': ['Django', 'PostgreSQL', 'Docker']},
                    ]
                }
            ]
        elif 'frontend' in career_lower:
            phases_data = [
                {
                    'title': 'Web Fundamentals',
                    'description': 'Master HTML, CSS, and JavaScript basics',
                    'weeks': 6,
                    'objectives': ['Learn HTML/CSS', 'Master JavaScript basics', 'Build responsive layouts'],
                    'milestones': [
                        {'title': 'HTML & CSS Fundamentals', 'type': 'course', 'hours': 30, 'skills': ['HTML', 'CSS']},
                        {'title': 'Build Landing Page', 'type': 'project', 'hours': 15, 'skills': ['HTML', 'CSS']},
                        {'title': 'JavaScript Basics', 'type': 'course', 'hours': 35, 'skills': ['JavaScript']},
                        {'title': 'Responsive Design', 'type': 'course', 'hours': 12, 'skills': ['CSS', 'Flexbox', 'Grid']},
                    ]
                },
                {
                    'title': 'React Development',
                    'description': 'Build modern web apps with React',
                    'weeks': 8,
                    'objectives': ['Master React', 'Manage state', 'Work with APIs'],
                    'milestones': [
                        {'title': 'React Fundamentals', 'type': 'course', 'hours': 25, 'skills': ['React', 'JSX']},
                        {'title': 'Build Todo App', 'type': 'project', 'hours': 15, 'skills': ['React']},
                        {'title': 'State Management (Redux/Context)', 'type': 'course', 'hours': 20, 'skills': ['Redux', 'Context API']},
                        {'title': 'API Integration & Hooks', 'type': 'course', 'hours': 15, 'skills': ['React Hooks', 'API']},
                    ]
                },
                {
                    'title': 'Advanced & TypeScript',
                    'description': 'Master TypeScript and advanced patterns',
                    'weeks': 6,
                    'objectives': ['Learn TypeScript', 'Optimize performance', 'Deploy applications'],
                    'milestones': [
                        {'title': 'TypeScript for React', 'type': 'course', 'hours': 20, 'skills': ['TypeScript', 'React']},
                        {'title': 'Performance Optimization', 'type': 'course', 'hours': 12, 'skills': ['React', 'Performance']},
                        {'title': 'Testing with Jest & React Testing Library', 'type': 'course', 'hours': 15, 'skills': ['Testing', 'Jest']},
                        {'title': 'Build E-commerce Frontend', 'type': 'project', 'hours': 40, 'skills': ['React', 'TypeScript', 'Redux']},
                    ]
                }
            ]
        elif 'data' in career_lower or 'scientist' in career_lower:
            phases_data = [
                {
                    'title': 'Python & Statistics',
                    'description': 'Master Python and statistical foundations',
                    'weeks': 8,
                    'objectives': ['Learn Python', 'Master statistics', 'Work with data'],
                    'milestones': [
                        {'title': 'Python for Data Science', 'type': 'course', 'hours': 35, 'skills': ['Python', 'NumPy', 'Pandas']},
                        {'title': 'Statistics & Probability', 'type': 'course', 'hours': 30, 'skills': ['Statistics']},
                        {'title': 'Data Visualization', 'type': 'course', 'hours': 20, 'skills': ['Matplotlib', 'Seaborn']},
                        {'title': 'Exploratory Data Analysis Project', 'type': 'project', 'hours': 15, 'skills': ['Pandas', 'Visualization']},
                    ]
                },
                {
                    'title': 'Machine Learning',
                    'description': 'Build and train ML models',
                    'weeks': 12,
                    'objectives': ['Understand ML algorithms', 'Build models', 'Evaluate performance'],
                    'milestones': [
                        {'title': 'Machine Learning Fundamentals', 'type': 'course', 'hours': 40, 'skills': ['ML', 'Scikit-learn']},
                        {'title': 'Supervised Learning', 'type': 'course', 'hours': 25, 'skills': ['Classification', 'Regression']},
                        {'title': 'Unsupervised Learning', 'type': 'course', 'hours': 20, 'skills': ['Clustering', 'PCA']},
                        {'title': 'Build Predictive Model', 'type': 'project', 'hours': 30, 'skills': ['ML', 'Python']},
                    ]
                },
                {
                    'title': 'Deep Learning & Deployment',
                    'description': 'Master deep learning and model deployment',
                    'weeks': 8,
                    'objectives': ['Learn deep learning', 'Deploy models', 'Work with big data'],
                    'milestones': [
                        {'title': 'Deep Learning with TensorFlow', 'type': 'course', 'hours': 35, 'skills': ['Deep Learning', 'TensorFlow']},
                        {'title': 'Computer Vision Basics', 'type': 'course', 'hours': 20, 'skills': ['CNN', 'Computer Vision']},
                        {'title': 'Model Deployment', 'type': 'course', 'hours': 15, 'skills': ['MLOps', 'Flask']},
                        {'title': 'Build Image Classification App', 'type': 'project', 'hours': 30, 'skills': ['Deep Learning', 'Deployment']},
                    ]
                }
            ]
        elif 'fullstack' in career_lower or 'full stack' in career_lower or 'full-stack' in career_lower:
            phases_data = [
                {
                    'title': 'Frontend Foundations',
                    'description': 'Master HTML, CSS, JavaScript, and React',
                    'weeks': 10,
                    'objectives': ['Learn web fundamentals', 'Master React', 'Build UIs'],
                    'milestones': [
                        {'title': 'HTML, CSS & JavaScript', 'type': 'course', 'hours': 40, 'skills': ['HTML', 'CSS', 'JavaScript']},
                        {'title': 'React Fundamentals', 'type': 'course', 'hours': 25, 'skills': ['React']},
                        {'title': 'Build Portfolio Website', 'type': 'project', 'hours': 20, 'skills': ['React', 'CSS']},
                    ]
                },
                {
                    'title': 'Backend Development',
                    'description': 'Build APIs and work with databases',
                    'weeks': 12,
                    'objectives': ['Build APIs', 'Database design', 'Authentication'],
                    'milestones': [
                        {'title': 'Python & Django/Flask', 'type': 'course', 'hours': 35, 'skills': ['Python', 'Django']},
                        {'title': 'Database & SQL', 'type': 'course', 'hours': 25, 'skills': ['SQL', 'PostgreSQL']},
                        {'title': 'REST API Development', 'type': 'course', 'hours': 20, 'skills': ['REST API']},
                        {'title': 'Build CRUD API', 'type': 'project', 'hours': 25, 'skills': ['Django', 'PostgreSQL']},
                    ]
                },
                {
                    'title': 'Full-Stack Integration',
                    'description': 'Connect frontend and backend, deploy apps',
                    'weeks': 10,
                    'objectives': ['Full-stack integration', 'Deploy applications', 'DevOps basics'],
                    'milestones': [
                        {'title': 'API Integration in React', 'type': 'course', 'hours': 15, 'skills': ['React', 'API']},
                        {'title': 'Authentication Flow', 'type': 'course', 'hours': 20, 'skills': ['JWT', 'Security']},
                        {'title': 'Docker & Deployment', 'type': 'course', 'hours': 18, 'skills': ['Docker', 'DevOps']},
                        {'title': 'Build Full-Stack Social App', 'type': 'project', 'hours': 50, 'skills': ['React', 'Django', 'PostgreSQL']},
                    ]
                }
            ]
        else:
            # Generic structure for other careers
            phases_data = [
                {
                    'title': 'Foundations',
                    'description': f'Learn the fundamentals of {template.target_career}',
                    'weeks': 8,
                    'objectives': ['Master basics', 'Build foundation', 'Practice fundamentals'],
                    'milestones': [
                        {'title': 'Core Concepts', 'type': 'course', 'hours': 30, 'skills': []},
                        {'title': 'Practical Exercises', 'type': 'practice', 'hours': 20, 'skills': []},
                        {'title': 'Beginner Project', 'type': 'project', 'hours': 15, 'skills': []},
                    ]
                },
                {
                    'title': 'Intermediate Skills',
                    'description': f'Develop intermediate {template.target_career} skills',
                    'weeks': 10,
                    'objectives': ['Apply knowledge', 'Build projects', 'Gain experience'],
                    'milestones': [
                        {'title': 'Advanced Topics', 'type': 'course', 'hours': 35, 'skills': []},
                        {'title': 'Real-world Application', 'type': 'project', 'hours': 30, 'skills': []},
                    ]
                },
                {
                    'title': 'Advanced & Professional',
                    'description': f'Master advanced {template.target_career} concepts',
                    'weeks': 6,
                    'objectives': ['Expert-level skills', 'Portfolio project', 'Job readiness'],
                    'milestones': [
                        {'title': 'Expert Techniques', 'type': 'course', 'hours': 25, 'skills': []},
                        {'title': 'Capstone Project', 'type': 'project', 'hours': 40, 'skills': []},
                    ]
                }
            ]

        # Create phases and milestones from the structure
        for phase_idx, phase_data in enumerate(phases_data, start=1):
            phase = RoadmapPhase.objects.create(
                roadmap=roadmap,
                title=phase_data['title'],
                description=phase_data['description'],
                order=phase_idx,
                estimated_duration_weeks=phase_data['weeks'],
                status='not_started',
                objectives=phase_data.get('objectives', [])
            )

            for milestone_idx, milestone_data in enumerate(phase_data['milestones'], start=1):
                RoadmapMilestone.objects.create(
                    phase=phase,
                    title=milestone_data['title'],
                    description=f"Complete {milestone_data['title']} as part of the {phase.title} phase",
                    milestone_type=milestone_data['type'],
                    order=milestone_idx,
                    estimated_duration_hours=Decimal(str(milestone_data['hours'])),
                    status='not_started',
                    is_required=True,
                    skills=milestone_data.get('skills', []),
                    resources=[]
                )

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
        is_primary: bool = False,
        match_score: Decimal = Decimal('0.00'),
        recommendation_reason: str = ''
    ) -> RoadmapCourse:
        """Associate a course with a milestone"""
        roadmap_course = RoadmapCourse.objects.create(
            milestone=milestone,
            course=course,
            order=order,
            is_primary=is_primary,
            match_score=match_score,
            recommendation_reason=recommendation_reason
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
