import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.advisory.llm_service import LLMAdvisoryService
from apps.advisory.models import Conversation, Message
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def advisory_user(db):
    return User.objects.create_user(
        auth0_id="advisory_contract_auth0",
        email="advisory-contract@example.com",
        username="advisory_contract_user",
        full_name="Advisory Contract User",
        date_of_birth="1998-01-01",
    )


@pytest.mark.django_db
def test_chat_persists_conversation_and_messages(api_client, advisory_user, monkeypatch):
    api_client.force_authenticate(user=advisory_user)

    class StubLLMService:
        def build_user_context(self, user):
            return {"name": user.full_name, "skills": []}

        def generate_response(self, message, conversation_history=None, user_context=None):
            return (
                "You should build one strong portfolio project next.",
                0.25,
                {
                    "source": "baseline",
                    "processing_time_ms": 250,
                    "model": "baseline-advisor-v1",
                    "trace_id": "trace-123",
                    "fallback_used": False,
                },
            )

    monkeypatch.setattr(
        "apps.advisory.llm_service.get_llm_service",
        lambda: StubLLMService(),
    )

    response = api_client.post(
        "/api/v1/advisory/chat/",
        {"message": "What should I focus on next?"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["conversation_id"]
    assert response.data["response"] == "You should build one strong portfolio project next."
    assert response.data["metadata"]["trace_id"] == "trace-123"

    conversation = Conversation.objects.get(id=response.data["conversation_id"])
    assert conversation.user == advisory_user
    assert conversation.message_count == 2
    assert conversation.messages.count() == 2
    assert list(conversation.messages.values_list("role", flat=True)) == ["user", "assistant"]

    assistant_message = Message.objects.get(conversation=conversation, role="assistant")
    assert assistant_message.model_used == "baseline-advisor-v1"
    assert assistant_message.response_time_ms == 250
    assert assistant_message.context_used["runtime"]["trace_id"] == "trace-123"


def test_llm_service_redirects_coding_requests_without_llm(monkeypatch):
    service = LLMAdvisoryService()

    monkeypatch.setattr(
        "apps.advisory.llm_service.get_rag_runtime",
        lambda: {
            "classify_message": lambda message: ("coding_redirect", ""),
            "get_redirect_response": lambda message: "I can help you learn Python for a backend role instead.",
            "get_clarifying_question": lambda: "Clarify",
            "system_prompt": "system",
            "retrieve_context": lambda *args, **kwargs: [],
        },
    )

    response, delay, metadata = service.generate_response(
        "How do I implement a binary tree in Python?",
        conversation_history=[],
        user_context={},
    )

    assert response == "I can help you learn Python for a backend role instead."
    assert delay >= 0.5
    assert metadata["source"] == "scope_filter"
    assert metadata["fallback_used"] is True


def test_llm_service_falls_back_when_retrieval_fails(monkeypatch):
    service = LLMAdvisoryService()

    def failing_retrieval(*args, **kwargs):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr(
        "apps.advisory.llm_service.get_rag_runtime",
        lambda: {
            "classify_message": lambda message: ("in_scope", ""),
            "get_redirect_response": lambda message: "redirect",
            "get_clarifying_question": lambda: "Clarify",
            "system_prompt": "system",
            "retrieve_context": failing_retrieval,
        },
    )

    response, _delay, metadata = service.generate_response(
        "What should I learn for backend jobs?",
        conversation_history=[],
        user_context={"skills": ["Python"]},
    )

    assert response
    assert metadata["source"] == "fallback"
    assert metadata["error_code"] == "retrieval_failed"
