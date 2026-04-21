"""
Shared runtime settings for the local RAG package.

When the package runs inside the Django backend, prefer the backend's
canonical AI settings module so `Backend/.env` remains the single source of
truth. When the package runs standalone, fall back to process environment
variables and safe local defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:e2b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 60
DEFAULT_OLLAMA_TEMPERATURE = 0.3
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CHROMA_PERSIST_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "vector_db"


def _load_backend_ai_settings() -> Any | None:
    try:
        from apps.core import ai_settings
    except Exception:
        return None
    return ai_settings


def get_ollama_base_url() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.OLLAMA_HOST
    return os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_BASE_URL)


def get_ollama_model() -> str:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return backend_settings.OLLAMA_MODEL
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


def get_ollama_timeout_seconds() -> int:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return int(backend_settings.OLLAMA_TIMEOUT_SECONDS)
    return int(os.getenv("OLLAMA_TIMEOUT_SECONDS", DEFAULT_OLLAMA_TIMEOUT_SECONDS))


def get_ollama_temperature() -> float:
    backend_settings = _load_backend_ai_settings()
    if backend_settings is not None:
        return float(backend_settings.OLLAMA_TEMPERATURE)
    return float(os.getenv("OLLAMA_TEMPERATURE", DEFAULT_OLLAMA_TEMPERATURE))


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
