"""
Shared runtime settings for the RAG support package.

When the package runs inside the Django backend, prefer the backend's canonical
AI settings module so `Backend/.env` remains the single source of truth. When
the package runs standalone, fall back to process environment variables.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_AI_PROVIDER = "gemini"
DEFAULT_GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_GEMINI_FLASH_LITE_MODEL = "gemini-2.5-flash-lite"
DEFAULT_GEMINI_FLASH_MODEL = "gemini-2.5-flash"
DEFAULT_LLM_TIMEOUT_SECONDS = 60
DEFAULT_LLM_TEMPERATURE = 0.2
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CHROMA_PERSIST_DIR = (
    Path(__file__).resolve().parent.parent.parent / "data" / "vector_db"
)


def _load_backend_ai_settings() -> Any | None:
    try:
        from apps.core import ai_settings
    except Exception:
        return None
    return ai_settings


def get_ai_provider() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.AI_PROVIDER
    return os.getenv("AI_PROVIDER", DEFAULT_AI_PROVIDER)


def get_gemini_api_key() -> str:
    keys = get_gemini_api_keys()
    return keys[0] if keys else ""


def get_gemini_api_keys() -> list[str]:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return list(getattr(backend_settings, "GEMINI_API_KEYS", []) or [])
    single = os.getenv("GEMINI_API_KEY", "").strip()
    return [single] if single else []


def get_gemini_api_base_url() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.GEMINI_API_BASE_URL
    return os.getenv("GEMINI_API_BASE_URL", DEFAULT_GEMINI_API_BASE_URL)


def get_gemini_flash_lite_model() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.GEMINI_FLASH_LITE_MODEL
    return os.getenv("GEMINI_FLASH_LITE_MODEL", DEFAULT_GEMINI_FLASH_LITE_MODEL)


def get_gemini_flash_model() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.GEMINI_FLASH_MODEL
    return os.getenv("GEMINI_FLASH_MODEL", DEFAULT_GEMINI_FLASH_MODEL)


def get_llm_timeout_seconds() -> int:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return int(backend_settings.LLM_TIMEOUT_SECONDS)
    return int(os.getenv("LLM_TIMEOUT_SECONDS", DEFAULT_LLM_TIMEOUT_SECONDS))


def get_llm_temperature() -> float:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return float(backend_settings.LLM_TEMPERATURE)
    return float(os.getenv("LLM_TEMPERATURE", DEFAULT_LLM_TEMPERATURE))


def get_embedding_model() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.EMBEDDING_MODEL
    return os.getenv("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)


def get_chroma_persist_dir() -> Path:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None and getattr(backend_settings, "CHROMA_PERSIST_DIR", ""):
        return Path(str(backend_settings.CHROMA_PERSIST_DIR)).expanduser()

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "").strip()
    if persist_dir:
        return Path(persist_dir).expanduser()

    return DEFAULT_CHROMA_PERSIST_DIR
