"""
Advisory Service Views

Implements AI chatbot REST API views for career guidance.

SRS References:
- FR-13: AI Chatbot Interface
- FR-14: Context-Aware Responses
- FR-15: RAG Pipeline
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.advisory.models import Conversation, Message
from apps.advisory.serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    MessageSerializer,
    ChatMessageSerializer,
)
from apps.advisory.services import AdvisoryService


class ChatView(APIView):
    """
    Send message to AI chatbot.

    SRS FR-13: AI Chatbot Interface
    SRS Appendix B: POST /advisory/chat

    Request Body:
    {
        "message": "How can I become a backend developer?",
        "conversation_id": "uuid"  // optional, creates new if not provided
    }

    Returns:
    {
        "conversation_id": "uuid",
        "user_message": {...},
        "assistant_message": {...}
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Send message and get AI response."""
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message_content = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')

        # Get or create conversation
        if conversation_id:
            try:
                conversation = Conversation.objects.get(
                    id=conversation_id,
                    user=request.user,
                    is_deleted=False
                )
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Create new conversation
            conversation = Conversation.objects.create(
                user=request.user,
                title=message_content[:100]  # Use first 100 chars as title
            )

        # Create user message
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=message_content
        )

        # TODO: Get AI response using AdvisoryService
        # For now, return a placeholder response
        assistant_response = "This is a placeholder response. AI integration (OpenAI/Claude API) is pending implementation."

        # Create assistant message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=assistant_response,
            tokens_used=0  # TODO: Track actual token usage
        )

        # Update conversation
        conversation.message_count = conversation.messages.count()
        conversation.last_message_at = assistant_message.created_at
        conversation.save()

        return Response({
            'conversation_id': str(conversation.id),
            'user_message': MessageSerializer(user_message).data,
            'assistant_message': MessageSerializer(assistant_message).data
        }, status=status.HTTP_201_CREATED)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    Manage conversation history.

    SRS Appendix B: GET /advisory/history

    Endpoints:
    - GET /conversations/ - List user's conversations
    - GET /conversations/{id}/ - Get conversation with messages
    - DELETE /conversations/{id}/ - Delete conversation
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return conversations for current user only."""
        return Conversation.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).order_by('-last_message_at')

    def get_serializer_class(self):
        """Use minimal serializer for list view."""
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft delete conversation."""
        instance = self.get_object()
        instance.is_deleted = True
        instance.save()

        return Response(
            {'message': 'Conversation deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
