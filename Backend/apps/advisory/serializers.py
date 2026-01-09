"""
Advisory Service Serializers

Implements AI chatbot serializers for career guidance.

SRS References:
- FR-13: AI Chatbot Interface
- FR-14: Context-Aware Responses
- FR-15: RAG Pipeline (Pinecone)
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
    last_message_preview = serializers.CharField(read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'message_count',
            'last_message_at',
            'last_message_preview',
            'created_at',
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """Complete conversation with messages."""
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'user',
            'title',
            'messages',
            'message_count',
            'total_tokens_used',
            'last_message_at',
            'metadata',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'message_count',
            'total_tokens_used',
            'last_message_at',
            'created_at',
            'updated_at',
        ]


class ChatMessageSerializer(serializers.Serializer):
    """Send chat message."""
    message = serializers.CharField(required=True, min_length=1)
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
