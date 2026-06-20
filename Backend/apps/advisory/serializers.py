"""
Advisory Service Serializers

Implements AI chatbot serializers for career guidance.

SRS References:
- FR-13: AI Chatbot Interface
- FR-14: Context-Aware Responses
- FR-15: RAG Pipeline (ChromaDB)
"""

from rest_framework import serializers
from apps.advisory.models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    """Chat message serializer."""

    class Meta:
        model = Message
        fields = [
            'id',
            'role',
            'content',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = ['id', 'tokens_used', 'created_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """Minimal conversation info for list views."""
    last_message_preview = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'topic',
            'message_count',
            'last_message_at',
            'last_message_preview',
            'created_at',
        ]

    def get_last_message_preview(self, obj):
        """Get preview of the last message in conversation."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            content = last_message.content
            return content[:100] + '...' if len(content) > 100 else content
        return None


class ConversationSerializer(serializers.ModelSerializer):
    """Complete conversation with messages."""
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'user',
            'title',
            'topic',
            'messages',
            'message_count',
            'total_tokens_used',
            'last_message_at',
            'context_snapshot',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'message_count',
            'total_tokens_used',
            'last_message_at',
            'created_at',
            'updated_at',
        ]


class ChatMessageSerializer(serializers.Serializer):
    """Send chat message with optional conversation history."""
    message = serializers.CharField(required=True, min_length=1, max_length=2000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    conversation_history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
        help_text="Previous messages in conversation for context. Each item should have 'role' and 'content' keys."
    )
