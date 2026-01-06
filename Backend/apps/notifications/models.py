"""
Notifications Module Models

Implements notification system including:
- Notification: User notifications with polymorphic entity references
- NotificationPreference: User notification preferences and settings
"""

from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel
from apps.users.models import User


class NotificationManager(models.Manager):
    """Custom manager for Notification model with optimized queries"""

    def for_user(self, user):
        """Get notifications for a specific user"""
        return self.filter(user=user, is_deleted=False)

    def unread(self):
        """Get unread notifications"""
        return self.filter(is_read=False, is_deleted=False)

    def read(self):
        """Get read notifications"""
        return self.filter(is_read=True, is_deleted=False)

    def urgent(self):
        """Get urgent notifications"""
        return self.filter(priority='urgent', is_deleted=False)

    def by_type(self, notification_type):
        """Get notifications by type"""
        return self.filter(notification_type=notification_type, is_deleted=False)

    def recent(self, days=7):
        """Get recent notifications from last N days"""
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date, is_deleted=False)


class Notification(BaseModel):
    """
    User notification with polymorphic entity references.

    Supports notifications for various events (milestone achieved, course completed,
    job match, etc.) with flexible entity references and action URLs.
    """

    # Notification Type Choices
    NOTIFICATION_TYPES = [
        ('milestone_achieved', 'Milestone Achieved'),
        ('course_completed', 'Course Completed'),
        ('job_match', 'Job Match Found'),
        ('roadmap_generated', 'Roadmap Generated'),
        ('assessment_complete', 'Assessment Complete'),
        ('roadmap_updated', 'Roadmap Updated'),
        ('new_course_added', 'New Course Added'),
        ('skill_recommendation', 'Skill Recommendation'),
        ('system_announcement', 'System Announcement'),
        ('achievement_unlocked', 'Achievement Unlocked'),
    ]

    # Delivery Status Choices
    DELIVERY_STATUS = [
        ('sent', 'Sent'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]

    # Priority Level Choices
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User receiving this notification"
    )

    # Notification Details
    notification_type = models.CharField(
        max_length=100,
        choices=NOTIFICATION_TYPES,
        db_index=True,
        help_text="Type of notification"
    )

    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )

    message = models.TextField(
        help_text="Notification message content"
    )

    # Polymorphic Entity Reference
    related_entity_type = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Type of related entity (roadmap, course, job, milestone, etc.)"
    )

    related_entity_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="ID of related entity"
    )

    # Action/Link
    action_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text="URL to redirect user when clicking notification"
    )

    action_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text for action button/link (e.g., 'View Roadmap', 'See Details')"
    )

    # Notification Status
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether notification has been read"
    )

    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when notification was read"
    )

    # Delivery
    delivery_status = models.CharField(
        max_length=50,
        choices=DELIVERY_STATUS,
        default='sent',
        help_text="Delivery status of notification"
    )

    # Priority
    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_LEVELS,
        default='normal',
        db_index=True,
        help_text="Notification priority level"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data for notification"
    )

    # Custom manager
    objects = NotificationManager()

    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='idx_notif_user'),
            models.Index(fields=['notification_type'], name='idx_notif_type'),
            models.Index(fields=['user', 'is_read'], name='idx_notif_unread'),
            models.Index(fields=['-created_at'], name='idx_notif_created'),
            models.Index(fields=['priority'], name='idx_notif_priority'),
            models.Index(fields=['related_entity_type', 'related_entity_id'], name='idx_notif_entity'),
        ]

    def __str__(self):
        read_status = "Read" if self.is_read else "Unread"
        return f"{self.user.email} - {self.title} ({read_status})"

    @property
    def is_unread(self):
        """Check if notification is unread"""
        return not self.is_read

    @property
    def entity_display(self):
        """Format entity type and ID for display"""
        if not self.related_entity_type:
            return "No related entity"
        entity_id = str(self.related_entity_id)[:8] if self.related_entity_id else "N/A"
        return f"{self.related_entity_type}: {entity_id}"

    @property
    def priority_icon(self):
        """Return emoji icon based on priority"""
        icons = {
            'low': '🔵',
            'normal': '🟢',
            'high': '🟠',
            'urgent': '🔴',
        }
        return icons.get(self.priority, '⚪')

    @property
    def type_icon(self):
        """Return emoji icon based on notification type"""
        icons = {
            'milestone_achieved': '🏆',
            'course_completed': '📚',
            'job_match': '💼',
            'roadmap_generated': '🗺️',
            'assessment_complete': '✅',
            'roadmap_updated': '🔄',
            'new_course_added': '➕',
            'skill_recommendation': '💡',
            'system_announcement': '📢',
            'achievement_unlocked': '🎖️',
        }
        return icons.get(self.notification_type, '🔔')

    def mark_as_read(self):
        """Mark notification as read and set timestamp"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])

            # Emit signal for listeners (WebSockets, analytics, etc.)
            from .signals import notification_read
            notification_read.send(sender=self.__class__, instance=self)

    def mark_as_unread(self):
        """Mark notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])


