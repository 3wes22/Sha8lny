"""
Health-check helpers for the active AI runtime.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from apps.core.ai_settings import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_FLASH_LITE_MODEL,
    GEMINI_FLASH_MODEL,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    get_ai_settings_summary,
    get_gemini_generate_url,
)


_GEMINI_PROBE_CACHE: Optional[dict[str, Any]] = None
_GEMINI_PROBE_CACHE_AT: float = 0.0
_GEMINI_PROBE_CACHE_TTL_SECONDS = 60.0


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


def check_gemini_live(timeout_seconds: int = 3) -> dict[str, Any]:
    """Probe hosted Gemini with a minimal generateContent call.

    Returns:
        dict with keys: reachable (bool), model (str), latency_ms (int), error (str|None)
    """
    global _GEMINI_PROBE_CACHE, _GEMINI_PROBE_CACHE_AT

    now = time.monotonic()
    if (
        _GEMINI_PROBE_CACHE is not None
        and (now - _GEMINI_PROBE_CACHE_AT) < _GEMINI_PROBE_CACHE_TTL_SECONDS
    ):
        return dict(_GEMINI_PROBE_CACHE)

    model = GEMINI_FLASH_LITE_MODEL
    result: dict[str, Any] = {
        "reachable": False,
        "model": model,
        "latency_ms": 0,
        "error": None,
    }

    if not GEMINI_API_KEY:
        result["error"] = "GEMINI_API_KEY not configured"
        _GEMINI_PROBE_CACHE = dict(result)
        _GEMINI_PROBE_CACHE_AT = now
        return result

    url = get_gemini_generate_url(model)
    body = {
        "contents": [{"parts": [{"text": "Reply with exactly: ok"}]}],
        "generationConfig": {
            "temperature": 0.0,
            "maxOutputTokens": 8,
        },
    }

    started = time.monotonic()
    try:
        response = httpx.post(
            f"{url}?key={GEMINI_API_KEY}",
            json=body,
            timeout=timeout_seconds,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        result["latency_ms"] = latency_ms

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
        else:
            payload = response.json()
            candidates = payload.get("candidates", []) if isinstance(payload, dict) else []
            if candidates:
                result["reachable"] = True
            else:
                result["error"] = "empty candidates in response"
    except httpx.HTTPError as error:
        result["latency_ms"] = int((time.monotonic() - started) * 1000)
        result["error"] = str(error)

    _GEMINI_PROBE_CACHE = dict(result)
    _GEMINI_PROBE_CACHE_AT = now
    return result


def reset_gemini_probe_cache() -> None:
    """Clear cached Gemini probe result (for tests)."""
    global _GEMINI_PROBE_CACHE, _GEMINI_PROBE_CACHE_AT
    _GEMINI_PROBE_CACHE = None
    _GEMINI_PROBE_CACHE_AT = 0.0


def get_ai_runtime_health() -> dict[str, Any]:
    if AI_PROVIDER == "gemini":
        provider_available = bool(GEMINI_API_KEY)
        model_available = bool(GEMINI_FLASH_LITE_MODEL and GEMINI_FLASH_MODEL)
        gemini_probe = check_gemini_live() if provider_available else {
            "reachable": False,
            "model": GEMINI_FLASH_LITE_MODEL,
            "latency_ms": 0,
            "error": "GEMINI_API_KEY not configured",
        }
    else:
        provider_available = check_ollama_available()
        model_available = check_model_available()
        gemini_probe = None

    health: dict[str, Any] = {
        "runtime": AI_PROVIDER,
        "provider_available": provider_available,
        "model_available": model_available,
        "settings": get_ai_settings_summary(),
    }
    if gemini_probe is not None:
        health["gemini_live"] = gemini_probe
        health["provider_reachable"] = bool(gemini_probe.get("reachable"))
    else:
        health["provider_reachable"] = provider_available and model_available

    return health
