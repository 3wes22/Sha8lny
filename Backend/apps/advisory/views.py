"""
Advisory Service Views

Implements AI chatbot REST API views for career guidance.

SRS References:
- FR-13: AI Chatbot Interface
- FR-14: Context-Aware Responses
- FR-15: RAG Pipeline
"""

from rest_framework import viewsets, status, permissions, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.advisory.models import Conversation
from apps.advisory.chat_service import AdvisoryConversationService
from apps.advisory.serializers import (
    ConversationSerializer,
    ConversationListSerializer,
    ChatMessageSerializer,
)


# Response serializer for schema documentation
class CitationSerializer(drf_serializers.Serializer):
    """Public per-source citation surfaced under each assistant answer (Task 2.2)."""
    source = drf_serializers.CharField()
    url = drf_serializers.CharField(allow_blank=True)
    section = drf_serializers.CharField(allow_blank=True)
    excerpt = drf_serializers.CharField(allow_blank=True)
    confidence_tier = drf_serializers.ChoiceField(choices=["HIGH", "MEDIUM", "LOW"])


class ChatResponseSerializer(drf_serializers.Serializer):
    """Response serializer for chat endpoint (for OpenAPI schema)."""
    conversation_id = drf_serializers.UUIDField()
    response = drf_serializers.CharField()
    delay_ms = drf_serializers.IntegerField()
    retrieved_documents = CitationSerializer(many=True)
    no_retrieval_context = drf_serializers.BooleanField()
    metadata = drf_serializers.DictField()


class ChatView(APIView):
    """
    Send message to AI chatbot.

    SRS FR-13: AI Chatbot Interface
    SRS Appendix B: POST /advisory/chat
    
    Messages are persisted to the user's conversation history so follow-up requests
    can reuse the same context contract.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatMessageSerializer

    @extend_schema(
        request=ChatMessageSerializer,
        responses={
            200: OpenApiResponse(description='AI response generated'),
        },
        description="""
        Send a message to the AI chatbot and receive a response.

        Request Body:
        - message: The user's message (required)
        - conversation_history: Optional list of previous messages for context

        Returns the AI assistant's response with suggested delay for typing indicator
        and the persisted conversation id for future turns.
        """
    )
    def post(self, request):
        """Send message and get AI response."""
        from apps.advisory.llm_service import get_llm_service
        
        serializer = ChatMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message_content = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')
        conversation_history = serializer.validated_data.get('conversation_history', [])

        # Get LLM service
        llm_service = get_llm_service()
        
        # Build user context from profile
        user_context = llm_service.build_user_context(request.user)
        conversation = AdvisoryConversationService.get_or_create_conversation(
            user=request.user,
            conversation_id=str(conversation_id) if conversation_id else None,
            first_message=message_content,
            context_snapshot=user_context,
        )
        resolved_history = AdvisoryConversationService.build_history(conversation, conversation_history)
        AdvisoryConversationService.add_user_message(conversation, message_content, user_context)
        
        # Generate response
        response_text, delay_seconds, metadata = llm_service.generate_response(
            message=message_content,
            conversation_history=resolved_history,
            user_context=user_context,
        )
        assistant_context = metadata.get('context_used') if isinstance(metadata.get('context_used'), dict) else user_context
        AdvisoryConversationService.add_assistant_message(
            conversation,
            response_text,
            assistant_context,
            metadata,
        )
        AdvisoryConversationService.refresh_conversation(conversation)

        return Response({
            'conversation_id': str(conversation.id),
            'response': response_text,
            'delay_ms': int(delay_seconds * 1000),
            # Top-level citation contract (Task 2.2) so the frontend renders
            # Sources / no-context state without reaching into `metadata`.
            'retrieved_documents': metadata.get('retrieved_documents', []),
            'no_retrieval_context': bool(metadata.get('no_retrieval_context', False)),
            'metadata': metadata,
        }, status=status.HTTP_200_OK)


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
