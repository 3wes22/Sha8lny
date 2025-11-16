"""
Custom user manager for Sha8alny User model.

Provides methods for creating users and superusers with proper validation.
"""

from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Custom manager for User model.

    Handles user creation with auth0_id as the primary identifier
    instead of username.
    """

    def create_user(
        self,
        email,
        auth0_id,
        username,
        full_name,
        date_of_birth,
        password=None,
        **extra_fields
    ):
        """
        Create and save a regular user.

        Args:
            email: User's email address
            auth0_id: Auth0 user identifier
            username: Unique username
            full_name: User's full name
            date_of_birth: User's date of birth
            password: User's password (optional, Auth0 handles auth)
            **extra_fields: Additional fields

        Returns:
            User: Created user instance

        Raises:
            ValueError: If required fields are missing
        """
        if not email:
            raise ValueError(_('Email address is required'))
        if not auth0_id:
            raise ValueError(_('Auth0 ID is required'))
        if not username:
            raise ValueError(_('Username is required'))
        if not full_name:
            raise ValueError(_('Full name is required'))
        if not date_of_birth:
            raise ValueError(_('Date of birth is required'))

        # Normalize email
        email = self.normalize_email(email)

        # Set default values
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        # Create user instance
        user = self.model(
            email=email,
            auth0_id=auth0_id,
            username=username,
            full_name=full_name,
            date_of_birth=date_of_birth,
            **extra_fields
        )

        # Set password (even though Auth0 handles authentication)
        if password:
            user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email,
        username,
        full_name,
        date_of_birth,
        password=None,
        **extra_fields
    ):
        """
        Create and save a superuser.

        Args:
            email: User's email address
            username: Unique username
            full_name: User's full name
            date_of_birth: User's date of birth
            password: User's password
            **extra_fields: Additional fields

        Returns:
            User: Created superuser instance

        Raises:
            ValueError: If superuser flags are not set correctly
        """
        # Set superuser flags
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True'))

        # Generate auth0_id for superuser (local development)
        # In production, superusers would also go through Auth0
        auth0_id = extra_fields.pop('auth0_id', f'local|superuser_{username}')

        return self.create_user(
            email=email,
            auth0_id=auth0_id,
            username=username,
            full_name=full_name,
            date_of_birth=date_of_birth,
            password=password,
            **extra_fields
        )
