"""
Career Tools Service Layer

Handles resume building, ATS optimization, and portfolio management.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal
from django.db import transaction
from django.core.files.base import ContentFile

from .models import Resume, Portfolio
from apps.users.models import User
from apps.notifications.signals import resume_generated, resume_optimized, portfolio_published


class ResumeService:
    """Service for resume management and generation"""

    @staticmethod
    @transaction.atomic
    def create_resume(
        user: User,
        title: str,
        template_name: str = "modern",
        **resume_data
    ) -> Resume:
        """
        Create a new resume.

        Args:
            user: User instance
            title: Resume title
            template_name: Template to use
            **resume_data: Resume section data (personal_info, work_experience, etc.)

        Returns:
            Resume: Created resume
        """
        # If this is the first resume, make it primary
        existing_count = Resume.objects.filter(user=user, is_deleted=False).count()
        is_primary = existing_count == 0

        resume = Resume.objects.create(
            user=user,
            title=title,
            template_name=template_name,
            personal_info=resume_data.get('personal_info', {}),
            work_experience=resume_data.get('work_experience', {}),
            education=resume_data.get('education', {}),
            skills=resume_data.get('skills', {}),
            certifications=resume_data.get('certifications', {}),
            projects=resume_data.get('projects', {}),
            languages=resume_data.get('languages', {}),
            is_primary=is_primary,
            ats_processing_status='completed'
        )

        # Emit signal
        resume_generated.send(sender=Resume, instance=resume, user=user)

        return resume

    @staticmethod
    def get_user_resumes(user: User) -> List[Resume]:
        """Get all resumes for user"""
        return list(Resume.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-is_primary', '-updated_at'))

    @staticmethod
    def get_primary_resume(user: User) -> Optional[Resume]:
        """Get user's primary resume"""
        try:
            return Resume.objects.get(
                user=user,
                is_primary=True,
                is_deleted=False
            )
        except Resume.DoesNotExist:
            # Return most recent resume
            return Resume.objects.filter(
                user=user,
                is_deleted=False
            ).order_by('-updated_at').first()

    @staticmethod
    def get_resume_by_id(resume_id: str) -> Optional[Resume]:
        """Get resume by ID"""
        try:
            return Resume.objects.get(id=resume_id, is_deleted=False)
        except Resume.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def update_resume(
        resume: Resume,
        **fields
    ) -> Resume:
        """Update resume data"""
        allowed_fields = [
            'title', 'template_name', 'personal_info', 'work_experience',
            'education', 'skills', 'certifications', 'projects', 'languages'
        ]

        for field, value in fields.items():
            if field in allowed_fields:
                setattr(resume, field, value)

        # Increment version
        resume.version += 1
        resume.save()

        return resume

    @staticmethod
    @transaction.atomic
    def set_primary_resume(resume: Resume) -> Resume:
        """Set resume as primary (unset others)"""
        # Unset all primary resumes for this user
        Resume.objects.filter(
            user=resume.user,
            is_primary=True,
            is_deleted=False
        ).update(is_primary=False)

        # Set this as primary
        resume.is_primary = True
        resume.save(update_fields=['is_primary', 'updated_at'])

        return resume

    @staticmethod
    def generate_pdf(resume: Resume) -> Resume:
        """
        Generate PDF file for resume.

        This would integrate with a PDF generation library.
        For now, it's a placeholder.
        """
        # TODO: Implement actual PDF generation
        # from reportlab.pdfgen import canvas
        # or use weasyprint, pdfkit, etc.

        # Placeholder: Create dummy PDF data
        pdf_content = b"PDF placeholder"
        resume.pdf_file.save(
            f"resume_{resume.id}.pdf",
            ContentFile(pdf_content),
            save=True
        )

        return resume

    @staticmethod
    def generate_docx(resume: Resume) -> Resume:
        """
        Generate DOCX file for resume.

        This would integrate with python-docx library.
        For now, it's a placeholder.
        """
        # TODO: Implement actual DOCX generation
        # from docx import Document

        # Placeholder: Create dummy DOCX data
        docx_content = b"DOCX placeholder"
        resume.docx_file.save(
            f"resume_{resume.id}.docx",
            ContentFile(docx_content),
            save=True
        )

        return resume

    @staticmethod
    @transaction.atomic
    def optimize_for_ats(resume: Resume) -> Resume:
        """
        Optimize resume for ATS systems using AI.

        Placeholder for a future hosted-Gemini ATS review task.
        """
        # Set processing status
        resume.ats_processing_status = 'pending'
        resume.save(update_fields=['ats_processing_status', 'updated_at'])

        # TODO: Trigger async Celery task for AI analysis
        # tasks.optimize_resume_ats.delay(resume.id)

        # Placeholder: Set dummy score
        resume.ats_score = Decimal('75.00')
        resume.is_ats_optimized = True
        resume.ats_suggestions = {
            'improvements': [
                'Add more action verbs',
                'Quantify achievements',
                'Include relevant keywords'
            ]
        }
        resume.ats_processing_status = 'completed'
        resume.save()

        # Emit signal
        resume_optimized.send(sender=Resume, instance=resume)

        return resume


