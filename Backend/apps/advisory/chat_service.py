"""
Conversation persistence helpers for the live advisory chat endpoint.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from django.utils import timezone

from apps.advisory.models import Conversation, Message
from apps.users.models import User


class AdvisoryConversationService:
    """Persist advisory conversations behind the live chat API."""

    @staticmethod
    def _title_from_message(message: str) -> str:
        preview = (message or "").strip()
        if not preview:
            return "Career advisory"
        if len(preview) <= 60:
            return preview
        return f"{preview[:57].rstrip()}..."

    @staticmethod
    def get_or_create_conversation(
        *,
        user: User,
        conversation_id: Optional[str],
        first_message: str,
        context_snapshot: Dict[str, object],
    ) -> Conversation:
        if conversation_id:
            return Conversation.objects.get(
                id=conversation_id,
                user=user,
                is_deleted=False,
            )

        return Conversation.objects.create(
            user=user,
            title=AdvisoryConversationService._title_from_message(first_message),
            topic=Conversation.GENERAL,
            context_snapshot=context_snapshot,
            is_active=True,
            last_message_at=timezone.now(),
            processing_status="completed",
        )

    @staticmethod
    def build_history(conversation: Conversation, fallback_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        persisted_messages = list(
            conversation.messages.filter(is_deleted=False)
            .order_by("created_at")
            .values("role", "content")
        )
        if persisted_messages:
            return persisted_messages
        return fallback_history

    @staticmethod
    def add_user_message(conversation: Conversation, content: str, context_used: Dict[str, object]) -> Message:
        return Message.objects.create(
            conversation=conversation,
            role=Message.USER,
            content=content,
            context_used=context_used,
        )

    @staticmethod
    def add_assistant_message(
        conversation: Conversation,
        content: str,
        context_used: Dict[str, object],
        metadata: Dict[str, object],
    ) -> Message:
        processing_time_ms = metadata.get("processing_time_ms")
        tokens_used = metadata.get("tokens_used")
        if not isinstance(tokens_used, int):
            prompt_tokens = metadata.get("prompt_tokens")
            completion_tokens = metadata.get("completion_tokens")
            if isinstance(prompt_tokens, int) and isinstance(completion_tokens, int):
                tokens_used = prompt_tokens + completion_tokens
            else:
                tokens_used = None

        assistant_context = {
            **context_used,
            "runtime": {
                "source": metadata.get("source"),
                "trace_id": metadata.get("trace_id"),
                "provider": metadata.get("provider"),
                "version": metadata.get("version"),
                "fallback_used": metadata.get("fallback_used"),
                "error_code": metadata.get("error_code"),
            },
        }
        return Message.objects.create(
            conversation=conversation,
            role=Message.ASSISTANT,
            content=content,
            context_used=assistant_context,
            model_used=(metadata.get("model") or "") if isinstance(metadata.get("model"), str) else "",
            tokens_used=tokens_used,
            response_time_ms=processing_time_ms if isinstance(processing_time_ms, int) else None,
        )

    @staticmethod
    def refresh_conversation(conversation: Conversation) -> Conversation:
        messages = conversation.messages.filter(is_deleted=False)
        conversation.message_count = messages.count()
        conversation.total_tokens_used = sum(
            message.tokens_used or 0 for message in messages.only("tokens_used")
        )
        conversation.last_message_at = timezone.now()
        conversation.save(
            update_fields=[
                "message_count",
                "total_tokens_used",
                "last_message_at",
                "updated_at",
            ]
        )
        return conversation
