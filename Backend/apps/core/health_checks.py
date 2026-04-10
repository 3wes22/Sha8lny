"""
Health-check helpers for the local AI runtime.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.core.ai_settings import OLLAMA_HOST, OLLAMA_MODEL, get_ai_settings_summary


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
    return {
        "runtime": "ollama",
        "ollama_available": check_ollama_available(),
        "model_available": check_model_available(),
        "settings": get_ai_settings_summary(),
    }
