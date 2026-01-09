"""
Course Service Models

Handles course aggregation from multiple platforms (Udemy, Coursera, edX, etc.)
and provides unified course management for the Sha8alny platform.
"""

from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from apps.core.models import BaseModel


class CoursePlatform(BaseModel):
    """
    Represents a learning platform from which courses are aggregated.

    Supports both API-based platforms and web-scraped platforms.
    """

    # Integration types
    API = 'api'
    SCRAPING = 'scraping'
    MANUAL = 'manual'

    INTEGRATION_TYPE_CHOICES = [
        (API, 'API Integration'),
        (SCRAPING, 'Web Scraping'),
        (MANUAL, 'Manual Entry'),
    ]

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Platform name (e.g., 'Udemy', 'Coursera', 'edX')"
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        help_text="URL-friendly identifier (e.g., 'udemy', 'coursera')"
    )

    website_url = models.URLField(
        max_length=1000,
        help_text="Main website URL of the platform"
    )

    logo_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Platform logo image URL"
    )

    description = models.TextField(
        blank=True,
        help_text="Brief description of the platform"
    )

    integration_type = models.CharField(
        max_length=20,
        choices=INTEGRATION_TYPE_CHOICES,
        default=API,
        help_text="How courses are fetched from this platform"
    )

    api_base_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Base URL for API integration (if applicable)"
    )

    api_key_required = models.BooleanField(
        default=False,
        help_text="Whether API key is required for integration"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Whether this platform is actively being scraped/synced"
    )

    last_synced_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time courses were synced from this platform"
    )

    total_courses = models.PositiveIntegerField(
        default=0,
        help_text="Total number of courses from this platform in our database"
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional platform-specific configuration (API endpoints, scraping rules, etc.)"
    )

    class Meta:
        verbose_name = "Course Platform"
        verbose_name_plural = "Course Platforms"
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug'], name='idx_platform_slug'),
            models.Index(fields=['is_active'], name='idx_platform_active'),
        ]

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<CoursePlatform: {self.name} ({self.integration_type})>"


