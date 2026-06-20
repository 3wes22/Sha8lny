"""Tests for Gemini API key collection and rotation."""

from pathlib import Path

import httpx
import pytest

from apps.core.exceptions import AIServiceError
from apps.core.gemini_keys import collect_gemini_api_keys
from apps.core.llm_provider import GeminiProvider


def test_collect_gemini_api_keys_from_mapping():
    keys = collect_gemini_api_keys(
        env={
            "GEMINI_API_KEY": "AIzaSy-primary-key",
            "GEMINI_API_KEYS": "AIzaSy-secondary-key,AIzaSy-tertiary-key",
            "GEMINI_API_KEY_2": "AIzaSy-secondary-key",
        }
    )
    assert keys == [
        "AIzaSy-primary-key",
        "AIzaSy-secondary-key",
        "AIzaSy-tertiary-key",
    ]


def test_collect_gemini_api_keys_from_commented_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GEMINI_API_KEY=AIzaSy-active-key",
                "# AIzaSy-commented-backup-key",
                "# GEMINI_API_KEY=AIzaSy-commented-assignment",
            ]
        )
    )
    keys = collect_gemini_api_keys(env={}, env_file=env_file)
    assert keys == [
        "AIzaSy-active-key",
        "AIzaSy-commented-backup-key",
        "AIzaSy-commented-assignment",
    ]


def test_gemini_provider_rotates_on_429(monkeypatch):
    calls: list[str] = []

    def fake_post(url, json, timeout):
        key = url.rsplit("key=", 1)[-1]
        calls.append(key)
        request = httpx.Request("POST", url)
        if key == "AIzaSy-first":
            return httpx.Response(429, request=request, json={"error": {"message": "quota"}})
        return httpx.Response(
            200,
            request=request,
            json={
                "candidates": [{"content": {"parts": [{"text": "ok"}]}}],
                "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1},
            },
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    provider = GeminiProvider(api_keys=["AIzaSy-first", "AIzaSy-second"])
    result = provider.send({"prompt": "hello"})
    assert provider.extract_text(result) == "ok"
    assert calls == ["AIzaSy-first", "AIzaSy-second"]
