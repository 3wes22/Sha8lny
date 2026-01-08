"""
Notifications Service Serializers

Implements notification delivery and preference management serializers.

SRS Reference: Not explicitly in SRS, but implied by system requirements
for user engagement and communication.
"""

from rest_framework import serializers
from django.utils import timezone

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.services import NotificationService, NotificationPreferenceService


# ============================================================================
# NOTIFICATION SERIALIZERS
# ============================================================================

class NotificationSerializer(serializers.ModelSerializer):
    """
    Notification display serializer.

    Used for listing and retrieving user notifications.
    """
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'priority',
            'is_read',
            'read_at',
            'related_entity_type',
            'related_entity_id',
            'action_url',
            'action_text',
            'delivery_status',
            'metadata',
            'created_at',
            'time_ago',
        ]
        read_only_fields = [
            'id',
            'delivery_status',
            'created_at',
            'time_ago',
        ]

    def get_time_ago(self, obj):
        """Calculate human-readable time since notification was created."""
        now = timezone.now()
        diff = now - obj.created_at

        if diff.days > 365:
            return f"{diff.days // 365} year{'s' if diff.days // 365 > 1 else ''} ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month{'s' if diff.days // 30 > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour{'s' if diff.seconds // 3600 > 1 else ''} ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute{'s' if diff.seconds // 60 > 1 else ''} ago"
        else:
            return "Just now"


class NotificationListSerializer(serializers.ModelSerializer):
    """
    Minimal notification serializer for list views.
    Optimized for performance.
    """

    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'title',
            'message',
            'priority',
            'is_read',
            'action_url',
            'created_at',
        ]


class NotificationCreateSerializer(serializers.Serializer):
    """
    Create notification serializer (admin/system use).

    Used by system to create notifications for users.
    """
    user_id = serializers.UUIDField(required=True)
    notification_type = serializers.CharField(required=True, max_length=100)
    title = serializers.CharField(required=True, max_length=255)
    message = serializers.TextField(required=True)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'urgent'],
        default='normal',
        required=False
    )
    related_entity_type = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )
    related_entity_id = serializers.UUIDField(
        required=False,
        allow_null=True
    )
    action_url = serializers.URLField(
        required=False,
        allow_blank=True,
        max_length=500
    )
    action_text = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict
    )

    def create(self, validated_data):
        """Create notification using NotificationService."""
        from apps.users.models import User

        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)

        notification = NotificationService.create_notification(
            user=user,
            **validated_data
        )

        return notification


class NotificationMarkReadSerializer(serializers.Serializer):
    """
    Mark notification as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )


# ============================================================================
# NOTIFICATION PREFERENCES SERIALIZERS
# ============================================================================

class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    User notification preferences serializer.

    Manages user's notification delivery preferences across channels.
    """

    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'in_app_enabled',
            'email_enabled',
            'push_enabled',
            'digest_frequency',
            'quiet_hours_start',
            'quiet_hours_end',
            'type_preferences',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validate quiet hours if both are provided."""
        start = attrs.get('quiet_hours_start')
        end = attrs.get('quiet_hours_end')

        if start and end and start >= end:
            raise serializers.ValidationError({
                'quiet_hours_end': 'End time must be after start time.'
            })

        return attrs


class NotificationTypePreferenceSerializer(serializers.Serializer):
    """
    Update preference for specific notification type.
    """
    notification_type = serializers.CharField(required=True, max_length=100)
    enabled = serializers.BooleanField(required=True)


class QuietHoursSerializer(serializers.Serializer):
    """
    Set quiet hours for notifications.
    """
    start_time = serializers.TimeField(
        required=True,
        help_text="Start time in HH:MM format (e.g., '22:00')"
    )
    end_time = serializers.TimeField(
        required=True,
        help_text="End time in HH:MM format (e.g., '07:00')"
    )

    def validate(self, attrs):
        """Validate that end time is different from start time."""
        if attrs['start_time'] == attrs['end_time']:
            raise serializers.ValidationError(
                "Start time and end time cannot be the same."
            )
        return attrs


# ============================================================================
# NOTIFICATION STATISTICS SERIALIZERS
# ============================================================================

class NotificationStatsSerializer(serializers.Serializer):
    """
    Notification statistics for user dashboard.
    """
    total_count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    urgent_count = serializers.IntegerField()
    by_type = serializers.DictField()
    recent_notifications = NotificationListSerializer(many=True)
