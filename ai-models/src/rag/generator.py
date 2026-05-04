"""
LLM generator for career advisory.

Uses the hosted Gemini API for demo-friendly inference.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import httpx

from .retriever import get_relevant_context
from .runtime_settings import (
    get_gemini_api_base_url,
    get_gemini_api_key,
    get_gemini_flash_model,
    get_llm_temperature,
    get_llm_timeout_seconds,
)
from .scope_rules import (
    SYSTEM_PROMPT,
    classify_message,
    get_clarifying_question,
    get_redirect_response,
)


logger = logging.getLogger(__name__)


MIN_DELAY_SECONDS = 0.5
MAX_DELAY_SECONDS = 3.0
CHARS_PER_SECOND = 100
DEFAULT_MAX_TOKENS = 512


def has_gemini_api_key() -> bool:
    """Return whether a Gemini API key is configured."""
    return bool(str(get_gemini_api_key() or "").strip())


def generate_with_gemini(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Generate a response using the hosted Gemini API.
    """
    api_key = str(get_gemini_api_key() or "").strip()
    if not api_key:
        raise ConnectionError("GEMINI_API_KEY is not configured.")

    base_url = get_gemini_api_base_url().rstrip("/")
    model = model or get_gemini_flash_model()
    temperature = get_llm_temperature() if temperature is None else temperature
    timeout_seconds = get_llm_timeout_seconds()

    response = httpx.post(
        f"{base_url}/models/{model}:generateContent?key={api_key}",
        json={
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "systemInstruction": {
                "role": "system",
                "parts": [{"text": system}],
            },
            "generationConfig": {
                "temperature": temperature,
                "candidateCount": 1,
                "maxOutputTokens": max_tokens,
            },
        },
        timeout=timeout_seconds,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Gemini API error: {response.status_code} {response.text.strip()}"
        )

    result = response.json()
    candidates = result.get("candidates", []) if isinstance(result, dict) else []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content") if isinstance(candidate.get("content"), dict) else {}
        parts = content.get("parts") if isinstance(content.get("parts"), list) else []
        for part in parts:
            if isinstance(part, dict) and str(part.get("text") or "").strip():
                return str(part.get("text") or "").strip()

    raise RuntimeError("Gemini returned an empty response")


def calculate_delay(response_text: str) -> float:
    """
    Calculate a variable delay based on response length.
    """
    char_count = len(response_text)
    delay = char_count / CHARS_PER_SECOND
    return max(MIN_DELAY_SECONDS, min(delay, MAX_DELAY_SECONDS))


def build_prompt_with_context(
    user_message: str,
    rag_context: str,
    conversation_history: Optional[list] = None,
    user_profile: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Build the full prompt including context and conversation history.
    """
    prompt_parts = []

    if user_profile:
        profile_summary = format_user_profile(user_profile)
        if profile_summary:
            prompt_parts.append(f"### User Profile\n{profile_summary}\n")

    if rag_context and rag_context != "No specific context available.":
        prompt_parts.append(f"### Relevant Knowledge\n{rag_context}\n")

    if conversation_history:
        history_text = format_conversation_history(conversation_history[-6:])
        if history_text:
            prompt_parts.append(f"### Conversation History\n{history_text}\n")

    prompt_parts.append(f"### User Message\n{user_message}")

    return "\n".join(prompt_parts)


def format_user_profile(profile: Dict[str, Any]) -> str:
    """Format user profile for prompt context."""
    parts = []

    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")
    if profile.get("current_job_title"):
        parts.append(f"Current Role: {profile['current_job_title']}")
    if profile.get("career_goal"):
        parts.append(f"Career Goal: {profile['career_goal']}")
    if profile.get("skills"):
        skills = profile["skills"][:5]
        parts.append(f"Skills: {', '.join(skills)}")

    return "\n".join(parts)


def format_conversation_history(messages: list) -> str:
    """Format recent messages for prompt context."""
    if not messages:
        return ""

    formatted = []
    for msg in messages:
        role = "User" if msg.get("role") == "user" else "Advisor"
        content = msg.get("content", "")[:200]
        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)


def generate_response(
    user_message: str,
    conversation_history: Optional[list] = None,
    user_profile: Optional[Dict[str, Any]] = None,
    use_rag: bool = True,
) -> Tuple[str, float]:
    """
    Generate a career advisory response.
    """
    classification, _ = classify_message(user_message)

    if classification == "unclear":
        response = get_clarifying_question()
        return response, calculate_delay(response)

    if classification == "coding_redirect":
        response = get_redirect_response(user_message)
        return response, calculate_delay(response)

    rag_context = ""
    if use_rag:
        try:
            rag_context = get_relevant_context(user_message)
        except Exception as error:
            logger.warning("RAG retrieval failed: %s", error)
            rag_context = ""

    full_prompt = build_prompt_with_context(
        user_message=user_message,
        rag_context=rag_context,
        conversation_history=conversation_history,
        user_profile=user_profile,
    )

    try:
        response = generate_with_gemini(full_prompt)
    except ConnectionError as error:
        response = (
            "I apologize, but I'm currently unable to generate a response. "
            "The hosted Gemini API is not configured. Please set GEMINI_API_KEY "
            "and try again."
        )
        logger.error("Gemini unavailable: %s", error)
    except RuntimeError as error:
        response = (
            "I encountered an issue generating a response. Please try rephrasing "
            "your question or try again in a moment."
        )
        logger.error("Generation error: %s", error)

    delay = calculate_delay(response)
    return response, delay


FALLBACK_RESPONSES = {
    "career_path": (
        "To plan your career path effectively:\n\n"
        "1. **Identify your goal role** - Research what skills and experience it requires\n"
        "2. **Assess your current position** - What skills do you have? What gaps exist?\n"
        "3. **Create a learning roadmap** - Break down skills into 3-6 month milestones\n"
        "4. **Build portfolio projects** - Demonstrate your skills practically\n"
        "5. **Network actively** - Connect with people in your target role\n\n"
        "Would you like me to help you with any of these steps specifically?"
    ),
    "learning": (
        "Here's how to approach learning for a job:\n\n"
        "1. **Focus on one technology deeply** before branching out\n"
        "2. **Build projects, not just follow tutorials** - Apply what you learn\n"
        "3. **Learn what companies actually use** - Check job postings for your target role\n"
        "4. **Practice coding problems** - LeetCode medium level is job-interview standard\n"
        "5. **Join communities** - Learn from and with others\n\n"
        "What specific skill or technology are you interested in learning?"
    ),
    "default": (
        "I'd be happy to help with your career question! I can assist with:\n\n"
        "- Career path planning and transitions\n"
        "- Learning roadmaps for tech skills\n"
        "- Job search and interview preparation\n"
        "- Egyptian tech market insights\n"
        "- Resume and portfolio advice\n\n"
        "What would you like to focus on?"
    ),
}


def get_fallback_response(user_message: str) -> str:
    """Get a fallback response when hosted inference is unavailable."""
    message_lower = user_message.lower()

    if any(word in message_lower for word in ["career", "path", "become", "transition"]):
        return FALLBACK_RESPONSES["career_path"]
    if any(word in message_lower for word in ["learn", "study", "course", "skill"]):
        return FALLBACK_RESPONSES["learning"]
    return FALLBACK_RESPONSES["default"]
