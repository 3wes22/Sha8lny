from decimal import Decimal
from datetime import date, timedelta

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import BaseModel
from apps.users.managers import UserManager


def validate_age(value):
    """
    Validate that user is at least 13 years old.

    Args:
        value: Date of birth

    Raises:
        ValidationError: If user is under 13 years old
    """
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

    if age < 13:
        raise ValidationError(
            _('You must be at least 13 years old to register.'),
            code='age_restriction'
        )


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    Custom user model for Sha8alny platform.

    Uses Auth0 for authentication while storing profile data locally.
    Inherits UUID, timestamps, and soft delete from BaseModel.
    """

    # Authentication Fields
    auth0_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Auth0 user identifier')
    )

    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$',
                message=_('Enter a valid email address.'),
                code='invalid_email'
            )
        ],
        help_text=_('User email address')
    )

    email_verified = models.BooleanField(
        default=False,
        help_text=_('Whether email has been verified')
    )

    username = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text=_('Unique username')
    )

    # Profile Information
    full_name = models.CharField(
        max_length=255,
        help_text=_('User full name')
    )

    date_of_birth = models.DateField(
        validators=[validate_age],
        help_text=_('Date of birth (must be 13+ years old)')
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Phone number')
    )

    # Account Status
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether user account is active')
    )

    is_staff = models.BooleanField(
        default=False,
        help_text=_('Whether user can access admin site')
    )

    is_premium = models.BooleanField(
        default=False,
        help_text=_('Whether user has premium subscription')
    )

    ACCOUNT_STATUS_CHOICES = [
        ('active', _('Active')),
        ('suspended', _('Suspended')),
        ('deleted', _('Deleted')),
    ]

    account_status = models.CharField(
        max_length=50,
        choices=ACCOUNT_STATUS_CHOICES,
        default='active',
        help_text=_('Account status')
    )

    # Onboarding
    onboarding_completed = models.BooleanField(
        default=False,
        help_text=_('Whether user has completed onboarding')
    )

    onboarding_step = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Current onboarding step (0-indexed)')
    )

    # Preferences
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('ar', _('Arabic')),
    ]

    preferred_language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='en',
        help_text=_('Preferred language')
    )

    timezone = models.CharField(
        max_length=50,
        default='Africa/Cairo',
        help_text=_('User timezone')
    )

    # Audit Fields
    last_login_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last login timestamp')
    )

    # Custom manager
    objects = UserManager()

    # Django auth configuration
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name', 'date_of_birth']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='idx_users_email'),
            models.Index(fields=['auth0_id'], name='idx_users_auth0_id'),
            models.Index(fields=['username'], name='idx_users_username'),
            models.Index(fields=['last_login_at'], name='idx_users_last_login'),
        ]
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self):
        """String representation using email."""
        return self.email

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<User id={self.id} email={self.email}>'

    def get_full_name(self):
        """Return user's full name."""
        return self.full_name

    def get_short_name(self):
        """Return user's email as short name."""
        return self.email

    @property
    def age(self):
        """Calculate and return user's age."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Skill(BaseModel):
    """
    Master skill taxonomy.

    Represents all available skills in the system (technical, soft, business, etc.).
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('Skill name')
    )

    slug = models.SlugField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_('URL-friendly skill identifier')
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text=_('Skill description')
    )

    CATEGORY_CHOICES = [
        ('technical', _('Technical')),
        ('soft', _('Soft Skills')),
        ('business', _('Business')),
        ('design', _('Design')),
        ('data', _('Data & Analytics')),
        ('marketing', _('Marketing')),
        ('other', _('Other')),
    ]

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES,
        help_text=_('Skill category')
    )

    # Hierarchical skills (e.g., Python -> Django)
    parent_skill = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sub_skills',
        help_text=_('Parent skill if this is a sub-skill')
    )

    SKILL_LEVEL_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert')),
    ]

    skill_level = models.CharField(
        max_length=50,
        choices=SKILL_LEVEL_CHOICES,
        blank=True,
        null=True,
        help_text=_('Typical skill level for this skill')
    )

    # Metadata
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether skill is active in the system')
    )

    popularity_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Popularity score for ranking')
    )

    class Meta:
        db_table = 'skills'
        ordering = ['-popularity_score', 'name']
        indexes = [
            models.Index(fields=['name'], name='idx_skills_name'),
            models.Index(fields=['slug'], name='idx_skills_slug'),
            models.Index(fields=['category'], name='idx_skills_category'),
            models.Index(fields=['parent_skill'], name='idx_skills_parent'),
            models.Index(fields=['-popularity_score'], name='idx_skills_popularity'),
        ]
        verbose_name = _('Skill')
        verbose_name_plural = _('Skills')

    def __str__(self):
        """String representation using skill name."""
        return self.name

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<Skill id={self.id} name={self.name} category={self.category}>'


