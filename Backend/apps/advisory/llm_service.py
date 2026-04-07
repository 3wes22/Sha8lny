"""
LLM Advisory Service for Django Backend

This module bridges the Django advisory app with the ai-models RAG system.
It provides a clean interface for generating career advisory responses.
"""

import sys
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

from apps.core.ai_contracts import AIInvocationMetadata

# Add ai-models to path for imports
AI_MODELS_PATH = Path(__file__).parent.parent.parent.parent.parent / "ai-models" / "src"
if str(AI_MODELS_PATH) not in sys.path:
    sys.path.insert(0, str(AI_MODELS_PATH))


def get_rag_module():
    """Lazy import of RAG module to avoid import errors if dependencies missing."""
    try:
        from rag import generate_response, check_ollama_available
        return generate_response, check_ollama_available
    except ImportError as e:
        logger.warning(f"RAG module not available: {e}")
        return None, None


class LLMAdvisoryService:
    """
    Service for generating AI-powered career advisory responses.
    
    Uses local LLM (Mistral 7B via Ollama) with RAG for context-aware responses.
    Handles scope filtering, fallbacks, and session management.
    """
    
    def __init__(self):
        self._rag_available = None
    
    @property
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        if self._rag_available is None:
            _, check_available = get_rag_module()
            if check_available:
                self._rag_available = check_available()
            else:
                self._rag_available = False
        return self._rag_available
    
    def generate_response(
        self,
        message: str,
        conversation_history: Optional[list] = None,
        user_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Generate an AI response to a user message.
        
        Args:
            message: User's message/question
            conversation_history: Previous messages in session
            user_context: User profile data (skills, goals, etc.)
            
        Returns:
            Tuple of (response_text, delay_seconds, metadata)
        """
        start_time = time.time()
        
        generate_response_func, _ = get_rag_module()
        
        if generate_response_func:
            try:
                response_text, delay = generate_response_func(
                    user_message=message,
                    conversation_history=conversation_history,
                    user_profile=user_context,
                    use_rag=True,
                )
                
                processing_time = time.time() - start_time

                metadata = AIInvocationMetadata(
                    source="llm",
                    processing_time_ms=int(processing_time * 1000),
                    model="mistral",
                    provider="ollama",
                    version="rag-local-v1",
                )
                return response_text, delay, {
                    **metadata.to_dict(),
                }
                
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                # Fall through to fallback
        
        # Fallback response
        return self._get_fallback_response(message)
    
    def _get_fallback_response(self, message: str) -> Tuple[str, float, Dict[str, Any]]:
        """Generate fallback response when LLM is unavailable."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["career", "job", "work", "hire"]):
            response = (
                "I'd be happy to help with your career question! Here are some key points:\n\n"
                "1. **Define your goal** - What specific role are you targeting?\n"
                "2. **Assess your skills** - What do you know? What gaps exist?\n"
                "3. **Create a plan** - Break learning into 3-6 month milestones\n"
                "4. **Build projects** - Practical experience matters most\n"
                "5. **Network actively** - Connect with people in your target field\n\n"
                "What specific aspect would you like to explore?"
            )
        elif any(word in message_lower for word in ["learn", "study", "course", "skill"]):
            response = (
                "Here's my advice for learning effectively:\n\n"
                "1. **Focus on one technology** before branching out\n"
                "2. **Build real projects** - Not just tutorials\n"
                "3. **Learn what companies use** - Check job postings\n"
                "4. **Practice coding problems** - LeetCode for interviews\n"
                "5. **Join communities** - Learn with others\n\n"
                "What technology are you interested in learning?"
            )
        else:
            response = (
                "Hello! I'm your career advisor. I can help you with:\n\n"
                "- **Career planning** - Choosing paths, transitions\n"
                "- **Skill development** - Learning roadmaps\n"
                "- **Job search** - Resumes, interviews, networking\n"
                "- **Egyptian tech market** - Companies, salaries, opportunities\n\n"
                "What would you like to discuss?"
            )
        
        delay = 1.0  # Fixed delay for fallback
        
        metadata = AIInvocationMetadata(
            source="fallback",
            processing_time_ms=0,
            model=None,
            provider="sha8alny",
            version="fallback-v1",
            fallback_used=True,
        )
        return response, delay, metadata.to_dict()
    
    def build_user_context(self, user) -> Dict[str, Any]:
        """
        Build user context from Django user instance.
        
        Args:
            user: Django User model instance
            
        Returns:
            Dict with user profile info for LLM context
        """
        context = {
            "name": getattr(user, 'full_name', '') or user.email.split('@')[0],
        }
        
        # Add profile fields if available
        if hasattr(user, 'current_job_title'):
            context["current_job_title"] = user.current_job_title or ''
        
        if hasattr(user, 'career_goal'):
            context["career_goal"] = user.career_goal or ''
        
        # Add skills if the user has them
        try:
            from apps.users.models import UserSkill
            user_skills = UserSkill.objects.filter(
                user=user, 
                is_deleted=False
            ).select_related('skill').values_list('skill__name', flat=True)[:5]
            context["skills"] = list(user_skills)
        except Exception:
            context["skills"] = []

        try:
            from apps.assessments.models import Assessment

            latest_assessment = Assessment.objects.filter(
                user=user,
                is_deleted=False,
            ).order_by("-created_at").first()
            if latest_assessment and latest_assessment.target_career:
                context["target_career"] = latest_assessment.target_career
        except Exception:
            pass

        try:
            from apps.roadmaps.models import Roadmap

            active_roadmap = Roadmap.objects.filter(
                user=user,
                is_deleted=False,
                status__in=[Roadmap.ACTIVE, Roadmap.IN_PROGRESS, Roadmap.DRAFT],
            ).order_by("-updated_at").first()
            if active_roadmap:
                context["active_roadmap"] = {
                    "id": str(active_roadmap.id),
                    "target_career": active_roadmap.target_career,
                    "current_level": active_roadmap.current_level,
                    "target_level": active_roadmap.target_level,
                }
        except Exception:
            pass
        
        return context


# Singleton instance
_llm_service = None


def get_llm_service() -> LLMAdvisoryService:
    """Get the LLM advisory service singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMAdvisoryService()
    return _llm_service
