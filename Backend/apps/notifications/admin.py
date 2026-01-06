"""
Notifications Module Admin Configuration

Provides comprehensive admin interface for notifications and preferences.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notifications"""

    list_display = [
        'user_email',
        'type_badge',
        'title_display',
        'priority_badge',
        'read_status_badge',
        'entity_link',
        'delivery_badge',
        'created_at',
    ]

    list_filter = [
        'notification_type',
        'priority',
        'is_read',
        'delivery_status',
        'created_at',
    ]

    search_fields = [
        'title',
        'message',
        'user__email',
        'user__first_name',
        'user__last_name',
        'related_entity_type',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'read_at',
        'is_unread',
        'entity_display',
        'priority_icon',
        'type_icon',
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'notification_type',
                'type_icon',
            )
        }),
        ('Content', {
            'fields': (
                'title',
                'message',
            )
        }),
        ('Related Entity', {
            'fields': (
                'related_entity_type',
                'related_entity_id',
                'entity_display',
            )
        }),
        ('Action', {
            'fields': (
                'action_url',
                'action_text',
            )
        }),
        ('Status', {
            'fields': (
                'is_read',
                'read_at',
                'is_unread',
                'delivery_status',
            )
        }),
        ('Priority', {
            'fields': (
                'priority',
                'priority_icon',
            )
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_selected_as_read', 'mark_selected_as_unread']

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def type_badge(self, obj):
        """Display notification type with icon"""
        type_colors = {
            'milestone_achieved': '#27ae60',
            'course_completed': '#3498db',
            'job_match': '#9b59b6',
            'roadmap_generated': '#e67e22',
            'assessment_complete': '#1abc9c',
            'roadmap_updated': '#3498db',
            'new_course_added': '#2ecc71',
            'skill_recommendation': '#f39c12',
            'system_announcement': '#e74c3c',
            'achievement_unlocked': '#f1c40f',
        }
        color = type_colors.get(obj.notification_type, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{} {}</span>',
            color,
            obj.type_icon,
            obj.get_notification_type_display()
        )
    type_badge.short_description = 'Type'
    type_badge.admin_order_field = 'notification_type'

    def title_display(self, obj):
        """Display title with truncation"""
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_display.short_description = 'Title'
    title_display.admin_order_field = 'title'

    def priority_badge(self, obj):
        """Display priority with color and icon"""
        priority_colors = {
            'low': '#95a5a6',
            'normal': '#3498db',
            'high': '#e67e22',
            'urgent': '#e74c3c',
        }
        color = priority_colors.get(obj.priority, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            color,
            obj.priority_icon,
            obj.priority.upper()
        )
    priority_badge.short_description = 'Priority'
    priority_badge.admin_order_field = 'priority'

    def read_status_badge(self, obj):
        """Display read/unread status"""
        if obj.is_read:
            return format_html(
                '<span style="color: #95a5a6;">✓ Read</span>'
            )
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">● UNREAD</span>'
        )
    read_status_badge.short_description = 'Status'
    read_status_badge.admin_order_field = 'is_read'

    def entity_link(self, obj):
        """Display related entity with link"""
        if not obj.related_entity_type:
            return format_html('<span style="color: gray;">No entity</span>')

        entity_id_short = str(obj.related_entity_id)[:8] if obj.related_entity_id else 'N/A'
        return format_html(
            '<span style="color: #3498db;" title="{}">{}: {}</span>',
            obj.related_entity_id,
            obj.related_entity_type,
            entity_id_short
        )
    entity_link.short_description = 'Related Entity'

    def delivery_badge(self, obj):
        """Display delivery status"""
        status_colors = {
            'sent': '#27ae60',
            'pending': '#f39c12',
            'failed': '#e74c3c',
        }
        color = status_colors.get(obj.delivery_status, '#95a5a6')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_delivery_status_display()
        )
    delivery_badge.short_description = 'Delivery'
    delivery_badge.admin_order_field = 'delivery_status'

    def mark_selected_as_read(self, request, queryset):
        """Mark selected notifications as read"""
        updated = 0
        for notification in queryset.filter(is_read=False):
            notification.mark_as_read()
            updated += 1
        self.message_user(request, f'{updated} notification(s) marked as read.')
    mark_selected_as_read.short_description = "Mark selected as read"

    def mark_selected_as_unread(self, request, queryset):
        """Mark selected notifications as unread"""
        updated = 0
        for notification in queryset.filter(is_read=True):
            notification.mark_as_unread()
            updated += 1
        self.message_user(request, f'{updated} notification(s) marked as unread.')
    mark_selected_as_unread.short_description = "Mark selected as unread"

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user')

    def changelist_view(self, request, extra_context=None):
        """Add unread count to changelist"""
        extra_context = extra_context or {}

        # Get statistics
        total_count = self.get_queryset(request).count()
        unread_count = self.get_queryset(request).filter(is_read=False).count()
        urgent_count = self.get_queryset(request).filter(priority='urgent').count()

        extra_context['total_notifications'] = total_count
        extra_context['unread_notifications'] = unread_count
        extra_context['urgent_notifications'] = urgent_count

        return super().changelist_view(request, extra_context)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for Notification Preferences"""

    list_display = [
        'user_email',
        'channels_badge',
        'digest_badge',
        'quiet_hours_badge',
        'preferences_summary',
        'updated_at',
    ]

    list_filter = [
        'in_app_enabled',
        'email_enabled',
        'push_enabled',
        'digest_frequency',
        'created_at',
    ]

    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'enabled_channels',
        'enabled_channels_display',
        'has_quiet_hours',
        'quiet_hours_display',
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
            )
        }),
        ('Notification Channels', {
            'fields': (
                'in_app_enabled',
                'email_enabled',
                'push_enabled',
                'enabled_channels_display',
            )
        }),
        ('Type Preferences', {
            'fields': ('preferences',),
            'description': 'Per-type notification preferences (JSONB)'
        }),
        ('Digest Settings', {
            'fields': ('digest_frequency',)
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_start',
                'quiet_hours_end',
                'has_quiet_hours',
                'quiet_hours_display',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def channels_badge(self, obj):
        """Display enabled channels as badges"""
        badges = []

        if obj.in_app_enabled:
            badges.append('<span style="background-color: #3498db; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">IN-APP</span>')
        if obj.email_enabled:
            badges.append('<span style="background-color: #27ae60; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">EMAIL</span>')
        if obj.push_enabled:
            badges.append('<span style="background-color: #9b59b6; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">PUSH</span>')

        if not badges:
            return format_html('<span style="color: gray;">None enabled</span>')

        return format_html(' '.join(badges))
    channels_badge.short_description = 'Channels'

    def digest_badge(self, obj):
        """Display digest frequency"""
        freq_colors = {
            'never': '#95a5a6',
            'daily': '#3498db',
            'weekly': '#27ae60',
            'monthly': '#f39c12',
        }
        color = freq_colors.get(obj.digest_frequency, '#95a5a6')

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_digest_frequency_display()
        )
    digest_badge.short_description = 'Digest'
    digest_badge.admin_order_field = 'digest_frequency'

    def quiet_hours_badge(self, obj):
        """Display quiet hours status"""
        if not obj.has_quiet_hours:
            return format_html('<span style="color: gray;">Not set</span>')

        return format_html(
            '<span style="color: #3498db; font-weight: bold;">🌙 {}</span>',
            obj.quiet_hours_display
        )
    quiet_hours_badge.short_description = 'Quiet Hours'

    def preferences_summary(self, obj):
        """Display count of custom preferences"""
        if not obj.preferences or obj.preferences == {}:
            return format_html('<span style="color: gray;">Default (all enabled)</span>')

        enabled_count = sum(1 for v in obj.preferences.values() if v)
        disabled_count = sum(1 for v in obj.preferences.values() if not v)

        return format_html(
            '<span title="Custom preferences set">✓ {} enabled, ✗ {} disabled</span>',
            enabled_count,
            disabled_count
        )
    preferences_summary.short_description = 'Custom Preferences'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user')
