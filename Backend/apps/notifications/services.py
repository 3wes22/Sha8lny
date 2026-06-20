"""
Notifications Service Layer

Handles notification creation, delivery, and preference management.
"""

from typing import Optional, List, Dict, Any
from django.utils import timezone
from django.db import transaction
from .models import Notification, NotificationPreference
from .signals import notification_created
from apps.users.models import User


class NotificationService:
    """Service for notification management"""

    @staticmethod
    @transaction.atomic
    def create_notification(
        user: User,
        notification_type: str,
        title: str,
        message: str,
        priority: str = 'normal',
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Notification:
        """
        Create a new notification for a user.

        Args:
            user: User to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Priority level (low, normal, high, urgent)
            related_entity_type: Type of related entity
            related_entity_id: ID of related entity
            action_url: URL for action button
            action_text: Text for action button
            metadata: Additional metadata

        Returns:
            Notification: Created notification
        """
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=priority,
            related_entity_type=related_entity_type or '',
            related_entity_id=related_entity_id,
            action_url=action_url or '',
            action_text=action_text or '',
            metadata=metadata or {},
            delivery_status='sent'
        )

        # Emit signal for potential listeners (email workers, WebSockets, etc.)
        notification_created.send(sender=Notification, instance=notification)

        return notification

    @staticmethod
    def get_user_notifications(
        user: User,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user: User instance
            unread_only: Return only unread notifications
            limit: Maximum number of notifications to return

        Returns:
            List[Notification]: List of notifications
        """
        queryset = Notification.objects.for_user(user)

        if unread_only:
            queryset = queryset.filter(is_read=False)

        return list(queryset[:limit])

    @staticmethod
    def get_unread_count(user: User) -> int:
        """Get count of unread notifications for user"""
        return Notification.objects.for_user(user).filter(is_read=False).count()

    @staticmethod
    def mark_as_read(notification_id: str, user: User) -> Optional[Notification]:
        """Mark a notification as read for the owning user."""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=user,
                is_deleted=False,
            )
            notification.mark_as_read()
            return notification
        except Notification.DoesNotExist:
            return None

    @staticmethod
    def mark_all_as_read(user: User) -> int:
        """Mark all notifications as read for a user"""
        unread = Notification.objects.for_user(user).unread()
        count = 0

        for notification in unread:
            notification.mark_as_read()
            count += 1

        return count

    @staticmethod
    def delete_notification(notification_id: str) -> bool:
        """Soft delete a notification"""
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.is_deleted = True
            notification.save(update_fields=['is_deleted', 'updated_at'])
            return True
        except Notification.DoesNotExist:
            return False

    @staticmethod
    def get_urgent_notifications(user: User) -> List[Notification]:
        """Get urgent notifications for user"""
        return list(Notification.objects.for_user(user).filter(priority='urgent'))

    @staticmethod
    def get_notifications_by_type(
        user: User,
        notification_type: str
    ) -> List[Notification]:
        """Get notifications of a specific type"""
        return list(Notification.objects.for_user(user).filter(notification_type=notification_type))


class NotificationPreferenceService:
    """Service for notification preference management"""

    @staticmethod
    def get_or_create_preferences(user: User) -> NotificationPreference:
        """Get or create notification preferences for user"""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'in_app_enabled': True,
                'email_enabled': True,
                'push_enabled': False,
                'digest_frequency': 'weekly'
            }
        )
        return preferences

    @staticmethod
    def update_preferences(
        user: User,
        **fields
    ) -> NotificationPreference:
        """
        Update notification preferences.

        Args:
            user: User instance
            **fields: Fields to update (in_app_enabled, email_enabled, etc.)

        Returns:
            NotificationPreference: Updated preferences
        """
        preferences = NotificationPreferenceService.get_or_create_preferences(user)

        allowed_fields = [
            'in_app_enabled', 'email_enabled', 'push_enabled',
            'digest_frequency', 'quiet_hours_start', 'quiet_hours_end'
        ]

        for field, value in fields.items():
            if field in allowed_fields:
                setattr(preferences, field, value)

        preferences.save()
        return preferences

    @staticmethod
    def set_type_preference(
        user: User,
        notification_type: str,
        enabled: bool
    ) -> NotificationPreference:
        """Enable or disable specific notification type"""
        preferences = NotificationPreferenceService.get_or_create_preferences(user)
        preferences.set_type_preference(notification_type, enabled)
        return preferences

    @staticmethod
    def is_notification_allowed(
        user: User,
        notification_type: str,
        channel: str = 'in_app'
    ) -> bool:
        """
        Check if notification is allowed based on user preferences.

        Args:
            user: User instance
            notification_type: Type of notification
            channel: Notification channel (in_app, email, push)

        Returns:
            bool: True if notification is allowed
        """
        try:
            preferences = NotificationPreference.objects.get(user=user)
        except NotificationPreference.DoesNotExist:
            return True  # Default to allowing notifications

        # Check channel is enabled
        if channel == 'in_app' and not preferences.in_app_enabled:
            return False
        elif channel == 'email' and not preferences.email_enabled:
            return False
        elif channel == 'push' and not preferences.push_enabled:
            return False

        # Check type is enabled
        if not preferences.is_type_enabled(notification_type):
            return False

        # Check quiet hours
        if channel in ['email', 'push'] and preferences.is_in_quiet_hours():
            return False

        return True

    @staticmethod
    def set_quiet_hours(
        user: User,
        start_time: str,
        end_time: str
    ) -> NotificationPreference:
        """
        Set quiet hours for user.

        Args:
            user: User instance
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format

        Returns:
            NotificationPreference: Updated preferences
        """
        from datetime import datetime

        preferences = NotificationPreferenceService.get_or_create_preferences(user)

        preferences.quiet_hours_start = datetime.strptime(start_time, '%H:%M').time()
        preferences.quiet_hours_end = datetime.strptime(end_time, '%H:%M').time()
        preferences.save()

        return preferences