class NotificationPreference(BaseModel):
    """
    User notification preferences and settings.

    Controls which notification channels are enabled, notification type
    preferences, digest frequency, and quiet hours.
    """

    # Digest Frequency Choices
    DIGEST_FREQUENCY = [
        ('never', 'Never'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        help_text="User who owns these preferences"
    )

    # Channel Preferences
    in_app_enabled = models.BooleanField(
        default=True,
        help_text="Enable in-app notifications"
    )

    email_enabled = models.BooleanField(
        default=True,
        help_text="Enable email notifications"
    )

    push_enabled = models.BooleanField(
        default=False,
        help_text="Enable push notifications (future feature)"
    )

    # Type-Specific Preferences (JSONB for flexibility)
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-type notification preferences (e.g., {'milestone_achieved': true, 'job_match': false})"
    )

    # Digest Settings
    digest_frequency = models.CharField(
        max_length=50,
        choices=DIGEST_FREQUENCY,
        default='weekly',
        help_text="Frequency for notification digest emails"
    )

    # Quiet Hours (Don't send notifications during these times)
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Start of quiet hours (24-hour format, e.g., 22:00)"
    )

    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="End of quiet hours (24-hour format, e.g., 08:00)"
    )

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"
        ordering = ['user']

    def __str__(self):
        return f"{self.user.email} - Notification Preferences"

    @property
    def enabled_channels(self):
        """Get list of enabled notification channels"""
        channels = []
        if self.in_app_enabled:
            channels.append('In-App')
        if self.email_enabled:
            channels.append('Email')
        if self.push_enabled:
            channels.append('Push')
        return channels if channels else ['None']

    @property
    def enabled_channels_display(self):
        """Display enabled channels as comma-separated string"""
        return ', '.join(self.enabled_channels)

    def is_type_enabled(self, notification_type):
        """
        Check if a specific notification type is enabled.

        Args:
            notification_type: Type of notification to check

        Returns:
            bool: True if enabled (or not explicitly disabled), False otherwise
        """
        if not self.preferences:
            return True  # Default to enabled if no preferences set

        # If preferences exist, check specific type (default to True if not specified)
        return self.preferences.get(notification_type, True)

    def is_in_quiet_hours(self, check_time=None):
        """
        Check if current time (or provided time) is within quiet hours.

        Args:
            check_time: Optional datetime.time object to check (defaults to now)

        Returns:
            bool: True if in quiet hours, False otherwise
        """
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False  # No quiet hours set

        if check_time is None:
            check_time = timezone.now().time()

        start = self.quiet_hours_start
        end = self.quiet_hours_end

        # Handle overnight quiet hours (e.g., 22:00 to 08:00)
        if start < end:
            # Normal range (e.g., 08:00 to 22:00)
            return start <= check_time <= end
        else:
            # Overnight range (e.g., 22:00 to 08:00)
            return check_time >= start or check_time <= end

    def set_type_preference(self, notification_type, enabled):
        """
        Set preference for a specific notification type.

        Args:
            notification_type: Type of notification
            enabled: Whether to enable (True) or disable (False)
        """
        if not self.preferences:
            self.preferences = {}

        self.preferences[notification_type] = enabled
        self.save(update_fields=['preferences', 'updated_at'])

    @property
    def has_quiet_hours(self):
        """Check if quiet hours are configured"""
        return bool(self.quiet_hours_start and self.quiet_hours_end)

    @property
    def quiet_hours_display(self):
        """Display quiet hours in readable format"""
        if not self.has_quiet_hours:
            return "Not set"

        start = self.quiet_hours_start.strftime('%H:%M')
        end = self.quiet_hours_end.strftime('%H:%M')
        return f"{start} - {end}"
