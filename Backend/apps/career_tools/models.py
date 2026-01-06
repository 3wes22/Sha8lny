"""
Career Tools Module Models

Implements career development tools including:
- Resume: Resume builder with ATS optimization
- Portfolio: Portfolio showcase with public sharing
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel
from apps.users.models import User


class Resume(BaseModel):
    """
    User resume with ATS optimization and multiple format support.

    Stores resume data as JSONB for flexibility and supports
    PDF/DOCX binary storage for downloads.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resumes',
        help_text="User who owns this resume"
    )

    # Resume Information
    title = models.CharField(
        max_length=255,
        help_text="Resume title (e.g., 'Software Engineer Resume', 'My Primary Resume')"
    )

    template_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Template used for this resume (e.g., 'modern', 'classic', 'minimal')"
    )

    # Resume Data (Stored as JSONB for flexibility)
    personal_info = models.JSONField(
        default=dict,
        help_text="Personal information: name, email, phone, location, summary, etc."
    )

    work_experience = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of work experience objects with company, role, duration, achievements"
    )

    education = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of education objects with institution, degree, field, dates"
    )

    skills = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of skills with proficiency levels"
    )

    certifications = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of certifications with name, issuer, date, expiry"
    )

    projects = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of projects with title, description, technologies, links"
    )

    languages = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of languages with proficiency levels"
    )

    # ATS Optimization
    is_ats_optimized = models.BooleanField(
        default=False,
        help_text="Whether this resume has been optimized for ATS systems"
    )

    ats_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="ATS optimization score (0-100)"
    )

    ats_suggestions = models.JSONField(
        default=dict,
        blank=True,
        help_text="AI-generated suggestions for improving ATS score"
    )

    # File Storage (Binary data for PDF and DOCX formats)
    pdf_data = models.BinaryField(
        null=True,
        blank=True,
        help_text="Resume as PDF binary data"
    )

    docx_data = models.BinaryField(
        null=True,
        blank=True,
        help_text="Resume as DOCX binary data"
    )

    # Metadata
    is_primary = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this is the user's primary/default resume"
    )

    version = models.PositiveIntegerField(
        default=1,
        help_text="Resume version number (for tracking revisions)"
    )

    class Meta:
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"
        ordering = ['-is_primary', '-updated_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_resume_user'),
            models.Index(fields=['user', 'is_primary'], name='idx_resume_primary'),
            models.Index(fields=['-ats_score'], name='idx_resume_ats'),
            models.Index(fields=['-created_at'], name='idx_resume_created'),
        ]

    def __str__(self):
        primary_badge = " (Primary)" if self.is_primary else ""
        return f"{self.user.email} - {self.title}{primary_badge}"

    @property
    def ats_grade_display(self):
        """Convert ATS score to letter grade"""
        if not self.ats_score:
            return "Not Scored"

        score = float(self.ats_score)
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    @property
    def has_files(self):
        """Check if resume has generated files"""
        return bool(self.pdf_data or self.docx_data)

    @property
    def file_formats_available(self):
        """List available file formats"""
        formats = []
        if self.pdf_data:
            formats.append("PDF")
        if self.docx_data:
            formats.append("DOCX")
        return ", ".join(formats) if formats else "None"

    @property
    def completeness_percentage(self):
        """Calculate resume completeness based on filled sections"""
        sections = [
            bool(self.personal_info and self.personal_info != {}),
            bool(self.work_experience and self.work_experience != {}),
            bool(self.education and self.education != {}),
            bool(self.skills and self.skills != {}),
            bool(self.certifications and self.certifications != {}),
            bool(self.projects and self.projects != {}),
            bool(self.languages and self.languages != {}),
        ]
        filled_sections = sum(sections)
        return round((filled_sections / 7) * 100, 1)

    @property
    def pdf_size_mb(self):
        """Get PDF file size in MB"""
        if not self.pdf_data:
            return 0
        return round(len(self.pdf_data) / (1024 * 1024), 2)

    @property
    def docx_size_mb(self):
        """Get DOCX file size in MB"""
        if not self.docx_data:
            return 0
        return round(len(self.docx_data) / (1024 * 1024), 2)


class Portfolio(BaseModel):
    """
    User portfolio for showcasing projects and achievements.

    Supports public sharing with custom URLs and analytics tracking.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolios',
        help_text="User who owns this portfolio"
    )

    # Portfolio Information
    title = models.CharField(
        max_length=255,
        help_text="Portfolio title (e.g., 'John Doe - Full Stack Developer')"
    )

    description = models.TextField(
        blank=True,
        help_text="Portfolio description or bio"
    )

    # Portfolio Data (Stored as JSONB)
    projects = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of project objects with title, description, images, links, technologies"
    )

    achievements = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of achievements, awards, recognitions"
    )

    testimonials = models.JSONField(
        default=dict,
        blank=True,
        help_text="Array of testimonials and recommendations"
    )

    # Customization
    theme = models.CharField(
        max_length=100,
        default='default',
        help_text="Portfolio theme/template (e.g., 'default', 'modern', 'minimal')"
    )

    custom_styles = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom CSS/styling options as JSON"
    )

    # Visibility
    is_public = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this portfolio is publicly accessible"
    )

    custom_url_slug = models.SlugField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Custom URL slug for public portfolio (e.g., 'john-doe')"
    )

    # Analytics
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of views"
    )

    last_viewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last view"
    )

    class Meta:
        verbose_name = "Portfolio"
        verbose_name_plural = "Portfolios"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_portfolio_user'),
            models.Index(fields=['custom_url_slug'], name='idx_portfolio_slug'),
            models.Index(fields=['is_public'], name='idx_portfolio_public'),
        ]

    def __str__(self):
        visibility = "Public" if self.is_public else "Private"
        return f"{self.user.email} - {self.title} ({visibility})"

    @property
    def public_url(self):
        """Generate public portfolio URL"""
        if not self.is_public or not self.custom_url_slug:
            return None
        return f"/portfolio/{self.custom_url_slug}"

    @property
    def project_count(self):
        """Count number of projects in portfolio"""
        if not self.projects or self.projects == {}:
            return 0
        if isinstance(self.projects, dict) and 'items' in self.projects:
            return len(self.projects['items'])
        if isinstance(self.projects, list):
            return len(self.projects)
        return 0

    @property
    def has_testimonials(self):
        """Check if portfolio has testimonials"""
        if not self.testimonials or self.testimonials == {}:
            return False
        if isinstance(self.testimonials, dict) and 'items' in self.testimonials:
            return len(self.testimonials['items']) > 0
        if isinstance(self.testimonials, list):
            return len(self.testimonials) > 0
        return False

    @property
    def achievement_count(self):
        """Count number of achievements"""
        if not self.achievements or self.achievements == {}:
            return 0
        if isinstance(self.achievements, dict) and 'items' in self.achievements:
            return len(self.achievements['items'])
        if isinstance(self.achievements, list):
            return len(self.achievements)
        return 0

    @property
    def completeness_percentage(self):
        """Calculate portfolio completeness"""
        sections = [
            bool(self.title),
            bool(self.description),
            self.project_count > 0,
            self.achievement_count > 0,
            self.has_testimonials,
        ]
        filled_sections = sum(sections)
        return round((filled_sections / 5) * 100, 1)

    def increment_view_count(self):
        """Increment view count and update last viewed timestamp"""
        from django.utils import timezone
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=['view_count', 'last_viewed_at'])
