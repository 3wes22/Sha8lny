"""
Advisory Service Admin Configuration

Provides admin interface for managing conversations and messages.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Conversations"""

    list_display = [
        'id',
        'user_email',
        'title_preview',
        'topic',
        'message_count',
        'total_tokens_used',
        'is_active_badge',
        'last_message_at',
        'created_at'
    ]

    list_filter = [
        'topic',
        'is_active',
        'created_at',
        'last_message_at'
    ]

    search_fields = [
        'title',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'message_count',
        'total_tokens_used',
        'last_message_at'
    ]

    autocomplete_fields = ['user']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'user',
                'title',
                'topic'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'last_message_at',
                'message_count',
                'total_tokens_used'
            )
        }),
        ('Context Snapshot', {
            'fields': ('context_snapshot',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'

    def title_preview(self, obj):
        """Display title with preview"""
        if obj.title:
            return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title
        return format_html('<span style="color: gray;">Untitled</span>')
    title_preview.short_description = 'Title'

    def is_active_badge(self, obj):
        """Display active status as colored badge"""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: gray;">○ Closed</span>'
        )
    is_active_badge.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Messages"""

    list_display = [
        'id',
        'conversation_id_display',
        'role_badge',
        'content_preview',
        'model_used',
        'tokens_used',
        'rating_display',
        'created_at'
    ]

    list_filter = [
        'role',
        'model_used',
        'user_rating',
        'is_helpful',
        'created_at'
    ]

    search_fields = [
        'content',
        'conversation__title',
        'conversation__user__email'
    ]

    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'tokens_used',
        'response_time_ms'
    ]

    autocomplete_fields = ['conversation']

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'conversation',
                'role',
                'content'
            )
        }),
        ('AI Metadata', {
            'fields': (
                'model_used',
                'tokens_used',
                'response_time_ms'
            )
        }),
        ('User Feedback', {
            'fields': (
                'user_rating',
                'is_helpful',
                'feedback_text'
            )
        }),
        ('RAG Context', {
            'fields': ('context_used',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def conversation_id_display(self, obj):
        """Display conversation ID as link"""
        return format_html(
            '<a href="/admin/advisory/conversation/{}/change/">{}</a>',
            obj.conversation.id,
            str(obj.conversation.id)[:8]
        )
    conversation_id_display.short_description = 'Conversation'

    def role_badge(self, obj):
        """Display role as colored badge"""
        colors = {
            'user': 'blue',
            'assistant': 'green',
            'system': 'gray'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.role, 'gray'),
            obj.role.upper()
        )
    role_badge.short_description = 'Role'

    def content_preview(self, obj):
        """Display content preview"""
        preview = obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
        return preview
    content_preview.short_description = 'Content'

    def rating_display(self, obj):
        """Display user rating with stars"""
        if obj.user_rating:
            stars = '⭐' * obj.user_rating
            return format_html('{} ({}/5)', stars, obj.user_rating)
        if obj.is_helpful is not None:
            return format_html(
                '<span style="color: {};">● {}</span>',
                'green' if obj.is_helpful else 'red',
                'Helpful' if obj.is_helpful else 'Not Helpful'
            )
        return format_html('<span style="color: gray;">No feedback</span>')
    rating_display.short_description = 'Feedback'

    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('conversation', 'conversation__user')
