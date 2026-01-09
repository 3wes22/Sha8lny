"""
Advisory Service Models

Handles AI-powered career advisory chatbot with RAG (Retrieval-Augmented Generation)
for context-aware, personalized career guidance.
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import BaseModel


class Conversation(BaseModel):
    """
    Represents a chatbot conversation session between a user and the AI advisory system.

    Uses RAG to provide context-aware responses based on user profile, roadmap,
    assessment results, and career knowledge base.
    """

    # Topic choices
    GENERAL = 'general'
    ROADMAP = 'roadmap'
    ASSESSMENT = 'assessment'
    JOB_SEARCH = 'job_search'
    CAREER_ADVICE = 'career_advice'

    TOPIC_CHOICES = [
        (GENERAL, 'General Career Questions'),
        (ROADMAP, 'Roadmap Guidance'),
        (ASSESSMENT, 'Assessment Interpretation'),
        (JOB_SEARCH, 'Job Search Assistance'),
        (CAREER_ADVICE, 'Career Advisory'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations',
        help_text="User who initiated this conversation"
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Conversation title (auto-generated from first message)"
    )

    topic = models.CharField(
        max_length=100,
        choices=TOPIC_CHOICES,
        default=GENERAL,
        help_text="Primary topic of conversation"
    )

    # Context snapshot (JSONB)
    context_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of user context at conversation start"
    )
    # Example: {
    #   "roadmap_id": "uuid",
    #   "assessment_id": "uuid",
    #   "career_goal": "Backend Developer",
    #   "user_skills": ["Python", "Django"],
    #   "current_phase": "Intermediate"
    # }

    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this conversation is currently active"
    )

    last_message_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of last message in conversation"
    )

    # Metadata
    message_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of messages in conversation"
    )

    total_tokens_used = models.PositiveIntegerField(
        default=0,
        help_text="Total LLM tokens consumed in this conversation"
    )

    # AI Processing Status (for async RAG processing)
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('completed', 'Completed'),
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('failed', 'Failed'),
        ],
        default='completed',
        help_text="Status of AI message processing"
    )

    task_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Celery task ID for async processing"
    )

    error_message = models.TextField(
        blank=True,
        help_text="Error details if processing failed"
    )

    class Meta:
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['user', '-last_message_at'], name='idx_conv_user_last_msg'),
            models.Index(fields=['is_active'], name='idx_conv_active'),
            models.Index(fields=['topic'], name='idx_conv_topic'),
        ]

    def __str__(self):
        return f"{self.title or 'Untitled'} - {self.user.email}"

    def __repr__(self):
        return f"<Conversation: {self.user.email} - {self.topic} ({self.message_count} messages)>"

    @property
    def last_user_message(self):
        """Get the last message from the user"""
        return self.messages.filter(role='user').order_by('-created_at').first()

    @property
    def last_ai_message(self):
        """Get the last AI response"""
        return self.messages.filter(role='assistant').order_by('-created_at').first()


class Message(BaseModel):
    """
    Represents a single message in a conversation (from user or AI).

    Stores RAG context used for generating AI responses and tracks model performance.
    """

    # Role choices
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'

    ROLE_CHOICES = [
        (USER, 'User Message'),
        (ASSISTANT, 'AI Assistant'),
        (SYSTEM, 'System Message'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation this message belongs to"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="Who sent this message"
    )

    content = models.TextField(
        help_text="Message content (user input or AI response)"
    )

    # RAG context used for this message (JSONB)
    context_used = models.JSONField(
        default=dict,
        blank=True,
        help_text="RAG context retrieved and used for generating this response"
    )
    # Example: {
    #   "roadmap_phase": "Intermediate",
    #   "relevant_courses": ["course-uuid-1", "course-uuid-2"],
    #   "user_skill_level": "beginner",
    #   "retrieved_documents": [
    #       {"source": "roadmap", "content": "..."},
    #       {"source": "knowledge_base", "content": "..."}
    #   ],
    #   "assessment_insights": {...}
    # }

    # AI metadata (for assistant messages)
    model_used = models.CharField(
        max_length=100,
        blank=True,
        help_text="LLM model used for this response (e.g., 'gpt-4', 'claude-3-sonnet')"
    )

    tokens_used = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Number of tokens consumed for this message"
    )

    response_time_ms = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Time taken to generate response (milliseconds)"
    )

    # User feedback (for assistant messages)
    user_rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ],
        help_text="User rating of AI response (1-5 stars)"
    )

    is_helpful = models.BooleanField(
        blank=True,
        null=True,
        help_text="Whether user found this response helpful"
    )

    feedback_text = models.TextField(
        blank=True,
        help_text="Optional user feedback text"
    )

    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at'], name='idx_msg_conv_created'),
            models.Index(fields=['role'], name='idx_msg_role'),
            models.Index(fields=['created_at'], name='idx_msg_created'),
            models.Index(fields=['model_used'], name='idx_msg_model'),
        ]

    def __str__(self):
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"{self.role}: {preview}"

    def __repr__(self):
        return f"<Message: {self.conversation.id} - {self.role} - {self.created_at}>"

    @property
    def is_from_user(self):
        """Check if message is from user"""
        return self.role == self.USER

    @property
    def is_from_ai(self):
        """Check if message is from AI assistant"""
        return self.role == self.ASSISTANT

    @property
    def has_feedback(self):
        """Check if user provided feedback"""
        return self.user_rating is not None or self.is_helpful is not None
