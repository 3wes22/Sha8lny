import pytest
from decimal import Decimal
from rest_framework import status
from rest_framework.test import APIClient

from apps.advisory.llm_service import LLMAdvisoryService
from apps.advisory.models import Conversation, Message
from apps.assessments.models import Assessment, AssessmentResult
from apps.progress.services import ProgressService
from apps.roadmaps.models import RoadmapTemplate
from apps.roadmaps.services import RoadmapService
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


@pytest.fixture
def advisory_roadmap_template(db):
    return RoadmapTemplate.objects.create(
        title="Backend Engineer Roadmap",
        slug="advisory-backend-engineer-roadmap",
        description="A practical roadmap for backend engineering.",
        short_description="Backend focus",
        target_career="Backend Engineer",
        career_level=RoadmapTemplate.ENTRY_LEVEL,
        estimated_duration_weeks=20,
        difficulty_level="intermediate",
        prerequisites=["Python basics"],
        learning_outcomes=["Ship backend services"],
        is_published=True,
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


@pytest.mark.django_db
def test_build_user_context_prefers_active_roadmap_and_progress(
    advisory_user,
    advisory_roadmap_template,
):
    assessment = Assessment.objects.create(
        user=advisory_user,
        assessment_type="skills",
        target_career="Backend Engineer",
        questions=[],
        total_questions=0,
        status="completed",
        ai_processing_status="completed",
    )
    AssessmentResult.objects.create(
        assessment=assessment,
        overall_score=84,
        skill_scores={"python": 88},
        strengths=["Problem solving"],
        areas_for_improvement=["System design"],
        recommended_careers=[{"title": "Backend Engineer", "match_score": 91}],
        recommended_learning_paths=[],
        ai_insights="Strong backend fundamentals",
        llm_model_used="mock-v1",
        ai_confidence_score=0.8,
    )

    active_roadmap = RoadmapService.create_roadmap_from_template(
        user=advisory_user,
        template=advisory_roadmap_template,
    )
    RoadmapService.update_roadmap_status(active_roadmap, "active")

    draft_roadmap = RoadmapService.create_roadmap_from_template(
        user=advisory_user,
        template=advisory_roadmap_template,
    )

    progress = ProgressService.get_or_create_progress(advisory_user, active_roadmap)
    progress.current_streak_days = 4
    progress.total_learning_hours = Decimal("9.50")
    progress.save(update_fields=["current_streak_days", "total_learning_hours", "updated_at"])

    service = LLMAdvisoryService()
    context = service.build_user_context(advisory_user)

    assert context["latest_assessment"]["target_career"] == "Backend Engineer"
    assert context["active_roadmap"]["id"] == str(active_roadmap.id)
    assert context["active_roadmap"]["id"] != str(draft_roadmap.id)
    assert context["active_roadmap"]["current_streak_days"] == 4
    assert context["active_roadmap"]["total_learning_hours"] == 9.5


def test_normalize_documents_carries_citation_fields():
    service = LLMAdvisoryService()
    documents = [
        {
            "id": "bls_x_1",
            "content": "Software developers design computer applications and systems.",
            "score": 0.41,
            "confidence_tier": "HIGH",
            "metadata": {
                "source": "bls_ooh",
                "file": "software-developers.md",
                "url": "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm",
                "section": "What They Do",
                "category": "career_development",
                "quality_tier": "official",
            },
        }
    ]

    (normalized,) = service._normalize_documents(documents)

    assert normalized["source_name"] == "bls_ooh"
    assert normalized["url"].startswith("https://www.bls.gov")
    assert normalized["section"] == "What They Do"
    assert normalized["file"] == "software-developers.md"
    assert normalized["confidence_tier"] == "HIGH"
    # legacy fields keep their original semantics
    assert normalized["source"] == "career_development"
    assert normalized["excerpt"]


def test_normalize_documents_defaults_for_legacy_payloads():
    service = LLMAdvisoryService()

    (normalized,) = service._normalize_documents(
        [{"content": "Some retrieved passage with enough length.", "score": 0.2, "metadata": {}}]
    )

    assert normalized["confidence_tier"] == "LOW"
    assert normalized["url"] == ""
    assert normalized["source_name"] == "general"


def test_generate_response_exposes_public_citations(monkeypatch):
    """Task 2.2: a successful answer carries a public citation payload with all five fields."""
    service = LLMAdvisoryService()

    monkeypatch.setattr(
        "apps.advisory.llm_service.get_rag_runtime",
        lambda: {
            "classify_message": lambda message: ("in_scope", ""),
            "get_redirect_response": lambda message: "redirect",
            "get_clarifying_question": lambda: "Clarify",
            "system_prompt": "system",
            "retrieve_context": lambda *args, **kwargs: [
                {
                    "content": "Backend engineers in Egypt earn competitive salaries.",
                    "score": 0.5,
                    "confidence_tier": "HIGH",
                    "metadata": {
                        "source": "bls_ooh",
                        "url": "https://www.bls.gov/ooh/example.htm",
                        "section": "Pay",
                        "category": "career_development",
                    },
                }
            ],
        },
    )

    class _FakeMeta:
        processing_time_ms = 120
        model = "gemini-fake"
        provider = "gemini"
        trace_id = "trace-citation"

    class _FakeResult:
        text = "Backend roles pay well; focus on system design."
        metadata = _FakeMeta()
        prompt_tokens = 10
        completion_tokens = 20

    class _FakeGemmaClient:
        def __init__(self, *args, **kwargs):
            pass

        def generate_text(self, *args, **kwargs):
            return _FakeResult()

    monkeypatch.setattr("apps.advisory.llm_service.GemmaClient", _FakeGemmaClient)

    _response, _delay, metadata = service.generate_response(
        "What do backend engineers earn?",
        conversation_history=[],
        user_context={"skills": ["Python"]},
    )

    assert metadata["no_retrieval_context"] is False
    citations = metadata["retrieved_documents"]
    assert len(citations) == 1
    citation = citations[0]
    assert set(citation.keys()) == {"source", "url", "section", "excerpt", "confidence_tier"}
    assert citation["source"] == "bls_ooh"
    assert citation["url"].startswith("https://www.bls.gov")
    assert citation["section"] == "Pay"
    assert citation["confidence_tier"] == "HIGH"
    assert citation["excerpt"]


def test_generate_response_flags_no_retrieval_context(monkeypatch):
    """Task 2.2: an empty retrieval sets an explicit machine-readable flag for the frontend."""
    service = LLMAdvisoryService()

    monkeypatch.setattr(
        "apps.advisory.llm_service.get_rag_runtime",
        lambda: {
            "classify_message": lambda message: ("in_scope", ""),
            "get_redirect_response": lambda message: "redirect",
            "get_clarifying_question": lambda: "Clarify",
            "system_prompt": "system",
            "retrieve_context": lambda *args, **kwargs: [],
        },
    )

    _response, _delay, metadata = service.generate_response(
        "What should I learn for backend jobs?",
        conversation_history=[],
        user_context={"skills": ["Python"]},
    )

    assert metadata["error_code"] == "no_retrieval_context"
    assert metadata["no_retrieval_context"] is True
    assert metadata["retrieved_documents"] == []


@pytest.mark.django_db
def test_chat_response_surfaces_citations_and_flag(api_client, advisory_user, monkeypatch):
    """Task 2.2: the chat endpoint lifts citations + no-context flag to the top level."""
    api_client.force_authenticate(user=advisory_user)

    class StubLLMService:
        def build_user_context(self, user):
            return {"name": user.full_name, "skills": []}

        def generate_response(self, message, conversation_history=None, user_context=None):
            return (
                "Backend roles pay well in Egypt.",
                0.3,
                {
                    "source": "llm",
                    "fallback_used": False,
                    "no_retrieval_context": False,
                    "retrieved_documents": [
                        {
                            "source": "bls_ooh",
                            "url": "https://www.bls.gov/ooh/example.htm",
                            "section": "Pay",
                            "excerpt": "Backend engineers earn competitive salaries.",
                            "confidence_tier": "HIGH",
                        }
                    ],
                    "context_used": {"retrieved_documents": []},
                },
            )

    monkeypatch.setattr(
        "apps.advisory.llm_service.get_llm_service",
        lambda: StubLLMService(),
    )

    response = api_client.post(
        "/api/v1/advisory/chat/",
        {"message": "What do backend engineers earn?"},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data["no_retrieval_context"] is False
    assert isinstance(response.data["retrieved_documents"], list)
    citation = response.data["retrieved_documents"][0]
    assert set(citation.keys()) == {"source", "url", "section", "excerpt", "confidence_tier"}
    assert citation["source"] == "bls_ooh"


@pytest.mark.django_db
def test_conversation_create_is_not_exposed(api_client, advisory_user):
    api_client.force_authenticate(user=advisory_user)

    response = api_client.post(
        "/api/v1/advisory/history/",
        {
            "user": str(advisory_user.id),
            "title": "Injected conversation",
            "topic": "career",
        },
        format="json",
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
