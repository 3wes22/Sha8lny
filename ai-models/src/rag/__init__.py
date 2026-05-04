"""
RAG (Retrieval-Augmented Generation) Module for Career Advisory

Components:
- embeddings: Text embedding using sentence-transformers
- vector_store: ChromaDB vector database
- retriever: Context retrieval for queries
- generator: LLM response generation with Gemini
- scope_rules: Topic classification and system prompts
- seeder: Knowledge base population
"""

from .generator import generate_response, has_gemini_api_key
from .retriever import get_relevant_context
from . import runtime_settings
from .scope_rules import classify_message, SYSTEM_PROMPT
from .seeder import seed_database

__all__ = [
    "generate_response",
    "has_gemini_api_key",
    "get_relevant_context",
    "runtime_settings",
    "classify_message",
    "SYSTEM_PROMPT",
    "seed_database",
]
