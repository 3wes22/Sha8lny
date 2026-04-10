"""
LLM advisory orchestration for the Django backend.

This module uses the shared Gemma runtime and the local `rag` package when it
is available as an installed dependency. It intentionally avoids direct
`sys.path` manipulation.
"""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple

from apps.core.ai_logging import build_ai_metadata
from apps.core.gemma_client import GemmaClient
from apps.roadmaps.models import Roadmap


logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 6
MAX_RETRIEVED_DOCS = 4
MAX_DOC_CHARS = 280
MAX_CONTEXT_CHARS = 1600

DEFAULT_SYSTEM_PROMPT = (
    "You are Sha8alny's career advisory assistant. Give concise, practical "
    "career guidance grounded in the supplied user context and retrieved "
    "knowledge snippets. Stay focused on careers, learning strategy, roadmaps, "
    "and job search decisions."
)


def calculate_delay(response_text: str) -> float:
    char_count = len(response_text or "")
    delay = char_count / 100
    return max(0.5, min(delay, 3.0))


def get_rag_runtime() -> Optional[Dict[str, Callable[..., Any] | str]]:
    """Load the installed `rag` package lazily."""
    try:
        scope_rules = import_module("rag.scope_rules")
        retriever = import_module("rag.retriever")
    except ImportError as error:
        logger.warning("RAG package not available: %s", error)
        return None

    return {
        "classify_message": scope_rules.classify_message,
        "get_redirect_response": scope_rules.get_redirect_response,
        "get_clarifying_question": scope_rules.get_clarifying_question,
        "system_prompt": getattr(scope_rules, "SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT),
        "retrieve_context": getattr(retriever, "retrieve_context", None),
    }


class LLMAdvisoryService:
    """Synchronous advisory orchestration on top of the shared AI runtime."""

    SCOPE_VERSION = "advisory-scope-v1"
    RUNTIME_VERSION = "advisory-gemma-v1"
    FALLBACK_VERSION = "advisory-fallback-v1"

    @property
    def is_available(self) -> bool:
        return get_rag_runtime() is not None

    def _bound_history(self, conversation_history: Optional[list]) -> List[Dict[str, str]]:
        history = conversation_history or []
        bounded = history[-MAX_HISTORY_MESSAGES:]
        return [
            {
                "role": str(item.get("role") or ""),
                "content": str(item.get("content") or "").strip()[:300],
            }
            for item in bounded
            if isinstance(item, dict) and str(item.get("content") or "").strip()
        ]

    def _normalize_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        total_chars = 0

        for document in documents[:MAX_RETRIEVED_DOCS]:
            if not isinstance(document, dict):
                continue
            content = str(document.get("content") or "").strip()
            if not content:
                continue

            excerpt = content[:MAX_DOC_CHARS]
            if total_chars + len(excerpt) > MAX_CONTEXT_CHARS:
                break

            metadata = document.get("metadata") if isinstance(document.get("metadata"), dict) else {}
            normalized.append(
                {
                    "source": str(metadata.get("category") or "general"),
                    "topic": str(metadata.get("topic") or "").strip(),
                    "score": float(document.get("score") or 0),
                    "excerpt": excerpt,
                }
            )
            total_chars += len(excerpt)

        return normalized

    def _format_documents(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return ""

        sections = []
        for index, document in enumerate(documents, start=1):
            topic = f": {document['topic']}" if document.get("topic") else ""
            sections.append(f"{index}. [{document['source']}{topic}] {document['excerpt']}")
        return "\n".join(sections)

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        if not history:
            return ""

        return "\n".join(
            f"{'User' if item['role'] == 'user' else 'Advisor'}: {item['content']}"
            for item in history
        )

    def _format_user_context(self, user_context: Dict[str, Any]) -> str:
        sections: List[str] = []
        profile_lines: List[str] = []

        if user_context.get("name"):
            profile_lines.append(f"Name: {user_context['name']}")
        if user_context.get("career_goal"):
            profile_lines.append(f"Career goal: {user_context['career_goal']}")
        if user_context.get("current_job_title"):
            profile_lines.append(f"Current role: {user_context['current_job_title']}")
        if user_context.get("skills"):
            profile_lines.append(f"Skills: {', '.join(user_context['skills'][:5])}")
        if profile_lines:
            sections.append("### User Profile\n" + "\n".join(profile_lines))

        assessment_summary = user_context.get("latest_assessment")
        if isinstance(assessment_summary, dict):
            sections.append(
                "### Latest Assessment\n"
                f"Target career: {assessment_summary.get('target_career') or 'Not set'}\n"
                f"Strengths: {', '.join(assessment_summary.get('strengths', [])[:3]) or 'Not available'}\n"
                f"Gaps: {', '.join(assessment_summary.get('gaps', [])[:3]) or 'Not available'}"
            )

        active_roadmap = user_context.get("active_roadmap")
        if isinstance(active_roadmap, dict):
            sections.append(
                "### Active Roadmap\n"
                f"Target career: {active_roadmap.get('target_career') or 'Not set'}\n"
                f"Current level: {active_roadmap.get('current_level') or 'Not set'}\n"
                f"Target level: {active_roadmap.get('target_level') or 'Not set'}\n"
                f"Next focus: {active_roadmap.get('next_focus') or 'Not available'}"
            )

        return "\n\n".join(sections)

    def _build_prompt(
        self,
        *,
        message: str,
        history: List[Dict[str, str]],
        user_context: Dict[str, Any],
        retrieved_documents: List[Dict[str, Any]],
    ) -> str:
        sections = []
        user_context_block = self._format_user_context(user_context)
        if user_context_block:
            sections.append(user_context_block)

        if history:
            sections.append("### Recent Conversation\n" + self._format_history(history))

        if retrieved_documents:
            sections.append("### Retrieved Knowledge\n" + self._format_documents(retrieved_documents))

        sections.append(f"### User Message\n{message}")
        return "\n\n".join(sections)

    def _scope_response(
        self,
        *,
        message: str,
        runtime: Optional[Dict[str, Callable[..., Any] | str]],
        classification: str,
        context_used: Dict[str, Any],
    ) -> Tuple[str, float, Dict[str, Any]]:
        if classification == "coding_redirect":
            if runtime and callable(runtime.get("get_redirect_response")):
                response_text = runtime["get_redirect_response"](message)  # type: ignore[index]
            else:
                response_text = (
                    "I focus on career guidance rather than coding implementation. "
                    "Tell me what role you want, and I can help you learn that skill for the job."
                )
        else:
            if runtime and callable(runtime.get("get_clarifying_question")):
                response_text = runtime["get_clarifying_question"]()  # type: ignore[index]
            else:
                response_text = "Tell me a bit more about the career or learning decision you want help with."

        metadata = build_ai_metadata(
            source="scope_filter",
            processing_time_ms=0,
            model=None,
            provider="sha8alny",
            version=self.SCOPE_VERSION,
            fallback_used=True,
        ).to_dict()
        metadata["context_used"] = context_used
        return response_text, calculate_delay(response_text), metadata

    def _fallback_response(
        self,
        *,
        message: str,
        context_used: Dict[str, Any],
        error_code: str,
    ) -> Tuple[str, float, Dict[str, Any]]:
        message_lower = message.lower()

        if any(word in message_lower for word in ["career", "job", "work", "hire"]):
            response_text = (
                "Start by choosing one target role, comparing it with your current skills, "
                "then turning the biggest gaps into a short project-based learning plan. "
                "If you want, ask about one specific role and I’ll help you break it down."
            )
        elif any(word in message_lower for word in ["learn", "study", "course", "skill", "roadmap"]):
            response_text = (
                "Focus on one marketable skill area, build a small proof-of-work project, "
                "and use job postings to decide what to learn next. If you name the role or "
                "skill you want, I can help you sequence the next steps."
            )
        else:
            response_text = (
                "I can help with career planning, learning strategy, roadmap decisions, and "
                "job-search questions. Ask about a specific role, skill gap, or next step and "
                "I’ll keep it practical."
            )

        metadata = build_ai_metadata(
            source="fallback",
            processing_time_ms=0,
            model=None,
            provider="sha8alny",
            version=self.FALLBACK_VERSION,
            fallback_used=True,
            error_code=error_code,
        ).to_dict()
        metadata["context_used"] = context_used
        return response_text, calculate_delay(response_text), metadata

    def generate_response(
        self,
        message: str,
        conversation_history: Optional[list] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, float, Dict[str, Any]]:
        runtime = get_rag_runtime()
        user_context = user_context or {}
        bounded_history = self._bound_history(conversation_history)
        context_used: Dict[str, Any] = {
            "history_window": len(bounded_history),
            "profile": {
                "name": user_context.get("name"),
                "career_goal": user_context.get("career_goal") or user_context.get("target_career"),
                "skills": user_context.get("skills", [])[:5],
            },
            "assessment_summary": user_context.get("latest_assessment"),
            "active_roadmap": user_context.get("active_roadmap"),
            "retrieved_documents": [],
        }

        if runtime and callable(runtime.get("classify_message")):
            classification, _ = runtime["classify_message"](message)  # type: ignore[index]
        else:
            classification = "in_scope" if any(
                token in message.lower()
                for token in ("career", "job", "learn", "skill", "roadmap", "interview", "resume")
            ) else "unclear"

        if classification in {"coding_redirect", "unclear", "out_of_scope"}:
            return self._scope_response(
                message=message,
                runtime=runtime,
                classification=classification,
                context_used=context_used,
            )

        if not runtime or not callable(runtime.get("retrieve_context")):
            return self._fallback_response(
                message=message,
                context_used=context_used,
                error_code="rag_unavailable",
            )

        try:
            raw_documents = runtime["retrieve_context"](  # type: ignore[index]
                message,
                top_k=MAX_RETRIEVED_DOCS,
            )
        except Exception as error:
            logger.warning("Advisory retrieval failed: %s", error)
            return self._fallback_response(
                message=message,
                context_used=context_used,
                error_code="retrieval_failed",
            )

        retrieved_documents = self._normalize_documents(raw_documents or [])
        context_used["retrieved_documents"] = retrieved_documents
        if not retrieved_documents:
            return self._fallback_response(
                message=message,
                context_used=context_used,
                error_code="no_retrieval_context",
            )

        prompt = self._build_prompt(
            message=message,
            history=bounded_history,
            user_context=user_context,
            retrieved_documents=retrieved_documents,
        )

        try:
            result = GemmaClient().generate_text(
                prompt=prompt,
                system=str(runtime.get("system_prompt") or DEFAULT_SYSTEM_PROMPT),
            )
            response_text = result.text or (
                "I’m missing enough signal to answer well. Ask about a specific role, roadmap choice, or job-search step."
            )
            metadata = build_ai_metadata(
                source="llm",
                processing_time_ms=result.metadata.processing_time_ms,
                model=result.metadata.model,
                provider=result.metadata.provider,
                version=self.RUNTIME_VERSION,
                trace_id=result.metadata.trace_id,
            ).to_dict()
            metadata.update(
                {
                    "prompt_tokens": result.prompt_tokens,
                    "completion_tokens": result.completion_tokens,
                    "tokens_used": result.prompt_tokens + result.completion_tokens,
                    "context_used": context_used,
                }
            )
            return response_text, calculate_delay(response_text), metadata
        except Exception as error:
            logger.warning("Advisory generation failed: %s", error)
            return self._fallback_response(
                message=message,
                context_used=context_used,
                error_code=type(error).__name__,
            )

    def build_user_context(self, user) -> Dict[str, Any]:
        context = {
            "name": getattr(user, "full_name", "") or user.email.split("@")[0],
        }

        if hasattr(user, "current_job_title"):
            context["current_job_title"] = user.current_job_title or ""

        if hasattr(user, "career_goal"):
            context["career_goal"] = user.career_goal or ""

        try:
            from apps.users.models import UserSkill

            user_skills = UserSkill.objects.filter(
                user=user,
                is_deleted=False,
            ).select_related("skill").values_list("skill__name", flat=True)[:5]
            context["skills"] = list(user_skills)
        except Exception:
            context["skills"] = []

        try:
            from apps.assessments.models import AssessmentResult

            latest_result = AssessmentResult.objects.select_related("assessment").filter(
                assessment__user=user,
                is_deleted=False,
            ).order_by("-created_at").first()
            if latest_result:
                target_career = (
                    getattr(latest_result.assessment, "target_career", "") or ""
                ).strip()
                context["latest_assessment"] = {
                    "id": str(latest_result.id),
                    "target_career": target_career,
                    "strengths": list(latest_result.strengths[:3]),
                    "gaps": list(latest_result.areas_for_improvement[:3]),
                }
                if target_career and not context.get("career_goal"):
                    context["target_career"] = target_career
        except Exception:
            pass

        try:
            active_roadmap = Roadmap.objects.filter(
                user=user,
                is_deleted=False,
                status__in=[Roadmap.ACTIVE, Roadmap.IN_PROGRESS, Roadmap.DRAFT],
            ).order_by("-updated_at").first()
            if active_roadmap:
                next_focus = None
                if isinstance(active_roadmap.ai_insights, dict):
                    next_focus = active_roadmap.ai_insights.get("summary")
                context["active_roadmap"] = {
                    "id": str(active_roadmap.id),
                    "target_career": active_roadmap.target_career,
                    "current_level": active_roadmap.current_level,
                    "target_level": active_roadmap.target_level,
                    "next_focus": next_focus,
                }
        except Exception:
            pass

        return context


_llm_service = None


def get_llm_service() -> LLMAdvisoryService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMAdvisoryService()
    return _llm_service
