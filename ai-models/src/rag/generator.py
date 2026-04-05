"""
LLM Generator for Career Advisory

Integrates with Ollama for local Mistral 7B inference.
Handles response generation with RAG context and scope filtering.
"""

import time
import requests
from typing import Optional, Dict, Any, Tuple
import logging

from .scope_rules import (
    SYSTEM_PROMPT,
    classify_message,
    get_redirect_response,
    get_clarifying_question,
)
from .retriever import get_relevant_context

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "mistral"

# Response timing (variable delay based on length)
MIN_DELAY_SECONDS = 0.5
MAX_DELAY_SECONDS = 3.0
CHARS_PER_SECOND = 100  # Simulated typing speed

# Model parameters
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1024


# ============================================================================
# OLLAMA CLIENT
# ============================================================================

def check_ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/version", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def check_model_available(model: str = DEFAULT_MODEL) -> bool:
    """Check if the specified model is downloaded."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(m.get("name", "").startswith(model) for m in models)
        return False
    except requests.exceptions.RequestException:
        return False


def generate_with_ollama(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Generate response using Ollama API.
    
    Args:
        prompt: User message with context
        system: System prompt
        model: Model name (default: mistral)
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum response length
        
    Returns:
        Generated response text
        
    Raises:
        ConnectionError: If Ollama is not available
        RuntimeError: If generation fails
    """
    if not check_ollama_available():
        raise ConnectionError(
            "Ollama server is not running. Start it with: ollama serve"
        )
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            },
            timeout=120  # 2 minute timeout for generation
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        return result.get("response", "").strip()
        
    except requests.exceptions.Timeout:
        raise RuntimeError("Response generation timed out")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama request failed: {e}")


# ============================================================================
# RESPONSE GENERATION
# ============================================================================

def calculate_delay(response_text: str) -> float:
    """
    Calculate variable delay based on response length.
    Simulates natural typing/thinking time.
    """
    char_count = len(response_text)
    delay = char_count / CHARS_PER_SECOND
    
    # Clamp to min/max
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
    
    # Add user profile context if available
    if user_profile:
        profile_summary = format_user_profile(user_profile)
        if profile_summary:
            prompt_parts.append(f"### User Profile\n{profile_summary}\n")
    
    # Add RAG context
    if rag_context and rag_context != "No specific context available.":
        prompt_parts.append(f"### Relevant Knowledge\n{rag_context}\n")
    
    # Add conversation history (last 3 exchanges)
    if conversation_history:
        history_text = format_conversation_history(conversation_history[-6:])  # Last 3 exchanges
        if history_text:
            prompt_parts.append(f"### Conversation History\n{history_text}\n")
    
    # Add current message
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
        skills = profile["skills"][:5]  # Top 5 skills
        parts.append(f"Skills: {', '.join(skills)}")
    
    return "\n".join(parts)


def format_conversation_history(messages: list) -> str:
    """Format recent messages for prompt context."""
    if not messages:
        return ""
    
    formatted = []
    for msg in messages:
        role = "User" if msg.get("role") == "user" else "Advisor"
        content = msg.get("content", "")[:200]  # Truncate long messages
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
    
    Args:
        user_message: The user's question
        conversation_history: Previous messages in conversation
        user_profile: User's profile data (optional)
        use_rag: Whether to retrieve context from knowledge base
        
    Returns:
        (response_text, delay_seconds)
    """
    # Step 1: Classify the message
    classification, hint = classify_message(user_message)
    
    # Step 2: Handle based on classification
    if classification == "unclear":
        # Return clarifying question
        response = get_clarifying_question()
        return response, calculate_delay(response)
    
    if classification == "coding_redirect":
        # Redirect to career-focused response
        response = get_redirect_response(user_message)
        return response, calculate_delay(response)
    
    # Step 3: Get RAG context for in-scope questions
    rag_context = ""
    if use_rag:
        try:
            rag_context = get_relevant_context(user_message)
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            rag_context = ""
    
    # Step 4: Build full prompt
    full_prompt = build_prompt_with_context(
        user_message=user_message,
        rag_context=rag_context,
        conversation_history=conversation_history,
        user_profile=user_profile,
    )
    
    # Step 5: Generate response with Ollama
    try:
        response = generate_with_ollama(full_prompt)
    except ConnectionError as e:
        # Ollama not available - return helpful error
        response = (
            "I apologize, but I'm currently unable to generate a response. "
            "The AI system is temporarily unavailable. Please try again in a moment, "
            "or check that Ollama is running on your system."
        )
        logger.error(f"Ollama unavailable: {e}")
    except RuntimeError as e:
        response = (
            "I encountered an issue generating a response. Please try rephrasing "
            "your question or try again in a moment."
        )
        logger.error(f"Generation error: {e}")
    
    # Step 6: Calculate delay
    delay = calculate_delay(response)
    
    return response, delay


# ============================================================================
# FALLBACK RESPONSES (When Ollama is unavailable)
# ============================================================================

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
    """Get a fallback response when LLM is unavailable."""
    message_lower = user_message.lower()
    
    if any(word in message_lower for word in ["career", "path", "become", "transition"]):
        return FALLBACK_RESPONSES["career_path"]
    elif any(word in message_lower for word in ["learn", "study", "course", "skill"]):
        return FALLBACK_RESPONSES["learning"]
    else:
        return FALLBACK_RESPONSES["default"]


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("Testing LLM Generator...\n")
    
    # Check Ollama status
    print(f"Ollama available: {check_ollama_available()}")
    print(f"Mistral model available: {check_model_available()}")
    
    if check_ollama_available() and check_model_available():
        # Test generation
        test_messages = [
            "How do I become a backend developer?",
            "How to implement recursion?",  # Should redirect
            "help",  # Should clarify
        ]
        
        for msg in test_messages:
            print(f"\n{'='*50}")
            print(f"User: {msg}")
            response, delay = generate_response(msg)
            print(f"Response ({delay:.1f}s delay):\n{response}")
    else:
        print("\nOllama not available. Using fallback response:")
        response = get_fallback_response("How do I become a developer?")
        print(response)
