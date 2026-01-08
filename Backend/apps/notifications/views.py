"""
Notifications Service Views

Implements REST API views for notification delivery and preference management.
"""

from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q

from apps.notifications.models import Notification, NotificationPreference
from apps.notifications.serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationCreateSerializer,
    NotificationMarkReadSerializer,
    NotificationPreferenceSerializer,
    NotificationTypePreferenceSerializer,
    QuietHoursSerializer,
    NotificationStatsSerializer,
)
from apps.notifications.services import (
    NotificationService,
    NotificationPreferenceService,
)


# ============================================================================
# NOTIFICATION VIEWS
# ============================================================================

class NotificationViewSet(viewsets.ModelViewSet):
    """
    Manage user notifications.

    Endpoints:
    - GET /notifications/ - List user's notifications
    - GET /notifications/{id}/ - Get specific notification
    - DELETE /notifications/{id}/ - Delete notification
    - POST /notifications/mark_read/ - Mark notification(s) as read
    - POST /notifications/mark_all_read/ - Mark all as read
    - GET /notifications/unread/ - Get unread notifications
    - GET /notifications/urgent/ - Get urgent notifications
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return notifications for current user only."""
        return Notification.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-created_at')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return NotificationListSerializer
        elif self.action == 'create':
            return NotificationCreateSerializer
        return NotificationSerializer

    def list(self, request, *args, **kwargs):
        """
        List user notifications with optional filtering.

        Query Parameters:
        - unread_only: Boolean (true/false)
        - notification_type: Filter by type
        - priority: Filter by priority (low, normal, high, urgent)
        """
        queryset = self.get_queryset()

        # Filter by unread
        unread_only = request.query_params.get('unread_only', '').lower() == 'true'
        if unread_only:
            queryset = queryset.filter(is_read=False)

        # Filter by type
        notification_type = request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        # Filter by priority
        priority = request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Delete notification (soft delete)."""
        instance = self.get_object()
        success = NotificationService.delete_notification(str(instance.id))

        if success:
            return Response(
                {'message': 'Notification deleted successfully'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'error': 'Failed to delete notification'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """
        Mark specific notification(s) as read.

        Request Body:
        {
            "notification_ids": ["uuid1", "uuid2", ...]
        }

        If notification_ids is empty or not provided, marks ALL as read.
        """
        serializer = NotificationMarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('notification_ids', [])

        if notification_ids:
            # Mark specific notifications as read
            marked_count = 0
            for notif_id in notification_ids:
                notification = NotificationService.mark_as_read(str(notif_id))
                if notification:
                    marked_count += 1

            return Response(
                {
                    'message': f'{marked_count} notification(s) marked as read',
                    'count': marked_count
                },
                status=status.HTTP_200_OK
            )
        else:
            # Mark all as read
            count = NotificationService.mark_all_as_read(request.user)
            return Response(
                {
                    'message': f'All {count} notifications marked as read',
                    'count': count
                },
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = NotificationService.mark_all_as_read(request.user)
        return Response(
            {
                'message': f'All {count} notifications marked as read',
                'count': count
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications only."""
        notifications = NotificationService.get_user_notifications(
            user=request.user,
            unread_only=True,
            limit=50
        )

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """Get urgent notifications."""
        notifications = NotificationService.get_urgent_notifications(request.user)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        Get notifications by type.

        Query Parameters:
        - type: Notification type (required)
        """
        notification_type = request.query_params.get('type')
        if not notification_type:
            return Response(
                {'error': 'type parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        notifications = NotificationService.get_notifications_by_type(
            user=request.user,
            notification_type=notification_type
        )

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


# ============================================================================
# NOTIFICATION PREFERENCES VIEWS
# ============================================================================

class NotificationPreferencesView(generics.RetrieveUpdateAPIView):
    """
    Get and update notification preferences.

    GET /preferences/ - Get current preferences
    PUT /preferences/ - Update preferences
    PATCH /preferences/ - Partial update
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Get or create preferences for current user."""
        return NotificationPreferenceService.get_or_create_preferences(
            self.request.user
        )

    def update(self, request, *args, **kwargs):
        """Update notification preferences."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # Update using service
        updated_preferences = NotificationPreferenceService.update_preferences(
            user=request.user,
            **serializer.validated_data
        )

        return Response(
            NotificationPreferenceSerializer(updated_preferences).data,
            status=status.HTTP_200_OK
        )


class UpdateTypePreferenceView(APIView):
    """
    Enable/disable specific notification type.

    POST /preferences/type/
    {
        "notification_type": "milestone_completed",
        "enabled": true
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Update preference for specific notification type."""
        serializer = NotificationTypePreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        preferences = NotificationPreferenceService.set_type_preference(
            user=request.user,
            notification_type=serializer.validated_data['notification_type'],
            enabled=serializer.validated_data['enabled']
        )

        return Response(
            NotificationPreferenceSerializer(preferences).data,
            status=status.HTTP_200_OK
        )


class SetQuietHoursView(APIView):
    """
    Set quiet hours for notifications.

    POST /preferences/quiet-hours/
    {
        "start_time": "22:00",
        "end_time": "07:00"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Set quiet hours."""
        serializer = QuietHoursSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        start_time = serializer.validated_data['start_time'].strftime('%H:%M')
        end_time = serializer.validated_data['end_time'].strftime('%H:%M')

        preferences = NotificationPreferenceService.set_quiet_hours(
            user=request.user,
            start_time=start_time,
            end_time=end_time
        )

        return Response(
            {
                'message': 'Quiet hours updated successfully',
                'preferences': NotificationPreferenceSerializer(preferences).data
            },
            status=status.HTTP_200_OK
        )


# ============================================================================
# NOTIFICATION STATISTICS VIEWS
# ============================================================================

class NotificationStatsView(APIView):
    """
    Get notification statistics for user dashboard.

    GET /stats/

    Returns:
    - total_count: Total notifications
    - unread_count: Unread notifications
    - urgent_count: Urgent unread notifications
    - by_type: Count by notification type
    - recent_notifications: Last 5 notifications
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get notification statistics."""
        user = request.user

        # Get counts
        all_notifications = Notification.objects.filter(
            user=user,
            is_deleted=False
        )

        total_count = all_notifications.count()
        unread_count = NotificationService.get_unread_count(user)
        urgent_count = all_notifications.filter(
            is_read=False,
            priority='urgent'
        ).count()

        # Count by type
        by_type = dict(
            all_notifications.values('notification_type')
            .annotate(count=Count('id'))
            .values_list('notification_type', 'count')
        )

        # Get recent notifications
        recent = NotificationService.get_user_notifications(
            user=user,
            unread_only=False,
            limit=5
        )

        stats = {
            'total_count': total_count,
            'unread_count': unread_count,
            'urgent_count': urgent_count,
            'by_type': by_type,
            'recent_notifications': NotificationListSerializer(recent, many=True).data
        }

        serializer = NotificationStatsSerializer(data=stats)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
