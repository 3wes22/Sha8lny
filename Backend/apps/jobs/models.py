"""
Jobs Module Models

Handles job market data including job platforms, job listings, skill requirements,
market insights, and skill demand analytics.

Based on SRS FR-18 to FR-21: Job scraping, normalization, search, and insights.
"""

from django.db import models
from django.core.validators import URLValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from apps.core.models import BaseModel


class JobPlatform(BaseModel):
    """
    Job listing platforms (Wuzzuf, Bayt, LinkedIn, etc.)

    Stores configuration for job scraping and API integration.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Platform name (e.g., 'Wuzzuf', 'LinkedIn', 'Bayt')"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly identifier"
    )

    website_url = models.URLField(
        max_length=500,
        help_text="Platform's main website URL"
    )

    logo_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Platform logo URL"
    )

    # API/Scraping Configuration
    has_api = models.BooleanField(
        default=False,
        help_text="Whether platform provides an API"
    )

    api_endpoint = models.URLField(
        max_length=500,
        blank=True,
        help_text="API base URL if available"
    )

    requires_scraping = models.BooleanField(
        default=True,
        help_text="Whether web scraping is needed"
    )

    scraping_enabled = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether scraping is currently active"
    )

    # Geographic Focus
    target_countries = models.JSONField(
        default=list,
        blank=True,
        help_text="List of countries this platform covers (e.g., ['Egypt', 'Saudi Arabia'])"
    )

    # Platform Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether platform is actively being used"
    )

    last_scraped_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of last successful scrape"
    )

    class Meta:
        verbose_name = "Job Platform"
        verbose_name_plural = "Job Platforms"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'], name='idx_job_platform_name'),
            models.Index(fields=['slug'], name='idx_job_platform_slug'),
            models.Index(fields=['is_active'], name='idx_job_platform_active'),
            models.Index(fields=['scraping_enabled'], name='idx_job_platform_scraping'),
        ]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<JobPlatform: {self.name} ({self.slug})>"

    @property
    def needs_scraping(self):
        """Check if platform needs scraping."""
        return self.requires_scraping and self.scraping_enabled and self.is_active


class Job(BaseModel):
    """
    Job listings scraped or fetched from platforms.

    Stores normalized job data with 24-hour cache expiry.
    """

    # Job Type Choices
    FULL_TIME = 'full_time'
    PART_TIME = 'part_time'
    CONTRACT = 'contract'
    INTERNSHIP = 'internship'
    FREELANCE = 'freelance'

    JOB_TYPE_CHOICES = [
        (FULL_TIME, 'Full Time'),
        (PART_TIME, 'Part Time'),
        (CONTRACT, 'Contract'),
        (INTERNSHIP, 'Internship'),
        (FREELANCE, 'Freelance'),
    ]

    # Experience Level Choices
    ENTRY = 'entry'
    MID = 'mid'
    SENIOR = 'senior'
    LEAD = 'lead'
    EXECUTIVE = 'executive'

    EXPERIENCE_LEVEL_CHOICES = [
        (ENTRY, 'Entry Level'),
        (MID, 'Mid Level'),
        (SENIOR, 'Senior Level'),
        (LEAD, 'Lead/Manager'),
        (EXECUTIVE, 'Executive'),
    ]

    # Remote Type Choices
    FULLY_REMOTE = 'fully_remote'
    HYBRID = 'hybrid'
    ON_SITE = 'on_site'

    REMOTE_TYPE_CHOICES = [
        (FULLY_REMOTE, 'Fully Remote'),
        (HYBRID, 'Hybrid'),
        (ON_SITE, 'On-Site'),
    ]

    # Salary Period Choices
    YEARLY = 'yearly'
    MONTHLY = 'monthly'
    HOURLY = 'hourly'

    SALARY_PERIOD_CHOICES = [
        (YEARLY, 'Yearly'),
        (MONTHLY, 'Monthly'),
        (HOURLY, 'Hourly'),
    ]

    # Relationships
    platform = models.ForeignKey(
        JobPlatform,
        on_delete=models.CASCADE,
        related_name='jobs',
        help_text="Platform this job was scraped from"
    )

    # Job Identification
    external_id = models.CharField(
        max_length=255,
        help_text="Platform's unique job ID"
    )

    external_url = models.URLField(
        max_length=1000,
        help_text="Direct link to job posting on platform"
    )

    # Job Information
    title = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Job title"
    )

    company_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Company offering the job"
    )

    company_logo_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text="Company logo URL"
    )

    # Job Description
    description = models.TextField(
        blank=True,
        help_text="Full job description"
    )

    requirements = models.TextField(
        blank=True,
        help_text="Job requirements and qualifications"
    )

    responsibilities = models.TextField(
        blank=True,
        help_text="Job responsibilities and duties"
    )

    # Location
    location_city = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="City location"
    )

    location_country = models.CharField(
        max_length=100,
        default='Egypt',
        db_index=True,
        help_text="Country location"
    )

    is_remote = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether job is remote"
    )

    remote_type = models.CharField(
        max_length=50,
        choices=REMOTE_TYPE_CHOICES,
        blank=True,
        help_text="Remote work arrangement"
    )

    # Employment Details
    job_type = models.CharField(
        max_length=50,
        choices=JOB_TYPE_CHOICES,
        blank=True,
        db_index=True,
        help_text="Employment type"
    )

    experience_level = models.CharField(
        max_length=50,
        choices=EXPERIENCE_LEVEL_CHOICES,
        blank=True,
        db_index=True,
        help_text="Required experience level"
    )

    experience_years_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Minimum years of experience required"
    )

    experience_years_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Maximum years of experience required"
    )

    # Salary
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Minimum salary"
    )

    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum salary"
    )

    salary_currency = models.CharField(
        max_length=10,
        default='EGP',
        help_text="Salary currency code (ISO 4217)"
    )

    salary_period = models.CharField(
        max_length=50,
        choices=SALARY_PERIOD_CHOICES,
        blank=True,
        help_text="Salary payment period"
    )

    salary_disclosed = models.BooleanField(
        default=False,
        help_text="Whether salary information is publicly disclosed"
    )

    # Application Details
    application_deadline = models.DateField(
        blank=True,
        null=True,
        help_text="Application deadline date"
    )

    posted_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        help_text="Date job was posted"
    )

    # Platform-Specific Data
    platform_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional platform-specific fields"
    )

    # Caching
    last_fetched_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time job data was fetched"
    )

    cache_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text="When cached job data expires (24hr TTL)"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether job posting is still active"
    )

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ['-posted_date', '-created_at']
        indexes = [
            models.Index(fields=['platform', 'external_id'], name='idx_job_platform_ext'),
            models.Index(fields=['title'], name='idx_job_title'),
            models.Index(fields=['company_name'], name='idx_job_company'),
            models.Index(fields=['location_city'], name='idx_job_city'),
            models.Index(fields=['location_country'], name='idx_job_country'),
            models.Index(fields=['job_type'], name='idx_job_type'),
            models.Index(fields=['experience_level'], name='idx_job_exp_level'),
            models.Index(fields=['is_remote'], name='idx_job_remote'),
            models.Index(fields=['is_active'], name='idx_job_active'),
            models.Index(fields=['cache_expires_at'], name='idx_job_cache_exp'),
            models.Index(fields=['posted_date'], name='idx_job_posted'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['platform', 'external_id'],
                name='unique_job_platform_external_id'
            )
        ]

    def __str__(self):
        return f"{self.title} at {self.company_name}"

    def __repr__(self):
        return f"<Job: {self.title} - {self.company_name} ({self.platform.name})>"

    def save(self, *args, **kwargs):
        """Set cache expiry to 24 hours from now if not set."""
        if not self.cache_expires_at:
            self.cache_expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if cached job data is expired."""
        if not self.cache_expires_at:
            return True
        return timezone.now() > self.cache_expires_at

    @property
    def salary_range_display(self):
        """Get formatted salary range."""
        if not self.salary_min and not self.salary_max:
            return "Not disclosed"

        if self.salary_min and self.salary_max:
            return f"{self.salary_currency} {self.salary_min:,.2f} - {self.salary_max:,.2f} ({self.salary_period})"
        elif self.salary_min:
            return f"{self.salary_currency} {self.salary_min:,.2f}+ ({self.salary_period})"
        else:
            return f"Up to {self.salary_currency} {self.salary_max:,.2f} ({self.salary_period})"


