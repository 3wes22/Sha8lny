"""
Authentication API Tests

Tests for user registration, login, and token refresh endpoints.
SRS References: FR-1 (User Registration), FR-2 (User Login)
"""

import pytest
from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestUserRegistration:
    """Tests for POST /api/v1/users/auth/register/"""

    def test_register_success(self, api_client, user_data):
        """Test successful user registration."""
        url = '/api/v1/users/auth/register/'
        response = api_client.post(url, user_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['email'] == user_data['email'].lower()
        assert response.data['user']['username'] == user_data['username']

    def test_register_duplicate_email(self, api_client, user, user_data):
        """Test registration with existing email fails."""
        url = '/api/v1/users/auth/register/'
        user_data['email'] = user.email  # Use existing user's email
        user_data['username'] = 'newusername'

        response = api_client.post(url, user_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # API uses custom exception handler with 'details' wrapper
        details = response.data.get('details', response.data)
        assert 'email' in details

    def test_register_duplicate_username(self, api_client, user, user_data):
        """Test registration with existing username fails."""
        url = '/api/v1/users/auth/register/'
        user_data['email'] = 'newemail@example.com'
        user_data['username'] = user.username  # Use existing user's username

        response = api_client.post(url, user_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        details = response.data.get('details', response.data)
        assert 'username' in details

    def test_register_password_mismatch(self, api_client, user_data):
        """Test registration with mismatched passwords fails."""
        url = '/api/v1/users/auth/register/'
        user_data['password_confirm'] = 'DifferentPass123!'

        response = api_client.post(url, user_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        details = response.data.get('details', response.data)
        assert 'password_confirm' in details

    def test_register_weak_password(self, api_client, user_data):
        """Test registration with weak password fails."""
        url = '/api/v1/users/auth/register/'
        user_data['password'] = '123'
        user_data['password_confirm'] = '123'

        response = api_client.post(url, user_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        details = response.data.get('details', response.data)
        assert 'password' in details

    def test_register_underage(self, api_client, user_data):
        """Test registration with age under 13 fails."""
        url = '/api/v1/users/auth/register/'
        user_data['date_of_birth'] = str(date.today() - timedelta(days=365 * 10))  # 10 years old

        response = api_client.post(url, user_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        details = response.data.get('details', response.data)
        assert 'date_of_birth' in details

    def test_register_missing_required_fields(self, api_client):
        """Test registration with missing required fields fails."""
        url = '/api/v1/users/auth/register/'
        incomplete_data = {
            'email': 'test@example.com',
            # Missing password, username, full_name, date_of_birth
        }

        response = api_client.post(url, incomplete_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUserLogin:
    """Tests for POST /api/v1/users/auth/login/"""

    def test_login_success(self, api_client, user):
        """Test successful login with valid credentials."""
        url = '/api/v1/users/auth/login/'
        response = api_client.post(url, {
            'email': user.email,
            'password': 'SecurePass123!',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
        assert response.data['user']['email'] == user.email

    def test_login_invalid_email(self, api_client):
        """Test login with non-existent email fails."""
        url = '/api/v1/users/auth/login/'
        response = api_client.post(url, {
            'email': 'nonexistent@example.com',
            'password': 'SecurePass123!',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        details = response.data.get('details', response.data)
        assert 'non_field_errors' in details

    def test_login_invalid_password(self, api_client, user):
        """Test login with wrong password fails."""
        url = '/api/v1/users/auth/login/'
        response = api_client.post(url, {
            'email': user.email,
            'password': 'WrongPassword123!',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        details = response.data.get('details', response.data)
        assert 'non_field_errors' in details

    def test_login_inactive_user(self, api_client, user):
        """Test login with inactive user fails."""
        user.is_active = False
        user.save()

        url = '/api/v1/users/auth/login/'
        response = api_client.post(url, {
            'email': user.email,
            'password': 'SecurePass123!',
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_case_insensitive_email(self, api_client, user):
        """Test login with different email case works."""
        url = '/api/v1/users/auth/login/'
        response = api_client.post(url, {
            'email': user.email.upper(),
            'password': 'SecurePass123!',
        }, format='json')

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests for POST /api/v1/users/auth/refresh/"""

    def test_refresh_token_success(self, api_client, auth_tokens):
        """Test successful token refresh."""
        url = '/api/v1/users/auth/refresh/'
        response = api_client.post(url, {
            'refresh': auth_tokens['refresh'],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    def test_refresh_token_invalid(self, api_client):
        """Test refresh with invalid token fails."""
        url = '/api/v1/users/auth/refresh/'
        response = api_client.post(url, {
            'refresh': 'invalid-token',
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserLogout:
    """Tests for POST /api/v1/users/auth/logout/"""

    def test_logout_success(self, authenticated_client, auth_tokens):
        """Test successful logout."""
        url = '/api/v1/users/auth/logout/'
        response = authenticated_client.post(url, {
            'refresh': auth_tokens['refresh'],
        }, format='json')

        assert response.status_code == status.HTTP_200_OK

    def test_logout_without_auth(self, api_client, auth_tokens):
        """Test logout without authentication fails."""
        url = '/api/v1/users/auth/logout/'
        response = api_client.post(url, {
            'refresh': auth_tokens['refresh'],
        }, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