class Course(BaseModel):
    """
    Represents a course from any learning platform.

    Uses JSONB fields for flexible storage of platform-specific data
    (pricing, instructors, curriculum, etc.)
    """

    # Course levels
    BEGINNER = 'beginner'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    ALL_LEVELS = 'all_levels'

    LEVEL_CHOICES = [
        (BEGINNER, 'Beginner'),
        (INTERMEDIATE, 'Intermediate'),
        (ADVANCED, 'Advanced'),
        (ALL_LEVELS, 'All Levels'),
    ]

    # Course types
    VIDEO = 'video'
    TEXT = 'text'
    INTERACTIVE = 'interactive'
    MIXED = 'mixed'

    TYPE_CHOICES = [
        (VIDEO, 'Video Course'),
        (TEXT, 'Text-based Course'),
        (INTERACTIVE, 'Interactive Course'),
        (MIXED, 'Mixed Content'),
    ]

    platform = models.ForeignKey(
        CoursePlatform,
        on_delete=models.CASCADE,
        related_name='courses',
        help_text="Platform where this course is hosted"
    )

    external_id = models.CharField(
        max_length=255,
        help_text="Course ID on the external platform"
    )

    title = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Course title"
    )

    slug = models.SlugField(
        max_length=255,
        help_text="URL-friendly identifier"
    )

    description = models.TextField(
        blank=True,
        help_text="Course description/overview"
    )

    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Brief one-liner description"
    )

    url = models.URLField(
        max_length=1000,
        help_text="Direct link to the course on the platform"
    )

    thumbnail_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Course thumbnail/cover image URL"
    )

    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default=BEGINNER,
        help_text="Course difficulty level"
    )

    course_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=VIDEO,
        help_text="Primary content type"
    )

    language = models.CharField(
        max_length=100,
        default='English',
        help_text="Primary language of instruction"
    )

    # Pricing information
    is_free = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the course is free"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Course price in USD (null if free or variable)"
    )

    currency = models.CharField(
        max_length=10,
        default='USD',
        help_text="Currency code (ISO 4217)"
    )

    # Course metrics
    duration_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Total course duration in hours"
    )

    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('5.00'))
        ],
        help_text="Average user rating (0-5 scale)"
    )

    total_reviews = models.PositiveIntegerField(
        default=0,
        help_text="Total number of reviews/ratings"
    )

    total_enrollments = models.PositiveIntegerField(
        default=0,
        help_text="Total number of students enrolled"
    )

    # Course content structure
    total_lectures = models.PositiveIntegerField(
        default=0,
        help_text="Total number of lectures/lessons"
    )

    total_resources = models.PositiveIntegerField(
        default=0,
        help_text="Total number of downloadable resources"
    )

    # Instructors (stored as JSONB array of objects)
    instructors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of instructors: [{name, bio, avatar_url, rating}]"
    )
    # Example: [
    #     {
    #         "name": "John Doe",
    #         "bio": "Senior Software Engineer...",
    #         "avatar_url": "https://...",
    #         "rating": 4.8
    #     }
    # ]

    # Learning outcomes (stored as JSONB array)
    learning_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text="What students will learn: [outcome1, outcome2, ...]"
    )
    # Example: [
    #     "Build RESTful APIs with Django",
    #     "Implement JWT authentication",
    #     "Deploy to production"
    # ]

    # Prerequisites (stored as JSONB array)
    prerequisites = models.JSONField(
        default=list,
        blank=True,
        help_text="Course prerequisites: [prerequisite1, prerequisite2, ...]"
    )
    # Example: [
    #     "Basic Python knowledge",
    #     "Familiarity with web development"
    # ]

    # Course curriculum/syllabus (stored as JSONB)
    curriculum = models.JSONField(
        default=list,
        blank=True,
        help_text="Course sections and lectures: [{section, lectures: [...]}]"
    )
    # Example: [
    #     {
    #         "section": "Introduction to Django",
    #         "lectures": [
    #             {"title": "What is Django?", "duration_minutes": 10},
    #             {"title": "Setting up environment", "duration_minutes": 15}
    #         ]
    #     }
    # ]

    # Certificates and features
    has_certificate = models.BooleanField(
        default=False,
        help_text="Whether course provides a certificate upon completion"
    )

    has_lifetime_access = models.BooleanField(
        default=False,
        help_text="Whether students get lifetime access"
    )

    has_subtitles = models.BooleanField(
        default=False,
        help_text="Whether course has subtitles/captions"
    )

    # Availability
    is_published = models.BooleanField(
        default=True,
        help_text="Whether course is currently available on the platform"
    )

    published_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the course was first published"
    )

    last_updated = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the course content was last updated"
    )

    # Data sync tracking
    last_synced_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time this course data was synced from the platform"
    )

    sync_error = models.TextField(
        blank=True,
        help_text="Error message if last sync failed"
    )

    # Platform-specific metadata (flexible storage)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Platform-specific data (tags, categories, affiliate links, etc.)"
    )
    # Example: {
    #     "tags": ["web development", "backend", "python"],
    #     "category": "Development",
    #     "subcategory": "Web Development",
    #     "affiliate_link": "https://...",
    #     "discount_available": true
    # }

    # Many-to-many relationship with skills (through CourseSkill)
    skills = models.ManyToManyField(
        'users.Skill',
        through='CourseSkill',
        related_name='courses',
        blank=True,
        help_text="Skills taught in this course"
    )

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['-rating', '-total_enrollments']
        unique_together = [['platform', 'external_id']]
        indexes = [
            models.Index(fields=['platform', 'external_id'], name='idx_course_platform_ext'),
            models.Index(fields=['title'], name='idx_course_title'),
            models.Index(fields=['level'], name='idx_course_level'),
            models.Index(fields=['is_free'], name='idx_course_free'),
            models.Index(fields=['rating'], name='idx_course_rating'),
            models.Index(fields=['-total_enrollments'], name='idx_course_enrollments'),
            models.Index(fields=['language'], name='idx_course_language'),
        ]

    def __str__(self):
        return f"{self.title} ({self.platform.name})"

    def __repr__(self):
        return f"<Course: {self.title} - {self.platform.name} - {self.level}>"

    @property
    def is_highly_rated(self):
        """Check if course has high rating (4.5+)"""
        if self.rating:
            return self.rating >= Decimal('4.5')
        return False

    @property
    def is_popular(self):
        """Check if course is popular (10,000+ enrollments)"""
        return self.total_enrollments >= 10000

    @property
    def formatted_price(self):
        """Return formatted price string"""
        if self.is_free:
            return "Free"
        if self.price:
            return f"{self.currency} {self.price}"
        return "Price varies"

    @property
    def instructor_names(self):
        """Extract instructor names from JSONB"""
        if not self.instructors:
            return []
        return [instructor.get('name', 'Unknown') for instructor in self.instructors]

    @property
    def main_instructor(self):
        """Get primary instructor name"""
        if self.instructors and len(self.instructors) > 0:
            return self.instructors[0].get('name', 'Unknown')
        return 'Unknown'


class CourseSkill(BaseModel):
    """
    Many-to-many relationship between Courses and Skills.

    Tracks which skills are taught in each course and the proficiency level
    students can expect to achieve.
    """

    # Proficiency levels achievable by completing the course
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

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='course_skills',
        help_text="Course that teaches this skill"
    )

    skill = models.ForeignKey(
        'users.Skill',
        on_delete=models.CASCADE,
        related_name='skill_courses',
        help_text="Skill taught in the course"
    )

    proficiency_level = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        default=BEGINNER,
        help_text="Expected proficiency level after completing the course"
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is a primary/core skill of the course"
    )

    coverage_percentage = models.PositiveIntegerField(
        default=50,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100)
        ],
        help_text="How much of the course focuses on this skill (1-100%)"
    )

    class Meta:
        verbose_name = "Course-Skill Relationship"
        verbose_name_plural = "Course-Skill Relationships"
        unique_together = [['course', 'skill']]
        ordering = ['-is_primary', '-coverage_percentage']
        indexes = [
            models.Index(fields=['course', 'skill'], name='idx_courseskill_course_skill'),
            models.Index(fields=['skill'], name='idx_courseskill_skill'),
            models.Index(fields=['is_primary'], name='idx_courseskill_primary'),
        ]

    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.course.title} → {self.skill.name} ({self.proficiency_level}){primary}"

    def __repr__(self):
        return f"<CourseSkill: {self.course.title} - {self.skill.name}>"