class UserSkill(BaseModel):
    """
    Junction table linking users to their skills.

    Tracks user's proficiency level and experience with each skill.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_skills',
        help_text=_('User who has this skill')
    )

    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='user_skills',
        help_text=_('Skill')
    )

    SKILL_TYPE_CHOICES = [
        ('hard', _('Hard Skill')),
        ('soft', _('Soft Skill')),
    ]

    skill_type = models.CharField(
        max_length=50,
        choices=SKILL_TYPE_CHOICES,
        help_text=_('Skill type')
    )

    PROFICIENCY_CHOICES = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert')),
    ]

    proficiency_level = models.CharField(
        max_length=50,
        choices=PROFICIENCY_CHOICES,
        blank=True,
        null=True,
        help_text=_('User proficiency level')
    )

    years_of_experience = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(Decimal("99.99"))],
        help_text=_('Years of experience with this skill')
    )

    SOURCE_CHOICES = [
        ('user_input', _('User Input')),
        ('assessment', _('Assessment')),
        ('verified', _('Verified')),
    ]

    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        default='user_input',
        help_text=_('Source of skill data')
    )

    # Verification (Future feature)
    is_verified = models.BooleanField(
        default=False,
        help_text=_('Whether skill is verified')
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When skill was verified')
    )

    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_skills',
        help_text=_('Who verified this skill')
    )

    class Meta:
        db_table = 'user_skills'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='idx_user_skills_user'),
            models.Index(fields=['skill'], name='idx_user_skills_skill'),
            models.Index(fields=['skill_type'], name='idx_user_skills_type'),
            models.Index(fields=['proficiency_level'], name='idx_user_skills_proficiency'),
        ]
        unique_together = [['user', 'skill']]
        verbose_name = _('User Skill')
        verbose_name_plural = _('User Skills')

    def __str__(self):
        """String representation."""
        return f'{self.user.username} - {self.skill.name} ({self.proficiency_level})'

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<UserSkill user={self.user.username} skill={self.skill.name}>'


class UserPreferences(BaseModel):
    """
    User preferences and settings.

    Stores notification, privacy, and learning preferences.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        help_text=_('User')
    )

    # Notification Preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive email notifications')
    )

    push_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive push notifications')
    )

    weekly_digest = models.BooleanField(
        default=True,
        help_text=_('Receive weekly digest emails')
    )

    # Privacy Settings
    PROFILE_VISIBILITY_CHOICES = [
        ('public', _('Public')),
        ('private', _('Private')),
        ('connections', _('Connections Only')),
    ]

    profile_visibility = models.CharField(
        max_length=50,
        choices=PROFILE_VISIBILITY_CHOICES,
        default='public',
        help_text=_('Profile visibility')
    )

    show_progress = models.BooleanField(
        default=True,
        help_text=_('Show learning progress publicly')
    )

    # Learning Preferences
    LEARNING_STYLE_CHOICES = [
        ('visual', _('Visual')),
        ('auditory', _('Auditory')),
        ('reading', _('Reading/Writing')),
        ('kinesthetic', _('Kinesthetic')),
    ]

    preferred_learning_style = models.CharField(
        max_length=50,
        choices=LEARNING_STYLE_CHOICES,
        blank=True,
        null=True,
        help_text=_('Preferred learning style')
    )

    daily_learning_goal_minutes = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        help_text=_('Daily learning goal in minutes')
    )

    reminder_time = models.TimeField(
        null=True,
        blank=True,
        help_text=_('Preferred time for learning reminders')
    )

    class Meta:
        db_table = 'user_preferences'
        verbose_name = _('User Preferences')
        verbose_name_plural = _('User Preferences')

    def __str__(self):
        """String representation."""
        return f'Preferences for {self.user.username}'

    def __repr__(self):
        """Developer-friendly representation."""
        return f'<UserPreferences user={self.user.username}>'