class PortfolioService:
    """Service for portfolio management"""

    @staticmethod
    @transaction.atomic
    def create_portfolio(
        user: User,
        title: str,
        description: str = "",
        custom_url_slug: Optional[str] = None,
        theme: str = "default"
    ) -> Portfolio:
        """
        Create a new portfolio.

        Args:
            user: User instance
            title: Portfolio title
            description: Portfolio description
            custom_url_slug: Custom URL slug
            theme: Theme to use

        Returns:
            Portfolio: Created portfolio
        """
        portfolio = Portfolio.objects.create(
            user=user,
            title=title,
            description=description,
            custom_url_slug=custom_url_slug,
            theme=theme,
            is_public=False  # Start as private
        )

        return portfolio

    @staticmethod
    def get_user_portfolios(user: User) -> List[Portfolio]:
        """Get all portfolios for user"""
        return list(Portfolio.objects.filter(
            user=user,
            is_deleted=False
        ).order_by('-updated_at'))

    @staticmethod
    def get_portfolio_by_id(portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        try:
            return Portfolio.objects.get(id=portfolio_id, is_deleted=False)
        except Portfolio.DoesNotExist:
            return None

    @staticmethod
    def get_portfolio_by_slug(slug: str) -> Optional[Portfolio]:
        """Get public portfolio by custom URL slug"""
        try:
            return Portfolio.objects.get(
                custom_url_slug=slug,
                is_public=True,
                is_deleted=False
            )
        except Portfolio.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def update_portfolio(
        portfolio: Portfolio,
        **fields
    ) -> Portfolio:
        """Update portfolio data"""
        allowed_fields = [
            'title', 'description', 'projects', 'achievements',
            'testimonials', 'theme', 'custom_styles', 'custom_url_slug'
        ]

        for field, value in fields.items():
            if field in allowed_fields:
                setattr(portfolio, field, value)

        portfolio.save()
        return portfolio

    @staticmethod
    @transaction.atomic
    def publish_portfolio(portfolio: Portfolio) -> Portfolio:
        """Make portfolio public"""
        portfolio.is_public = True
        portfolio.save(update_fields=['is_public', 'updated_at'])

        # Emit signal
        portfolio_published.send(sender=Portfolio, instance=portfolio)

        return portfolio

    @staticmethod
    @transaction.atomic
    def unpublish_portfolio(portfolio: Portfolio) -> Portfolio:
        """Make portfolio private"""
        portfolio.is_public = False
        portfolio.save(update_fields=['is_public', 'updated_at'])

        return portfolio

    @staticmethod
    def increment_view_count(portfolio: Portfolio) -> None:
        """Increment portfolio view count"""
        portfolio.increment_view_count()

    @staticmethod
    @transaction.atomic
    def add_project_to_portfolio(
        portfolio: Portfolio,
        project_data: Dict[str, Any]
    ) -> Portfolio:
        """
        Add project to portfolio.

        Args:
            portfolio: Portfolio instance
            project_data: Project information dict

        Returns:
            Portfolio: Updated portfolio
        """
        projects = portfolio.projects

        # Initialize if needed
        if not isinstance(projects, dict):
            projects = {'items': []}
        if 'items' not in projects:
            projects['items'] = []

        # Add new project
        projects['items'].append(project_data)
        portfolio.projects = projects
        portfolio.save()

        return portfolio

    @staticmethod
    @transaction.atomic
    def add_achievement_to_portfolio(
        portfolio: Portfolio,
        achievement_data: Dict[str, Any]
    ) -> Portfolio:
        """Add achievement to portfolio"""
        achievements = portfolio.achievements

        if not isinstance(achievements, dict):
            achievements = {'items': []}
        if 'items' not in achievements:
            achievements['items'] = []

        achievements['items'].append(achievement_data)
        portfolio.achievements = achievements
        portfolio.save()

        return portfolio

    @staticmethod
    @transaction.atomic
    def add_testimonial_to_portfolio(
        portfolio: Portfolio,
        testimonial_data: Dict[str, Any]
    ) -> Portfolio:
        """Add testimonial to portfolio"""
        testimonials = portfolio.testimonials

        if not isinstance(testimonials, dict):
            testimonials = {'items': []}
        if 'items' not in testimonials:
            testimonials['items'] = []

        testimonials['items'].append(testimonial_data)
        portfolio.testimonials = testimonials
        portfolio.save()

        return portfolio