class JobSkill(BaseModel):
    """
    Skills required for jobs (many-to-many relationship).

    Links jobs to required skills with proficiency levels.
    """

    # Proficiency Level Choices
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'

    PROFICIENCY_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
        (EXPERT, 'Expert'),
    ]

    # Relationships
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='job_skills',
        help_text="Job requiring this skill"
    )

    skill = models.ForeignKey(
        'users.Skill',
        on_delete=models.CASCADE,
        related_name='job_skills',
        help_text="Required skill"
    )

    # Skill Details
    is_required = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether skill is required or just nice-to-have"
    )

    proficiency_level = models.CharField(
        max_length=50,
        choices=PROFICIENCY_CHOICES,
        blank=True,
        help_text="Required proficiency level"
    )

    years_required = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Years of experience required with this skill"
    )

    class Meta:
        verbose_name = "Job Skill"
        verbose_name_plural = "Job Skills"
        ordering = ['-is_required', 'skill__name']
        indexes = [
            models.Index(fields=['job'], name='idx_jobskill_job'),
            models.Index(fields=['skill'], name='idx_jobskill_skill'),
            models.Index(fields=['is_required'], name='idx_jobskill_required'),
        ]

    def __str__(self):
        required = "Required" if self.is_required else "Nice-to-have"
        return f"{self.skill.name} ({required}) for {self.job.title}"

    def __repr__(self):
        return f"<JobSkill: {self.skill.name} for {self.job.id}>"


