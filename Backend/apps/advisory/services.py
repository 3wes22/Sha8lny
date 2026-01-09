"""
Advisory Service Layer

Handles AI-powered career advisory chatbot conversations and RAG context management.
"""

from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Conversation, Message
from apps.users.models import User
from apps.notifications.signals import chat_message_sent, chat_response_generated


class ConversationService:
    """Service for conversation management"""

    @staticmethod
    @transaction.atomic
    def create_conversation(
        user: User,
        title: str = "New Conversation",
        context_type: Optional[str] = None
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user: User instance
            title: Conversation title
            context_type: Optional context type (career, skill, roadmap, etc.)

        Returns:
            Conversation: Created conversation
        """
        conversation = Conversation.objects.create(
            user=user,
            title=title,
            status='active',
            context={
                'type': context_type or 'general',
                'created_at': timezone.now().isoformat()
            },
            processing_status='completed'
        )

        # Emit signal (conversation started with first message)
        chat_message_sent.send(
            sender=Conversation,
            instance=conversation,
            user=user
        )

        return conversation

    @staticmethod
    def get_user_conversations(
        user: User,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Get all conversations for user.

        Args:
            user: User instance
            status: Optional status filter (active, closed, archived)
            limit: Maximum results

        Returns:
            List[Conversation]: User's conversations
        """
        queryset = Conversation.objects.filter(
            user=user,
            is_deleted=False
        )

        if status:
            queryset = queryset.filter(status=status)

        return list(queryset.order_by('-updated_at')[:limit])

    @staticmethod
    def get_active_conversations(user: User) -> List[Conversation]:
        """Get user's active conversations"""
        return list(Conversation.objects.filter(
            user=user,
            status='active',
            is_deleted=False
        ).order_by('-updated_at'))

    @staticmethod
    def get_conversation_by_id(conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        try:
            return Conversation.objects.prefetch_related('messages').get(
                id=conversation_id,
                is_deleted=False
            )
        except Conversation.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def update_conversation_status(
        conversation: Conversation,
        status: str
    ) -> Conversation:
        """
        Update conversation status.

        Args:
            conversation: Conversation instance
            status: New status (active, closed, archived)

        Returns:
            Conversation: Updated conversation
        """
        conversation.status = status
        conversation.save(update_fields=['status', 'updated_at'])
        return conversation

    @staticmethod
    @transaction.atomic
    def close_conversation(conversation: Conversation) -> Conversation:
        """Close a conversation"""
        return ConversationService.update_conversation_status(conversation, 'closed')

    @staticmethod
    @transaction.atomic
    def archive_conversation(conversation: Conversation) -> Conversation:
        """Archive a conversation"""
        return ConversationService.update_conversation_status(conversation, 'archived')

    @staticmethod
    def get_conversation_statistics(conversation: Conversation) -> Dict[str, Any]:
        """Get statistics for a conversation"""
        messages = conversation.messages.filter(is_deleted=False)

        total_messages = messages.count()
        user_messages = messages.filter(sender_type='user').count()
        ai_messages = messages.filter(sender_type='ai').count()

        # Calculate average satisfaction
        rated_messages = messages.filter(
            feedback_rating__isnull=False
        )
        avg_rating = None
        if rated_messages.exists():
            total_rating = sum(m.feedback_rating for m in rated_messages)
            avg_rating = round(total_rating / rated_messages.count(), 2)

        return {
            'total_messages': total_messages,
            'user_messages': user_messages,
            'ai_messages': ai_messages,
            'average_rating': avg_rating,
            'duration_minutes': 0  # TODO: Calculate from first to last message
        }


class MessageService:
    """Service for message handling and AI response generation"""

    @staticmethod
    @transaction.atomic
    def send_user_message(
        conversation: Conversation,
        content: str,
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> Message:
        """
        Send a user message in conversation.

        Args:
            conversation: Conversation instance
            content: Message content
            attachments: Optional attachments metadata

        Returns:
            Message: Created message
        """
        message = Message.objects.create(
            conversation=conversation,
            sender_type='user',
            content=content,
            attachments=attachments or []
        )

        # Update conversation timestamp
        conversation.save(update_fields=['updated_at'])

        # Emit signal
        chat_message_sent.send(
            sender=Message,
            instance=message,
            conversation=conversation
        )

        return message

    @staticmethod
    @transaction.atomic
    def generate_ai_response(
        conversation: Conversation,
        user_message: Message,
        use_rag: bool = True
    ) -> Message:
        """
        Generate AI response to user message.

        This would integrate with OpenAI/Claude API and RAG system.
        For now, it's a placeholder that will be implemented with async tasks.

        Args:
            conversation: Conversation instance
            user_message: User's message to respond to
            use_rag: Whether to use RAG context retrieval

        Returns:
            Message: AI-generated message
        """
        # Set conversation processing status
        conversation.processing_status = 'pending'
        conversation.save(update_fields=['processing_status', 'updated_at'])

        # TODO: Trigger async Celery task for AI generation
        # This would:
        # 1. Retrieve RAG context from user profile, roadmaps, assessments
        # 2. Build conversation history
        # 3. Call OpenAI/Claude API
        # 4. Process and validate response
        # tasks.generate_ai_response.delay(conversation.id, user_message.id, use_rag)

        # Placeholder: Create AI response
        ai_message = Message.objects.create(
            conversation=conversation,
            sender_type='ai',
            content=f"AI response to: {user_message.content[:50]}...",
            metadata={
                'model': 'gpt-4',  # Placeholder
                'rag_used': use_rag,
                'confidence': 0.95,
                'processing_time_ms': 1500
            }
        )

        # Update conversation status
        conversation.processing_status = 'completed'
        conversation.save(update_fields=['processing_status', 'updated_at'])

        return ai_message

    @staticmethod
    def get_conversation_messages(
        conversation: Conversation,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get messages for conversation in chronological order.

        Args:
            conversation: Conversation instance
            limit: Optional limit on messages returned

        Returns:
            List[Message]: Messages in conversation
        """
        queryset = Message.objects.filter(
            conversation=conversation,
            is_deleted=False
        ).order_by('created_at')

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    @staticmethod
    def get_recent_messages(
        conversation: Conversation,
        count: int = 10
    ) -> List[Message]:
        """Get N most recent messages"""
        return list(Message.objects.filter(
            conversation=conversation,
            is_deleted=False
        ).order_by('-created_at')[:count])

    @staticmethod
    @transaction.atomic
    def add_message_feedback(
        message: Message,
        rating: int,
        feedback_text: str = ""
    ) -> Message:
        """
        Add user feedback to AI message.

        Args:
            message: Message instance (should be AI message)
            rating: Rating 1-5
            feedback_text: Optional feedback text

        Returns:
            Message: Updated message
        """
        message.feedback_rating = rating
        message.feedback_text = feedback_text
        message.save(update_fields=['feedback_rating', 'feedback_text', 'updated_at'])

        return message

    @staticmethod
    def get_message_by_id(message_id: str) -> Optional[Message]:
        """Get message by ID"""
        try:
            return Message.objects.select_related('conversation').get(
                id=message_id,
                is_deleted=False
            )
        except Message.DoesNotExist:
            return None


class RAGContextService:
    """Service for RAG (Retrieval-Augmented Generation) context management"""

    @staticmethod
    def build_user_context(user: User) -> Dict[str, Any]:
        """
        Build comprehensive context for user from their profile and data.

        This retrieves relevant information to provide to the AI model.

        Args:
            user: User instance

        Returns:
            Dict: User context for RAG
        """
        from apps.users.models import UserSkill
        from apps.progress.models import UserProgress
        from apps.roadmaps.models import Roadmap
        from apps.assessments.models import AssessmentResult

        # Get user skills
        user_skills = list(UserSkill.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('skill').values(
            'skill__name',
            'proficiency_level',
            'years_of_experience'
        ))

        # Get active roadmaps
        active_roadmaps = list(Roadmap.objects.filter(
            user=user,
            status__in=['active', 'in_progress'],
            is_deleted=False
        ).values(
            'title',
            'target_career',
            'current_level',
            'target_level',
            'completion_percentage'
        )[:5])

        # Get recent assessment results
        assessments = list(AssessmentResult.objects.filter(
            user=user,
            is_deleted=False
        ).select_related('assessment').values(
            'assessment__title',
            'overall_score',
            'skill_level'
        ).order_by('-created_at')[:5])

        # Get progress metrics
        progress_data = list(UserProgress.objects.filter(
            user=user,
            is_deleted=False
        ).values(
            'roadmap__title',
            'completion_percentage',
            'current_streak_days',
            'total_study_hours'
        )[:5])

        context = {
            'user_profile': {
                'name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'bio': user.bio or '',
                'current_job_title': user.current_job_title or '',
                'career_goal': user.career_goal or '',
                'experience_years': user.years_of_experience or 0
            },
            'skills': user_skills,
            'active_roadmaps': active_roadmaps,
            'assessments': assessments,
            'progress': progress_data,
            'timestamp': timezone.now().isoformat()
        }

        return context

    @staticmethod
    def build_conversation_context(conversation: Conversation) -> Dict[str, Any]:
        """
        Build context from conversation history.

        Args:
            conversation: Conversation instance

        Returns:
            Dict: Conversation context
        """
        # Get recent messages (last 10)
        recent_messages = MessageService.get_recent_messages(conversation, count=10)

        # Reverse to chronological order
        recent_messages.reverse()

        messages_context = [
            {
                'sender': msg.sender_type,
                'content': msg.content,
                'timestamp': msg.created_at.isoformat()
            }
            for msg in recent_messages
        ]

        return {
            'conversation_id': str(conversation.id),
            'title': conversation.title,
            'messages': messages_context,
            'context_metadata': conversation.context
        }

    @staticmethod
    def build_full_rag_context(
        user: User,
        conversation: Conversation
    ) -> Dict[str, Any]:
        """
        Build complete RAG context combining user profile and conversation.

        This would be passed to the AI model along with the query.

        Args:
            user: User instance
            conversation: Conversation instance

        Returns:
            Dict: Complete RAG context
        """
        user_context = RAGContextService.build_user_context(user)
        conversation_context = RAGContextService.build_conversation_context(conversation)

        return {
            'user': user_context,
            'conversation': conversation_context,
            'platform_name': 'Sha8alny',
            'assistant_role': 'career_advisor',
            'capabilities': [
                'roadmap_generation',
                'skill_assessment',
                'course_recommendation',
                'job_matching',
                'career_advice'
            ]
        }

    @staticmethod
    def retrieve_relevant_documents(
        query: str,
        user: User,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from vector database.

        This would integrate with Pinecone/Weaviate for semantic search.
        For now, it's a placeholder.

        Args:
            query: User's query
            user: User instance
            top_k: Number of documents to retrieve

        Returns:
            List[Dict]: Relevant documents
        """
        # TODO: Implement vector database integration
        # This would:
        # 1. Embed the query using OpenAI embeddings
        # 2. Search Pinecone for similar vectors
        # 3. Retrieve metadata and content
        # 4. Rank and filter results
        # tasks.retrieve_rag_documents.delay(query, user.id, top_k)

        # Placeholder
        return [
            {
                'source': 'user_roadmap',
                'content': 'Sample roadmap content...',
                'relevance_score': 0.92
            },
            {
                'source': 'assessment_result',
                'content': 'Sample assessment insights...',
                'relevance_score': 0.87
            }
        ]
