"""
User Service Serializers

Implements serializers for user authentication, profile management, and skill tracking
as specified in SRS Section 3.1.1 (FR-1 to FR-5) and Appendix B.

SRS References:
- FR-1: User Registration
- FR-2: User Login
- FR-3: Profile Management
- FR-4: User Preferences
- FR-5: Skill Tracking
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from datetime import date

from apps.users.models import User, Skill, UserSkill, UserPreferences
from apps.users.services import UserService, SkillService


# ============================================================================
# SKILL SERIALIZERS
# ============================================================================

class SkillSerializer(serializers.ModelSerializer):
    """
    Basic skill information serializer.

    SRS Reference: FR-5 (Skill Tracking)
    Used for: Listing available skills, displaying skill details
    """

    class Meta:
        model = Skill
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'category',
            'parent_skill',
            'is_active',
            'popularity_score',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'popularity_score']


class SkillListSerializer(serializers.ModelSerializer):
    """
    Minimal skill information for list views.
    Optimized for performance in nested relationships.
    """

    class Meta:
        model = Skill
        fields = ['id', 'name', 'category']


# ============================================================================
# USER SKILL SERIALIZERS
# ============================================================================

class UserSkillSerializer(serializers.ModelSerializer):
    """
    User skill with proficiency level.

    SRS Reference: FR-5 (Skill Tracking)
    Displays user's skills with proficiency and experience details.
    """
    skill = SkillListSerializer(read_only=True)

    class Meta:
        model = UserSkill
        fields = [
            'id',
            'skill',
            'skill_type',
            'proficiency_level',
            'years_of_experience',
            'source',
            'is_verified',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'source',
            'is_verified',
            'created_at',
            'updated_at',
        ]


class UserSkillCreateSerializer(serializers.Serializer):
    """
    Add skill to user profile.

    SRS Reference: FR-5 (Skill Tracking)
    Endpoint: POST /users/skills (SRS Appendix B)
    """
    skill_id = serializers.UUIDField(required=True)
    proficiency_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        required=True
    )
    years_of_experience = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
        max_value=99.99
    )
    skill_type = serializers.ChoiceField(
        choices=['hard', 'soft'],
        default='hard',
        required=False
    )

    def validate_skill_id(self, value):
        """Validate that skill exists and is active."""
        try:
            skill = Skill.objects.get(id=value, is_active=True, is_deleted=False)
        except Skill.DoesNotExist:
            raise serializers.ValidationError("Skill not found or inactive")
        return value

    def create(self, validated_data):
        """Add skill to user using SkillService."""
        user = self.context['request'].user
        skill_id = validated_data['skill_id']

        skill = Skill.objects.get(id=skill_id)

        user_skill = SkillService.add_user_skill(
            user=user,
            skill=skill,
            proficiency_level=validated_data['proficiency_level'],
            years_of_experience=validated_data.get('years_of_experience', 0)
        )

        return user_skill


class UserSkillUpdateSerializer(serializers.Serializer):
    """
    Update skill proficiency level.

    SRS Reference: FR-5 (System shall update skill levels after roadmap progress)
    """
    proficiency_level = serializers.ChoiceField(
        choices=['beginner', 'intermediate', 'advanced', 'expert'],
        required=True
    )
    years_of_experience = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=0,
        max_value=99.99
    )

    def update(self, instance, validated_data):
        """Update skill proficiency using SkillService."""
        user = self.context['request'].user

        updated_skill = SkillService.update_skill_proficiency(
            user=user,
            skill=instance.skill,
            proficiency_level=validated_data['proficiency_level'],
            years_of_experience=validated_data.get('years_of_experience')
        )

        return updated_skill


# ============================================================================
# USER PREFERENCES SERIALIZERS
# ============================================================================

class UserPreferencesSerializer(serializers.ModelSerializer):
    """
    User preferences and settings.

    SRS Reference: FR-4 (User Preferences)
    Stores: Preferred learning format, Target job role, Interests, Language preference
    """

    class Meta:
        model = UserPreferences
        fields = [
            'id',
            'email_notifications',
            'push_notifications',
            'weekly_digest',
            'profile_visibility',
            'show_progress',
            'preferred_learning_style',
            'daily_learning_goal_minutes',
            'reminder_time',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ============================================================================
# USER PROFILE SERIALIZERS
# ============================================================================

class UserSerializer(serializers.ModelSerializer):
    """
    Basic user information (public profile view).

    SRS Reference: FR-3 (Profile Management)
    Endpoint: GET /users/me (SRS Appendix B)
    """
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'date_of_birth',
            'age',
            'phone_number',
            'is_premium',
            'onboarding_completed',
            'preferred_language',
            'timezone',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'age',
            'is_premium',
            'created_at',
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Complete user profile with nested relationships.

    SRS Reference: FR-3 (Profile Management)
    Endpoint: GET /users/me (SRS Appendix B)
    Includes: User skills with proficiency levels
    """
    user_skills = UserSkillSerializer(many=True, read_only=True)
    preferences = UserPreferencesSerializer(read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'full_name',
            'date_of_birth',
            'age',
            'phone_number',
            'is_premium',
            'account_status',
            'onboarding_completed',
            'onboarding_step',
            'preferred_language',
            'timezone',
            'user_skills',
            'preferences',
            'last_login_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'age',
            'is_premium',
            'account_status',
            'last_login_at',
            'created_at',
            'updated_at',
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Update user profile fields.

    SRS Reference: FR-3 (Edit personal information, Set career goals, Add experience summary)
    Endpoint: PUT /users/me (SRS Appendix B)
    """

    class Meta:
        model = User
        fields = [
            'username',
            'full_name',
            'date_of_birth',
            'phone_number',
            'preferred_language',
            'timezone',
        ]

    def validate_date_of_birth(self, value):
        """
        Validate age is at least 13 years.

        SRS Requirement: User must be 13+ years old
        """
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

        if age < 13:
            raise serializers.ValidationError(
                "You must be at least 13 years old to use this platform."
            )

        return value

    def update(self, instance, validated_data):
        """Update user profile using UserService."""
        updated_user = UserService.update_user_profile(
            user=instance,
            **validated_data
        )
        return updated_user


# ============================================================================
# AUTHENTICATION SERIALIZERS
# ============================================================================

class UserRegistrationSerializer(serializers.Serializer):
    """
    User registration serializer.

    SRS Reference: FR-1 (User Registration)
    Note: SRS specifies Auth0 authentication, but for MVP we'll use Django auth
          with the understanding that Auth0 integration will replace this later.

    The system shall store: auth0_id (will be auto-generated for now), email, minimal profile data
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    username = serializers.CharField(required=True, min_length=3, max_length=100)
    full_name = serializers.CharField(required=True, max_length=255)
    date_of_birth = serializers.DateField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    preferred_language = serializers.ChoiceField(
        choices=['en', 'ar'],
        default='en',
        required=False
    )

    def validate_email(self, value):
        """Validate email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()

    def validate_username(self, value):
        """Validate username is unique."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )
        return value

    def validate_date_of_birth(self, value):
        """
        Validate age is at least 13 years.

        SRS Requirement: Users must be 13+ years old
        """
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

        if age < 13:
            raise serializers.ValidationError(
                "You must be at least 13 years old to register."
            )

        return value

    def validate(self, attrs):
        """Validate passwords match and meet requirements."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password_confirm": "Passwords do not match."
            })

        # Validate password strength using Django's validators
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({
                "password": list(e.messages)
            })

        return attrs

    def create(self, validated_data):
        """
        Create new user account.

        SRS Reference: FR-1 (System shall store user's auth0_id, email, and minimal profile data)
        Note: auth0_id will be auto-generated as username for now until Auth0 is integrated
        """
        validated_data.pop('password_confirm')

        user = UserService.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            username=validated_data['username'],
            full_name=validated_data['full_name'],
            date_of_birth=validated_data['date_of_birth'],
            phone_number=validated_data.get('phone_number', ''),
            preferred_language=validated_data.get('preferred_language', 'en'),
            auth0_id=f"temp_{validated_data['username']}",  # Temporary until Auth0
        )

        return user

    def to_representation(self, instance):
        """Return user profile without password."""
        return UserSerializer(instance).data


class UserLoginSerializer(serializers.Serializer):
    """
    User login serializer.

    SRS Reference: FR-2 (User Login)
    SRS Endpoint: POST /auth/login (Appendix B)

    Note: SRS specifies Auth0 authentication returning JWT.
          For MVP, using Django authentication until Auth0 is configured.

    Returns: JWT access token (as per SRS FR-2)
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Authenticate user credentials."""
        email = attrs.get('email', '').lower()
        password = attrs.get('password')

        # Try to get user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "non_field_errors": "Invalid email or password."
            })

        # Authenticate
        user = authenticate(
            username=email,  # Django uses USERNAME_FIELD which is email
            password=password
        )

        if not user:
            raise serializers.ValidationError({
                "non_field_errors": "Invalid email or password."
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "non_field_errors": "This account has been deactivated."
            })

        attrs['user'] = user
        return attrs


# ============================================================================
# SKILL SEARCH SERIALIZERS
# ============================================================================

class SkillSearchSerializer(serializers.Serializer):
    """
    Search skills by name.

    SRS Reference: FR-5 (Skill Tracking)
    """
    query = serializers.CharField(required=True, min_length=2)
    category = serializers.ChoiceField(
        choices=[
            'technical',
            'soft',
            'business',
            'design',
            'data',
            'marketing',
            'other',
        ],
        required=False,
        allow_null=True
    )
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)
