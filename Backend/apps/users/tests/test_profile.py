"""
User Profile API Tests

Tests for user profile management endpoints.
SRS References: FR-3 (Profile Management), FR-4 (User Preferences)
"""

import pytest
from datetime import date, timedelta
from rest_framework import status


@pytest.mark.django_db
class TestUserProfile:
    """Tests for GET/PUT /api/v1/users/me/"""

    def test_get_profile_authenticated(self, authenticated_client, user):
        """Test getting profile for authenticated user."""
        url = '/api/v1/users/me/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email
        assert response.data['username'] == user.username
        assert response.data['full_name'] == user.full_name
        assert 'user_skills' in response.data
        assert 'preferences' in response.data

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile without authentication fails."""
        url = '/api/v1/users/me/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_full_name(self, authenticated_client, user):
        """Test updating profile full name."""
        url = '/api/v1/users/me/'
        response = authenticated_client.patch(url, {
            'full_name': 'Updated Name',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['full_name'] == 'Updated Name'

    def test_update_profile_username(self, authenticated_client, user):
        """Test updating profile username."""
        url = '/api/v1/users/me/'
        response = authenticated_client.patch(url, {
            'username': 'newusername',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'newusername'

    def test_update_profile_language(self, authenticated_client, user):
        """Test updating preferred language."""
        url = '/api/v1/users/me/'
        response = authenticated_client.patch(url, {
            'preferred_language': 'ar',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['preferred_language'] == 'ar'

    def test_update_profile_date_of_birth(self, authenticated_client, user):
        """Test updating date of birth."""
        new_dob = date.today() - timedelta(days=365 * 30)
        url = '/api/v1/users/me/'
        response = authenticated_client.patch(url, {
            'date_of_birth': str(new_dob),
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['date_of_birth'] == str(new_dob)

    def test_update_profile_underage_dob(self, authenticated_client, user):
        """Test updating DOB to underage fails."""
        new_dob = date.today() - timedelta(days=365 * 10)  # 10 years old
        url = '/api/v1/users/me/'
        response = authenticated_client.patch(url, {
            'date_of_birth': str(new_dob),
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_profile_email_readonly(self, authenticated_client, user):
        """Test that email cannot be updated (read-only)."""
        url = '/api/v1/users/me/'
        original_email = user.email
        response = authenticated_client.patch(url, {
            'email': 'newemail@example.com',
        }, format='json')

        # Should succeed but email should not change
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == original_email

    def test_update_profile_multiple_fields(self, authenticated_client, user):
        """Test updating multiple profile fields at once."""
        url = '/api/v1/users/me/'
        response = authenticated_client.put(url, {
            'username': 'brandnewname',
            'full_name': 'Brand New Name',
            'phone_number': '+201111111111',
            'preferred_language': 'ar',
            'timezone': 'Africa/Cairo',
            'date_of_birth': str(date.today() - timedelta(days=365 * 28)),
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'brandnewname'
        assert response.data['full_name'] == 'Brand New Name'
        assert response.data['phone_number'] == '+201111111111'


@pytest.mark.django_db
class TestUserPreferences:
    """Tests for GET/PUT /api/v1/users/me/preferences/"""

    def test_get_preferences(self, authenticated_client, user_preferences):
        """Test getting user preferences."""
        url = '/api/v1/users/me/preferences/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'email_notifications' in response.data
        assert 'push_notifications' in response.data
        assert 'preferred_learning_style' in response.data

    def test_get_preferences_creates_default(self, authenticated_client, user):
        """Test getting preferences creates default if not exists."""
        url = '/api/v1/users/me/preferences/'
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Default values should be present
        assert 'id' in response.data

    def test_update_preferences_notifications(self, authenticated_client, user_preferences):
        """Test updating notification preferences."""
        url = '/api/v1/users/me/preferences/'
        response = authenticated_client.patch(url, {
            'email_notifications': False,
            'push_notifications': False,
            'weekly_digest': True,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email_notifications'] is False
        assert response.data['push_notifications'] is False
        assert response.data['weekly_digest'] is True

    def test_update_preferences_learning_style(self, authenticated_client, user_preferences):
        """Test updating learning preferences."""
        url = '/api/v1/users/me/preferences/'
        # Valid choices: visual, auditory, reading, kinesthetic
        response = authenticated_client.patch(url, {
            'preferred_learning_style': 'visual',
            'daily_learning_goal_minutes': 60,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['preferred_learning_style'] == 'visual'
        assert response.data['daily_learning_goal_minutes'] == 60

    def test_update_preferences_privacy(self, authenticated_client, user_preferences):
        """Test updating privacy preferences."""
        url = '/api/v1/users/me/preferences/'
        response = authenticated_client.patch(url, {
            'profile_visibility': 'private',
            'show_progress': False,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['profile_visibility'] == 'private'
        assert response.data['show_progress'] is False

    def test_preferences_unauthenticated(self, api_client):
        """Test preferences endpoint requires authentication."""
        url = '/api/v1/users/me/preferences/'
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
