"""
Pytest configuration and fixtures for Sha8lny backend tests.

This file is automatically loaded by pytest and provides shared fixtures
for all test modules.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.fixture
def api_client():
    """Return a DRF API test client."""
    return APIClient()


@pytest.fixture
def user_data():
    """Return valid user registration data."""
    return {
        'email': 'testuser@example.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!',
        'username': 'testuser',
        'full_name': 'Test User',
        'date_of_birth': str(date.today() - timedelta(days=365 * 25)),  # 25 years old
        'phone_number': '+201234567890',
        'preferred_language': 'en',
    }


@pytest.fixture
def user(db):
    """Create and return a test user."""
    from apps.users.models import User

    user = User.objects.create_user(
        email='testuser@example.com',
        password='SecurePass123!',
        username='testuser',
        full_name='Test User',
        date_of_birth=date.today() - timedelta(days=365 * 25),
        auth0_id='temp_testuser',
    )
    return user


@pytest.fixture
def another_user(db):
    """Create and return another test user for multi-user tests."""
    from apps.users.models import User

    user = User.objects.create_user(
        email='another@example.com',
        password='SecurePass123!',
        username='anotheruser',
        full_name='Another User',
        date_of_birth=date.today() - timedelta(days=365 * 30),
        auth0_id='temp_anotheruser',
    )
    return user


@pytest.fixture
def auth_tokens(user):
    """Generate JWT tokens for the test user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@pytest.fixture
def authenticated_client(api_client, user, auth_tokens):
    """Return an authenticated API client."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access']}")
    return api_client


@pytest.fixture
def skill(db):
    """Create and return a test skill."""
    from apps.users.models import Skill

    skill = Skill.objects.create(
        name='Python',
        slug='python',
        description='Python programming language',
        category='technical',
        is_active=True,
    )
    return skill


@pytest.fixture
def skill_set(db):
    """Create and return a set of test skills."""
    from apps.users.models import Skill
    import uuid

    skills = []
    skill_data = [
        ('Python', 'technical'),
        ('JavaScript', 'technical'),
        ('Communication', 'soft'),
        ('Project Management', 'business'),
        ('Data Analysis', 'data'),
    ]

    for name, category in skill_data:
        # Use unique slug with uuid suffix to avoid conflicts
        unique_slug = f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}"
        skill, _ = Skill.objects.get_or_create(
            name=name,
            defaults={
                'slug': unique_slug,
                'description': f'{name} skill',
                'category': category,
                'is_active': True,
            }
        )
        skills.append(skill)

    return skills


@pytest.fixture
def user_skill(db, user, skill):
    """Create and return a user skill."""
    from apps.users.models import UserSkill

    user_skill = UserSkill.objects.create(
        user=user,
        skill=skill,
        proficiency_level='intermediate',
        years_of_experience=Decimal('2.5'),
        skill_type='hard',
        source='manual',
    )
    return user_skill


@pytest.fixture
def user_preferences(db, user):
    """Create and return user preferences."""
    from apps.users.models import UserPreferences

    preferences, _ = UserPreferences.objects.get_or_create(user=user)
    return preferences
