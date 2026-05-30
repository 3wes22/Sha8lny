"""
Roadmaps Service Layer

Handles roadmap generation, template management, and roadmap operations.
This is where AI-powered roadmap generation will be integrated.
"""

import math
from time import monotonic
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

    GENERATOR_VERSION = 'roadmap-generator-v1'
    GENERATOR_MODEL = 'sha8alny-roadmap-v1'

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
        elif 'mobile' in career_lower or 'flutter' in career_lower or 'ios' in career_lower or 'android' in career_lower:
            phases_data = [
                {
                    'title': 'Mobile Fundamentals',
                    'description': 'Learn mobile development basics and build your first app',
                    'weeks': 6,
                    'objectives': ['Learn Dart/Flutter or Swift/Kotlin', 'Build basic UI layouts', 'Understand mobile navigation'],
                    'milestones': [
                        {'title': 'Dart & Flutter Basics (or Swift/Kotlin)', 'type': 'course', 'hours': 30, 'skills': ['Flutter', 'Dart']},
                        {'title': 'Build a Simple Counter/Calculator App', 'type': 'project', 'hours': 10, 'skills': ['Flutter']},
                        {'title': 'Mobile UI Layouts & Navigation', 'type': 'course', 'hours': 20, 'skills': ['Flutter', 'Mobile UI']},
                        {'title': 'State Management Basics', 'type': 'course', 'hours': 15, 'skills': ['Provider', 'State Management']},
                    ]
                },
                {
                    'title': 'App Development',
                    'description': 'Build real apps with API integration and local storage',
                    'weeks': 8,
                    'objectives': ['Integrate REST APIs', 'Handle local storage', 'Build multi-screen apps'],
                    'milestones': [
                        {'title': 'REST API Integration in Flutter', 'type': 'course', 'hours': 20, 'skills': ['API', 'HTTP']},
                        {'title': 'Local Storage & SQLite', 'type': 'course', 'hours': 12, 'skills': ['SQLite', 'Storage']},
                        {'title': 'Build a Notes/Task Manager App', 'type': 'project', 'hours': 25, 'skills': ['Flutter', 'API', 'SQLite']},
                        {'title': 'Push Notifications & Platform Features', 'type': 'course', 'hours': 10, 'skills': ['Notifications', 'Platform APIs']},
                    ]
                },
                {
                    'title': 'Publishing & Portfolio',
                    'description': 'Polish, test, and publish your app',
                    'weeks': 6,
                    'objectives': ['Write tests', 'Optimize performance', 'Publish to stores'],
                    'milestones': [
                        {'title': 'Testing Mobile Apps', 'type': 'course', 'hours': 12, 'skills': ['Testing', 'Widget Tests']},
                        {'title': 'Performance Optimization', 'type': 'course', 'hours': 10, 'skills': ['Performance', 'Profiling']},
                        {'title': 'App Store & Play Store Submission', 'type': 'course', 'hours': 8, 'skills': ['Publishing', 'App Store']},
                        {'title': 'Build & Publish a Portfolio App', 'type': 'project', 'hours': 35, 'skills': ['Flutter', 'Publishing']},
                    ]
                }
            ]
        elif 'devops' in career_lower or 'sre' in career_lower or 'cloud' in career_lower:
            phases_data = [
                {
                    'title': 'Linux & Networking Fundamentals',
                    'description': 'Master the foundations of systems and networking',
                    'weeks': 6,
                    'objectives': ['Learn Linux command line', 'Understand networking', 'Master Git workflows'],
                    'milestones': [
                        {'title': 'Linux Command Line & Shell Scripting', 'type': 'course', 'hours': 25, 'skills': ['Linux', 'Bash']},
                        {'title': 'Networking Fundamentals (TCP/IP, DNS, HTTP)', 'type': 'course', 'hours': 15, 'skills': ['Networking']},
                        {'title': 'Git Workflows & Collaboration', 'type': 'course', 'hours': 10, 'skills': ['Git']},
                        {'title': 'Set Up a Linux Server (VPS)', 'type': 'project', 'hours': 12, 'skills': ['Linux', 'SSH']},
                    ]
                },
                {
                    'title': 'Containers & CI/CD',
                    'description': 'Learn Docker, CI/CD pipelines, and infrastructure automation',
                    'weeks': 10,
                    'objectives': ['Master Docker', 'Build CI/CD pipelines', 'Learn infrastructure as code'],
                    'milestones': [
                        {'title': 'Docker & Docker Compose', 'type': 'course', 'hours': 25, 'skills': ['Docker', 'Containers']},
                        {'title': 'CI/CD with GitHub Actions', 'type': 'course', 'hours': 18, 'skills': ['CI/CD', 'GitHub Actions']},
                        {'title': 'Infrastructure as Code (Terraform basics)', 'type': 'course', 'hours': 20, 'skills': ['Terraform', 'IaC']},
                        {'title': 'Containerize & Deploy a Full-Stack App', 'type': 'project', 'hours': 25, 'skills': ['Docker', 'CI/CD']},
                    ]
                },
                {
                    'title': 'Cloud & Monitoring',
                    'description': 'Deploy to cloud and implement monitoring',
                    'weeks': 8,
                    'objectives': ['Learn a cloud platform', 'Set up monitoring', 'Obtain a certification'],
                    'milestones': [
                        {'title': 'AWS or GCP Fundamentals', 'type': 'course', 'hours': 30, 'skills': ['AWS', 'Cloud']},
                        {'title': 'Monitoring & Logging (Prometheus, Grafana)', 'type': 'course', 'hours': 15, 'skills': ['Monitoring', 'Grafana']},
                        {'title': 'AWS Cloud Practitioner Certification Prep', 'type': 'course', 'hours': 20, 'skills': ['AWS', 'Certification']},
                        {'title': 'Build a Production-Ready Deployment Pipeline', 'type': 'project', 'hours': 30, 'skills': ['AWS', 'Docker', 'CI/CD', 'Monitoring']},
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
    def derive_target_career_from_assessment(assessment: Optional[AssessmentResult]) -> Optional[str]:
        """Derive target career from assessment recommendations."""
        if not assessment:
            return None

        selected_target = (getattr(assessment.assessment, 'target_career', '') or '').strip()
        if selected_target:
            return selected_target

        roadmap_signal = assessment.roadmap_signal if isinstance(assessment.roadmap_signal, dict) else {}
        signal_role = (roadmap_signal.get('role') or '').strip()
        if signal_role:
            return signal_role.replace('_', ' ').title()

        recommended_careers = assessment.recommended_careers or []
        for item in recommended_careers:
            title = (item or {}).get('title') if isinstance(item, dict) else None
            if isinstance(title, str) and title.strip():
                return title.strip()

        return None

    @staticmethod
    def derive_current_level_from_assessment(assessment: Optional[AssessmentResult]) -> str:
        """Map assessment score to a readable current level."""
        if not assessment:
            return 'beginner'

        score = float(assessment.overall_score or 0)
        if score >= 80:
            return 'advanced'
        if score >= 55:
            return 'intermediate'
        return 'beginner'

    @staticmethod
    def default_target_level(_: Optional[str] = None) -> str:
        """Default target outcome for generated roadmaps."""
        return 'job-ready'

    @staticmethod
    def _dedupe_preserve_order(values: List[str]) -> List[str]:
        """Deduplicate strings while preserving order and removing blanks."""
        deduped: List[str] = []
        seen = set()

        for value in values:
            cleaned = (value or '').strip()
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped.append(cleaned)

        return deduped

    @staticmethod
    def _humanize_signal_key(value: str) -> str:
        return (value or '').replace('_', ' ').strip().title()

    @staticmethod
    def _signal_gap_entries(assessment: Optional[AssessmentResult]) -> List[Dict[str, Any]]:
        if not assessment or not isinstance(assessment.roadmap_signal, dict):
            return []
        entries = assessment.roadmap_signal.get('subskill_gaps') or []
        return [entry for entry in entries if isinstance(entry, dict)]

    @staticmethod
    def _extract_gap_labels(assessment: Optional[AssessmentResult]) -> List[str]:
        signal_entries = RoadmapService._signal_gap_entries(assessment)
        if signal_entries:
            ordered = sorted(
                signal_entries,
                key=lambda entry: (entry.get('gap', 0), -entry.get('confidence', 0)),
                reverse=True,
            )
            return RoadmapService._dedupe_preserve_order(
                [RoadmapService._humanize_signal_key(entry.get('subskill_key', '')) for entry in ordered]
            )[:4]
        if not assessment:
            return []
        return RoadmapService._dedupe_preserve_order(assessment.areas_for_improvement or [])[:4]

    @staticmethod
    def _extract_priority_skills(assessment: Optional[AssessmentResult]) -> List[str]:
        """Get prioritized skills from assessment recommendations."""
        if not assessment:
            return []

        roadmap_signal = assessment.roadmap_signal if isinstance(assessment.roadmap_signal, dict) else {}
        priority_order = roadmap_signal.get('priority_order') or []
        if isinstance(priority_order, list) and priority_order:
            return RoadmapService._dedupe_preserve_order(
                [RoadmapService._humanize_signal_key(item) for item in priority_order if isinstance(item, str)]
            )[:4]

        learning_paths = assessment.recommended_learning_paths or []
        extracted: List[str] = []
        for item in learning_paths:
            if isinstance(item, dict):
                skill = item.get('skill')
                if isinstance(skill, str):
                    extracted.append(skill)
            elif isinstance(item, str):
                extracted.append(item)

        return RoadmapService._dedupe_preserve_order(extracted)[:4]

    @staticmethod
    def _extract_top_skills(assessment: Optional[AssessmentResult]) -> List[str]:
        """Get strongest current skills from assessment results."""
        if not assessment:
            return []

        signal_entries = RoadmapService._signal_gap_entries(assessment)
        if signal_entries:
            ordered = sorted(
                signal_entries,
                key=lambda entry: (entry.get('gap', 0), -entry.get('observed_level', 0)),
            )
            return RoadmapService._dedupe_preserve_order(
                [RoadmapService._humanize_signal_key(entry.get('subskill_key', '')) for entry in ordered]
            )[:3]

        return RoadmapService._dedupe_preserve_order(
            [item.get('skill', '') for item in assessment.top_skills if isinstance(item, dict)]
        )[:3]

    @staticmethod
    def _portfolio_project_title(target_career: str) -> str:
        """Return a role-specific proof-of-work milestone title."""
        career_lower = target_career.lower()

        if 'backend' in career_lower:
            return 'Ship a production-style backend API project'
        if 'frontend' in career_lower:
            return 'Ship a responsive frontend portfolio project'
        if 'data' in career_lower or 'scientist' in career_lower:
            return 'Publish an end-to-end data analysis case study'
        if 'fullstack' in career_lower or 'full stack' in career_lower or 'full-stack' in career_lower:
            return 'Ship a full-stack portfolio application'
        if 'mobile' in career_lower or 'flutter' in career_lower or 'ios' in career_lower or 'android' in career_lower:
            return 'Publish a polished mobile app to App Store or Play Store'
        if 'devops' in career_lower or 'sre' in career_lower or 'cloud' in career_lower:
            return 'Build and document a CI/CD pipeline for a real project'

        return f'Ship a portfolio project aligned with {target_career}'

    @staticmethod
    def _build_personalized_phase_blueprint(
        target_career: str,
        current_level: str,
        strengths: List[str],
        gaps: List[str],
        priority_skills: List[str],
        top_skills: List[str],
        weekly_hours: int,
    ) -> List[Dict[str, Any]]:
        """Create a deterministic, assessment-aware roadmap structure."""
        total_focus_items = max(1, len(priority_skills) + len(gaps))
        base_hours = {
            'beginner': 96,
            'intermediate': 72,
            'advanced': 54,
        }.get(current_level, 72)
        total_hours = base_hours + (total_focus_items * 10)
        estimated_weeks = max(8, math.ceil(total_hours / max(weekly_hours, 1)))

        first_skill = priority_skills[0] if priority_skills else (top_skills[0] if top_skills else target_career)
        second_skill = priority_skills[1] if len(priority_skills) > 1 else first_skill
        first_gap = gaps[0] if gaps else f'{target_career} fundamentals'
        second_gap = gaps[1] if len(gaps) > 1 else 'project execution'
        lead_strength = strengths[0] if strengths else 'your strongest skills'

        phase_weeks = [
            max(2, math.ceil(estimated_weeks * 0.3)),
            max(2, math.ceil(estimated_weeks * 0.4)),
            max(2, estimated_weeks - max(2, math.ceil(estimated_weeks * 0.3)) - max(2, math.ceil(estimated_weeks * 0.4))),
        ]
        if phase_weeks[2] < 2:
            phase_weeks[1] = max(2, phase_weeks[1] - (2 - phase_weeks[2]))
            phase_weeks[2] = 2

        return [
            {
                'title': f'Stabilize your {target_career} baseline',
                'description': (
                    f'Anchor the roadmap around your current {current_level} signal and '
                    f'build repeatable confidence with {first_skill}.'
                ),
                'weeks': phase_weeks[0],
                'objectives': [
                    f'Clarify what job-ready {target_career} performance looks like.',
                    f'Strengthen {first_skill} with deliberate practice.',
                    'Create momentum before the heavier gap-closing work starts.',
                ],
                'milestones': [
                    {'title': f'Audit your current {target_career} baseline', 'type': 'practice', 'hours': 6, 'skills': top_skills[:2] or [first_skill]},
                    {'title': f'Strengthen {first_skill} foundations', 'type': 'course', 'hours': 14, 'skills': [first_skill]},
                    {'title': f'Build a scoped practice project using {first_skill}', 'type': 'project', 'hours': 18, 'skills': [first_skill]},
                ],
            },
            {
                'title': 'Close the highest-priority gaps',
                'description': (
                    f'Turn the assessment gaps into explicit milestones so the roadmap stays '
                    f'personal instead of generic.'
                ),
                'weeks': phase_weeks[1],
                'objectives': [
                    f'Close the {first_gap} gap with focused work.',
                    f'Build working confidence with {second_skill}.',
                    'Translate weak spots into visible progress.',
                ],
                'milestones': [
                    {'title': f'Close the {first_gap} gap', 'type': 'practice', 'hours': 12, 'skills': [first_gap]},
                    {'title': f'Build working confidence with {second_skill}', 'type': 'course', 'hours': 12, 'skills': [second_skill]},
                    {'title': f'Apply {second_gap} in a guided project sprint', 'type': 'project', 'hours': 20, 'skills': [second_gap, second_skill]},
                ],
            },
            {
                'title': 'Ship proof and become job-ready',
                'description': (
                    f'Use {lead_strength} as an advantage while packaging your work for real '
                    f'{target_career} opportunities.'
                ),
                'weeks': phase_weeks[2],
                'objectives': [
                    'Produce portfolio evidence that matches the target role.',
                    'Turn project work into resume and interview stories.',
                    'Run a focused job search with clear next actions.',
                ],
                'milestones': [
                    {'title': RoadmapService._portfolio_project_title(target_career), 'type': 'project', 'hours': 24, 'skills': [first_skill, second_skill]},
                    {'title': f'Turn {lead_strength} into resume-ready and interview-ready stories', 'type': 'practice', 'hours': 8, 'skills': strengths[:2] or [lead_strength]},
                    {'title': f'Run a targeted {target_career} job search sprint', 'type': 'practice', 'hours': 8, 'skills': [target_career]},
                ],
            },
        ]

    @staticmethod
    def _create_personalized_structure(roadmap: Roadmap, phases_data: List[Dict[str, Any]]) -> None:
        """Persist the generated roadmap hierarchy."""
        for phase_idx, phase_data in enumerate(phases_data, start=1):
            phase = RoadmapPhase.objects.create(
                roadmap=roadmap,
                title=phase_data['title'],
                description=phase_data['description'],
                order=phase_idx,
                estimated_duration_weeks=phase_data['weeks'],
                status='not_started',
                objectives=phase_data.get('objectives', []),
            )

            for milestone_idx, milestone_data in enumerate(phase_data.get('milestones', []), start=1):
                RoadmapMilestone.objects.create(
                    phase=phase,
                    title=milestone_data['title'],
                    description=(
                        milestone_data.get('description')
                        or f"Complete {milestone_data['title']} during the {phase.title} phase."
                    ),
                    milestone_type=milestone_data['type'],
                    order=milestone_idx,
                    estimated_duration_hours=Decimal(str(milestone_data['hours'])),
                    status='not_started',
                    is_required=True,
                    skills=milestone_data.get('skills', []),
                    resources=[],
                )

    @staticmethod
    def _build_generation_input_summary(
        *,
        target_career: str,
        current_level: str,
        target_level: str,
        weekly_hours: int,
        strengths: List[str],
        gaps: List[str],
        priority_skills: List[str],
        top_skills: List[str],
    ) -> Dict[str, Any]:
        return {
            'target_career': target_career,
            'current_level': current_level,
            'target_level': target_level,
            'weekly_hours_commitment': weekly_hours,
            'top_strengths': strengths,
            'priority_skills': priority_skills,
            'top_skills': top_skills,
            'gaps': gaps,
        }

    @staticmethod
    @transaction.atomic
    def create_ai_roadmap_shell(
        user: User,
        assessment: Optional[AssessmentResult],
        target_career: str,
        current_level: str,
        target_level: str,
        weekly_hours: int = 10,
    ) -> Roadmap:
        if assessment:
            existing = Roadmap.objects.filter(
                user=user,
                assessment=assessment,
                status__in=[Roadmap.DRAFT, Roadmap.ACTIVE, Roadmap.IN_PROGRESS],
                is_deleted=False,
            ).order_by('-created_at').first()
            if existing:
                return existing

        matched_template = RoadmapTemplateService.get_template_by_career(target_career)
        template = matched_template[0] if matched_template else None
        top_skills = RoadmapService._extract_top_skills(assessment)
        priority_skills = RoadmapService._extract_priority_skills(assessment)
        strengths = top_skills[:3] if top_skills else (assessment.strengths[:3] if assessment else [])
        gaps = RoadmapService._extract_gap_labels(assessment)

        metadata = {
            'generation': {
                'source': 'assessment_result' if assessment else 'manual_request',
                'version': RoadmapService.GENERATOR_VERSION,
                'runtime_version': None,
                'assessment_id': str(assessment.id) if assessment else None,
                'template_basis_id': str(template.id) if template else None,
                'status': 'pending',
                'task_id': None,
                'trace_id': None,
                'fallback_used': False,
                'error_code': None,
                'provider': None,
                'input_summary': RoadmapService._build_generation_input_summary(
                    target_career=target_career,
                    current_level=current_level,
                    target_level=target_level,
                    weekly_hours=weekly_hours,
                    strengths=strengths,
                    gaps=gaps,
                    priority_skills=priority_skills,
                    top_skills=top_skills,
                ),
            }
        }

        return Roadmap.objects.create(
            user=user,
            template=template,
            assessment=assessment,
            title=f"{target_career} roadmap for {user.full_name or user.username or user.email}",
            description=f'Personalized roadmap for {target_career}, paced for {weekly_hours} focused hours each week.',
            target_career=target_career,
            current_level=current_level,
            target_level=target_level,
            weekly_hours_commitment=weekly_hours,
            estimated_duration_weeks=0,
            status='draft',
            ai_processing_status='pending',
            metadata=metadata,
        )

    @staticmethod
    @transaction.atomic
    def populate_ai_roadmap(roadmap: Roadmap, *, task_id: Optional[str] = None) -> Roadmap:
        from apps.roadmaps.ai_pipeline import RoadmapAIService

        if roadmap.ai_processing_status == 'completed' and roadmap.phases.exists():
            return roadmap

        started_at = monotonic()
        assessment = roadmap.assessment
        matched_template = RoadmapTemplateService.get_template_by_career(roadmap.target_career)
        template = roadmap.template or (matched_template[0] if matched_template else None)
        top_skills = RoadmapService._extract_top_skills(assessment)
        priority_skills = RoadmapService._extract_priority_skills(assessment)
        strengths = top_skills[:3] if top_skills else (assessment.strengths[:3] if assessment else [])
        gaps = RoadmapService._extract_gap_labels(assessment)

        generation = roadmap.metadata.get('generation', {}) if isinstance(roadmap.metadata, dict) else {}
        generation.update(
            {
                'status': 'processing',
                'task_id': task_id or generation.get('task_id'),
                'template_basis_id': str(template.id) if template else None,
                'input_summary': RoadmapService._build_generation_input_summary(
                    target_career=roadmap.target_career,
                    current_level=roadmap.current_level,
                    target_level=roadmap.target_level,
                    weekly_hours=roadmap.weekly_hours_commitment,
                    strengths=strengths,
                    gaps=gaps,
                    priority_skills=priority_skills,
                    top_skills=top_skills,
                ),
            }
        )

        roadmap.ai_processing_status = 'processing'
        roadmap.ai_processing_error = ''
        roadmap.metadata = {**(roadmap.metadata if isinstance(roadmap.metadata, dict) else {}), 'generation': generation}
        if template and roadmap.template_id != template.id:
            roadmap.template = template
        roadmap.save(update_fields=['ai_processing_status', 'ai_processing_error', 'metadata', 'template', 'updated_at'])

        phases_data = RoadmapService._build_personalized_phase_blueprint(
            target_career=roadmap.target_career,
            current_level=roadmap.current_level,
            strengths=strengths,
            gaps=gaps,
            priority_skills=priority_skills,
            top_skills=top_skills,
            weekly_hours=roadmap.weekly_hours_commitment,
        )
        estimated_duration_weeks = sum(phase['weeks'] for phase in phases_data)
        default_summary = (
            f'This roadmap prioritizes {", ".join(priority_skills[:2]) or roadmap.target_career} and closes '
            f'the most visible gaps from your latest assessment.'
        )
        personalization = RoadmapAIService.personalize_blueprint(
            target_career=roadmap.target_career,
            current_level=roadmap.current_level,
            target_level=roadmap.target_level,
            weekly_hours=roadmap.weekly_hours_commitment,
            strengths=strengths,
            gaps=gaps,
            priority_skills=priority_skills,
            top_skills=top_skills,
            phases_data=phases_data,
            default_summary=default_summary,
        )

        roadmap.phases.all().delete()
        RoadmapService._create_personalized_structure(roadmap, personalization.phases)
        RoadmapService.match_courses_for_roadmap(roadmap)

        generation.update(
            {
                'status': 'completed',
                'runtime_version': personalization.metadata.version,
                'trace_id': personalization.metadata.trace_id,
                'fallback_used': personalization.metadata.fallback_used,
                'error_code': personalization.metadata.error_code,
                'provider': personalization.metadata.provider,
            }
        )
        roadmap.metadata = {**(roadmap.metadata if isinstance(roadmap.metadata, dict) else {}), 'generation': generation}
        roadmap.description = personalization.summary
        roadmap.estimated_duration_weeks = estimated_duration_weeks
        roadmap.ai_processing_status = 'completed'
        roadmap.ai_processed_at = timezone.now()
        roadmap.llm_model_used = personalization.metadata.model or ''
        roadmap.llm_prompt_tokens = personalization.prompt_tokens
        roadmap.llm_completion_tokens = personalization.completion_tokens
        roadmap.processing_time_seconds = Decimal(f"{monotonic() - started_at:.2f}")
        roadmap.ai_insights = {
            'summary': personalization.summary,
            'strengths': strengths,
            'gaps': gaps,
            'priority_skills': priority_skills,
            'top_skills': top_skills,
            'job_readiness_focus': roadmap.target_career,
            'coaching_notes': personalization.coaching_notes,
        }
        roadmap.save(
            update_fields=[
                'description',
                'estimated_duration_weeks',
                'ai_processing_status',
                'ai_processed_at',
                'llm_model_used',
                'llm_prompt_tokens',
                'llm_completion_tokens',
                'processing_time_seconds',
                'ai_insights',
                'metadata',
                'updated_at',
            ]
        )

        roadmap_generated.send(
            sender=Roadmap,
            instance=roadmap,
            user=roadmap.user
        )

        return roadmap

    @staticmethod
    def _milestone_search_query(milestone: RoadmapMilestone, roadmap: Roadmap) -> str:
        """Build the embedding search query from milestone skills and roadmap context."""
        skills = milestone.skills if isinstance(milestone.skills, list) else []
        skill_text = ", ".join(str(item) for item in skills[:5])
        return f"{roadmap.target_career} {milestone.title} {skill_text}".strip()

    @staticmethod
    def match_courses_for_milestone(
        milestone: RoadmapMilestone,
        roadmap: Roadmap,
        *,
        top_k: Optional[int] = None,
    ) -> None:
        """Link embedding-matched courses to a milestone (no LLM call)."""
        from apps.core.ai_settings import COURSE_INDEX_TOP_K
        from apps.courses.course_index import CourseIndex

        if milestone.milestone_type != RoadmapMilestone.COURSE:
            return

        query = RoadmapService._milestone_search_query(milestone, roadmap)
        matches = CourseIndex.search(query, top_k=top_k or COURSE_INDEX_TOP_K)
        if not matches:
            return

        linked_course_ids = set(milestone.courses.values_list("course_id", flat=True))
        order = milestone.courses.count()

        for match in matches:
            course_id = match.get("course_id")
            if not course_id or course_id in linked_course_ids:
                continue
            try:
                course = Course.objects.get(id=course_id, is_deleted=False)
            except Course.DoesNotExist:
                continue

            order += 1
            score = Decimal(str(round(float(match.get("score", 0)) * 100, 2)))
            RoadmapService.add_course_to_milestone(
                milestone=milestone,
                course=course,
                order=order,
                is_primary=order == 1,
                match_score=score,
                recommendation_reason=(
                    f"Embedding similarity match ({score}%) for {milestone.title}."
                ),
            )
            linked_course_ids.add(course_id)

    @staticmethod
    def match_courses_for_roadmap(roadmap: Roadmap) -> None:
        """Attach embedding-matched courses to all course-type milestones on a roadmap."""
        for phase in roadmap.phases.filter(is_deleted=False).prefetch_related("milestones"):
            for milestone in phase.milestones.filter(is_deleted=False):
                RoadmapService.match_courses_for_milestone(milestone, roadmap)

    @staticmethod
    def record_generation_failure(
        roadmap: Roadmap,
        *,
        error_message: str,
        error_code: Optional[str] = None,
    ) -> Roadmap:
        generation = roadmap.metadata.get('generation', {}) if isinstance(roadmap.metadata, dict) else {}
        generation.update({'status': 'failed', 'error_code': error_code or generation.get('error_code')})
        roadmap.metadata = {**(roadmap.metadata if isinstance(roadmap.metadata, dict) else {}), 'generation': generation}
        roadmap.ai_processing_status = 'failed'
        roadmap.ai_processing_error = error_message
        roadmap.save(update_fields=['metadata', 'ai_processing_status', 'ai_processing_error', 'updated_at'])
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

        Delegates to ``create_ai_roadmap_shell`` and ``populate_ai_roadmap`` which
        use the shared Gemini runtime with deterministic fallbacks.

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
        roadmap = RoadmapService.create_ai_roadmap_shell(
            user=user,
            assessment=assessment,
            target_career=target_career,
            current_level=current_level,
            target_level=target_level,
            weekly_hours=weekly_hours,
        )
        RoadmapService.populate_ai_roadmap(roadmap)
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