class MarketInsight(BaseModel):
    """
    Market analytics and trends.

    Aggregated insights about job demand, salary trends, and skill trends.
    """

    # Insight Type Choices
    JOB_DEMAND = 'job_demand'
    SALARY_TREND = 'salary_trend'
    SKILL_TREND = 'skill_trend'
    COMPANY_HIRING = 'company_hiring'
    LOCATION_TREND = 'location_trend'

    INSIGHT_TYPE_CHOICES = [
        (JOB_DEMAND, 'Job Demand Analysis'),
        (SALARY_TREND, 'Salary Trend Analysis'),
        (SKILL_TREND, 'Skill Trend Analysis'),
        (COMPANY_HIRING, 'Company Hiring Trends'),
        (LOCATION_TREND, 'Location Trends'),
    ]

    insight_type = models.CharField(
        max_length=50,
        choices=INSIGHT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of market insight"
    )

    career_field = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Career field (e.g., 'Backend Development', 'Data Science')"
    )

    country = models.CharField(
        max_length=100,
        default='Egypt',
        db_index=True,
        help_text="Country for this insight"
    )

    # Time Period
    data_period_start = models.DateField(
        help_text="Start date of data period"
    )

    data_period_end = models.DateField(
        help_text="End date of data period"
    )

    # Insights Data (JSONB)
    insights_data = models.JSONField(
        default=dict,
        help_text="Aggregated insights and analytics data"
    )
    # Example structure:
    # {
    #   "total_jobs": 1234,
    #   "average_salary": 50000,
    #   "top_skills": ["Python", "Django", "PostgreSQL"],
    #   "top_companies": ["Company A", "Company B"],
    #   "trend_direction": "rising",
    #   "trend_percentage": 15.5
    # }

    total_jobs_analyzed = models.PositiveIntegerField(
        default=0,
        help_text="Number of jobs analyzed for this insight"
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this insight was generated"
    )

    class Meta:
        verbose_name = "Market Insight"
        verbose_name_plural = "Market Insights"
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['insight_type'], name='idx_insight_type'),
            models.Index(fields=['career_field'], name='idx_insight_field'),
            models.Index(fields=['country'], name='idx_insight_country'),
            models.Index(fields=['generated_at'], name='idx_insight_generated'),
            models.Index(
                fields=['insight_type', 'career_field', 'country'],
                name='idx_insight_composite'
            ),
        ]

    def __str__(self):
        return f"{self.get_insight_type_display()} - {self.career_field} ({self.country})"

    def __repr__(self):
        return f"<MarketInsight: {self.insight_type} - {self.career_field}>"


class SkillDemand(BaseModel):
    """
    Trending skills data by month and country.

    Tracks skill demand over time for trend analysis.
    """

    # Trend Direction Choices
    RISING = 'rising'
    STABLE = 'stable'
    DECLINING = 'declining'

    TREND_CHOICES = [
        (RISING, 'Rising'),
        (STABLE, 'Stable'),
        (DECLINING, 'Declining'),
    ]

    # Relationships
    skill = models.ForeignKey(
        'users.Skill',
        on_delete=models.CASCADE,
        related_name='demand_data',
        help_text="Skill being tracked"
    )

    country = models.CharField(
        max_length=100,
        default='Egypt',
        db_index=True,
        help_text="Country for this demand data"
    )

    month = models.DateField(
        db_index=True,
        help_text="Month of data (first day of month)"
    )

    # Demand Metrics
    demand_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of jobs requiring this skill in this month"
    )

    trend_direction = models.CharField(
        max_length=50,
        choices=TREND_CHOICES,
        db_index=True,
        help_text="Trend direction compared to previous month"
    )

    trend_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('-100.00')), MaxValueValidator(Decimal('1000.00'))],
        help_text="Percentage change from previous month"
    )

    # Salary Data
    average_salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Average minimum salary for jobs requiring this skill"
    )

    average_salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Average maximum salary for jobs requiring this skill"
    )

    # Top Job Titles
    top_job_titles = models.JSONField(
        default=list,
        blank=True,
        help_text="List of most common job titles requiring this skill"
    )
    # Example: ["Backend Developer", "Full Stack Engineer", "Django Developer"]

    class Meta:
        verbose_name = "Skill Demand"
        verbose_name_plural = "Skill Demand Data"
        ordering = ['-month', '-demand_count']
        indexes = [
            models.Index(fields=['skill'], name='idx_skilldemand_skill'),
            models.Index(fields=['country'], name='idx_skilldemand_country'),
            models.Index(fields=['month'], name='idx_skilldemand_month'),
            models.Index(fields=['trend_direction'], name='idx_skilldemand_trend'),
            models.Index(
                fields=['skill', 'country', 'month'],
                name='idx_skilldemand_composite'
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['skill', 'country', 'month'],
                name='unique_skill_country_month'
            )
        ]

    def __str__(self):
        return f"{self.skill.name} - {self.country} ({self.month.strftime('%B %Y')})"

    def __repr__(self):
        return f"<SkillDemand: {self.skill.name} - {self.month.strftime('%Y-%m')}>"

    @property
    def trend_display(self):
        """Get formatted trend display."""
        direction_symbol = {
            'rising': '↑',
            'stable': '→',
            'declining': '↓'
        }.get(self.trend_direction, '')

        return f"{direction_symbol} {self.trend_percentage:+.1f}%"
