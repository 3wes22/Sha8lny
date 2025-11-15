"""
Base models and mixins for Sha8alny platform.

Provides common functionality for all models including:
- UUID primary keys
- Soft delete functionality
- Audit fields (created_at, updated_at)
- Common managers
"""

import uuid
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """
    Manager that automatically filters out soft-deleted objects.

    Usage:
        objects = SoftDeleteManager()  # Only returns non-deleted objects
        all_objects = models.Manager()  # Returns all objects including deleted
    """

    def get_queryset(self):
        """Return only non-deleted objects."""
        return super().get_queryset().filter(is_deleted=False)


class TimeStampedModel(models.Model):
    """
    Abstract base class providing automatic timestamps.

    Adds created_at and updated_at fields that are automatically managed.
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """
    Abstract base class providing soft delete functionality.

    Instead of actually deleting records, sets is_deleted flag to True
    and records when deletion occurred.
    """

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Default manager returns only non-deleted objects
    objects = SoftDeleteManager()
    # all_objects manager returns all objects including deleted
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        """
        Soft delete the object by setting is_deleted=True.

        Args:
            using: Database alias to use
            keep_parents: Whether to keep parent objects
            hard: If True, perform actual delete (use with caution)
        """
        if hard:
            # Perform actual hard delete
            super().delete(using=using, keep_parents=keep_parents)
        else:
            # Soft delete
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(using=using)

    def restore(self):
        """Restore a soft-deleted object."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class UUIDModel(models.Model):
    """
    Abstract base class providing UUID primary key.

    All models should use UUID for distributed system readiness.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel):
    """
    Base model combining UUID, timestamps, and soft delete.

    All application models should inherit from this base class.

    Provides:
    - UUID primary key (id)
    - Automatic timestamps (created_at, updated_at)
    - Soft delete functionality (is_deleted, deleted_at)
    - Proper managers (objects, all_objects)
    """

    class Meta:
        abstract = True

    def __str__(self):
        """Default string representation using ID."""
        return f"{self.__class__.__name__}({self.id})"

    def __repr__(self):
        """Developer-friendly representation."""
        return f"<{self.__class__.__name__} id={self.id}>"
