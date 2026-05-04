"""
Health-check helpers for the active AI runtime.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.core.ai_settings import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_FLASH_LITE_MODEL,
    GEMINI_FLASH_MODEL,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    get_ai_settings_summary,
)


def check_ollama_available(host: str = OLLAMA_HOST) -> bool:
    try:
        response = httpx.get(f"{host.rstrip('/')}/api/version", timeout=2)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


def check_model_available(model: str = OLLAMA_MODEL, host: str = OLLAMA_HOST) -> bool:
    try:
        response = httpx.get(f"{host.rstrip('/')}/api/tags", timeout=5)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return False

    models = payload.get("models", []) if isinstance(payload, dict) else []
    return any(str(item.get("name", "")).startswith(model) for item in models if isinstance(item, dict))


def get_ai_runtime_health() -> dict[str, Any]:
    if AI_PROVIDER == "gemini":
        provider_available = bool(GEMINI_API_KEY)
        model_available = bool(GEMINI_FLASH_LITE_MODEL and GEMINI_FLASH_MODEL)
    else:
        provider_available = check_ollama_available()
        model_available = check_model_available()

    return {
        "runtime": AI_PROVIDER,
        "provider_available": provider_available,
        "model_available": model_available,
        "settings": get_ai_settings_summary(),
    }
