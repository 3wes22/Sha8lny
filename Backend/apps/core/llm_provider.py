"""
Provider abstractions for hosted and local LLM runtimes.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.core.ai_settings import (
    AI_PROVIDER,
    GEMINI_API_BASE_URL,
    GEMINI_API_KEY,
    GEMINI_FLASH_LITE_MODEL,
    GEMINI_FLASH_MODEL,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_TEMPERATURE,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
)
from apps.core.exceptions import AIServiceError


FLASH_LITE_TASK_TYPES = {
    "assessment_question_generation",
    "classification",
    "feedback_summary",
    "json_generation",
    "json_repair",
    "rewriting",
    "roadmap_personalization",
}

FLASH_TASK_TYPES = {
    "assessment_quality_review",
    "career_matching",
    "complex_role_matching",
    "rubric_validation",
}

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def select_model_for_task(task_type: str, *, provider: str = AI_PROVIDER) -> str:
    """Return the default model for the given task type."""
    provider_name = str(provider or AI_PROVIDER).strip().lower()
    if provider_name == "ollama":
        return OLLAMA_MODEL

    normalized = str(task_type or "json_generation").strip().lower()
    if normalized in FLASH_TASK_TYPES:
        return GEMINI_FLASH_MODEL
    return GEMINI_FLASH_LITE_MODEL


class LLMProvider:
    """Base provider contract used by the shared backend client."""

    name = "unknown"

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def extract_text(self, raw: dict[str, Any]) -> str:
        raise NotImplementedError

    def extract_usage(self, raw: dict[str, Any]) -> tuple[int, int]:
        return 0, 0


class GeminiProvider(LLMProvider):
    """Gemini API provider using the Google AI Studio Gemini Developer API."""

    name = "gemini"

    def __init__(
        self,
        *,
        api_key: str = GEMINI_API_KEY,
        base_url: str = GEMINI_API_BASE_URL,
        timeout_seconds: int = 60,
        temperature: float = LLM_TEMPERATURE,
    ) -> None:
        self.api_key = str(api_key or "").strip()
        self.base_url = str(base_url or GEMINI_API_BASE_URL).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise AIServiceError(
                "Gemini API key is not configured",
                details={"reason": "missing_api_key", "retryable": False},
            )
        if self.api_key.startswith("your-") or self.api_key.startswith("<") or self.api_key.endswith("-here"):
            raise AIServiceError(
                "Gemini API key is still set to a placeholder value",
                details={"reason": "placeholder_api_key", "retryable": False},
            )

        model = str(payload.get("model") or GEMINI_FLASH_LITE_MODEL).strip()
        generation_config: dict[str, Any] = {
            "temperature": float(payload.get("temperature", self.temperature)),
            "candidateCount": 1,
            "maxOutputTokens": int(
                payload.get("max_output_tokens") or LLM_MAX_OUTPUT_TOKENS
            ),
        }
        if payload.get("structured"):
            generation_config["responseMimeType"] = "application/json"
        if payload.get("response_json_schema"):
            generation_config["responseJsonSchema"] = payload["response_json_schema"]

        body: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": str(payload.get("prompt") or "")}],
                }
            ],
            "generationConfig": generation_config,
        }

        system_prompt = str(payload.get("system") or "").strip()
        if system_prompt:
            body["systemInstruction"] = {
                "role": "system",
                "parts": [{"text": system_prompt}],
            }

        response = httpx.post(
            f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
            json=body,
            timeout=self.timeout_seconds,
        )

        if response.status_code >= 400:
            message = _extract_error_message(response)
            raise AIServiceError(
                "Gemini request failed",
                details={
                    "reason": "gemini_http_error",
                    "message": message,
                    "status_code": response.status_code,
                    "retryable": response.status_code in RETRYABLE_STATUS_CODES,
                    "provider": self.name,
                },
            )

        try:
            result = response.json()
        except ValueError as error:
            raise AIServiceError(
                "Gemini returned invalid JSON",
                details={
                    "reason": "invalid_gemini_response",
                    "message": str(error),
                    "retryable": True,
                    "provider": self.name,
                },
            ) from error

        if not isinstance(result, dict):
            raise AIServiceError(
                "Gemini returned an unexpected payload",
                details={
                    "reason": "unexpected_payload_type",
                    "payload_type": type(result).__name__,
                    "retryable": False,
                    "provider": self.name,
                },
            )

        prompt_feedback = result.get("promptFeedback")
        if isinstance(prompt_feedback, dict) and prompt_feedback.get("blockReason"):
            raise AIServiceError(
                "Gemini blocked the prompt",
                details={
                    "reason": "prompt_blocked",
                    "block_reason": prompt_feedback.get("blockReason"),
                    "retryable": False,
                    "provider": self.name,
                },
            )

        return result

    def extract_text(self, raw: dict[str, Any]) -> str:
        candidates = raw.get("candidates") if isinstance(raw.get("candidates"), list) else []
        texts: list[str] = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content") if isinstance(candidate.get("content"), dict) else {}
            parts = content.get("parts") if isinstance(content.get("parts"), list) else []
            for part in parts:
                if isinstance(part, dict) and str(part.get("text") or "").strip():
                    texts.append(str(part.get("text") or "").strip())
        return "\n".join(texts).strip()

    def extract_usage(self, raw: dict[str, Any]) -> tuple[int, int]:
        usage = raw.get("usageMetadata") if isinstance(raw.get("usageMetadata"), dict) else {}
        return (
            int(usage.get("promptTokenCount") or 0),
            int(usage.get("candidatesTokenCount") or 0),
        )


class OllamaProvider(LLMProvider):
    """Optional local-provider implementation kept for future switching."""

    name = "ollama"

    def __init__(
        self,
        *,
        host: str = OLLAMA_HOST,
        timeout_seconds: int = 60,
        temperature: float = LLM_TEMPERATURE,
        num_ctx: int = OLLAMA_NUM_CTX,
    ) -> None:
        self.host = str(host or OLLAMA_HOST).rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.num_ctx = num_ctx

    def send(self, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.host}/api/generate",
            json={
                "model": payload.get("model") or OLLAMA_MODEL,
                "prompt": payload.get("prompt"),
                "system": payload.get("system", ""),
                "stream": False,
                "format": "json" if payload.get("structured") else "",
                "options": {
                    "temperature": float(payload.get("temperature", self.temperature)),
                    "num_ctx": self.num_ctx,
                    "num_predict": int(
                        payload.get("max_output_tokens") or LLM_MAX_OUTPUT_TOKENS
                    ),
                },
            },
            timeout=self.timeout_seconds,
        )

        if response.status_code >= 400:
            raise AIServiceError(
                "Ollama request failed",
                details={
                    "reason": "ollama_http_error",
                    "status_code": response.status_code,
                    "message": _extract_error_message(response),
                    "retryable": response.status_code in RETRYABLE_STATUS_CODES,
                    "provider": self.name,
                },
            )

        try:
            result = response.json()
        except ValueError as error:
            raise AIServiceError(
                "Ollama returned invalid JSON",
                details={
                    "reason": "invalid_ollama_response",
                    "message": str(error),
                    "retryable": True,
                    "provider": self.name,
                },
            ) from error

        if not isinstance(result, dict):
            raise AIServiceError(
                "Ollama returned an unexpected payload",
                details={
                    "reason": "unexpected_payload_type",
                    "payload_type": type(result).__name__,
                    "retryable": False,
                    "provider": self.name,
                },
            )

        return result

    def extract_text(self, raw: dict[str, Any]) -> str:
        return str(raw.get("response") or "").strip()

    def extract_usage(self, raw: dict[str, Any]) -> tuple[int, int]:
        return (
            int(raw.get("prompt_eval_count") or 0),
            int(raw.get("eval_count") or 0),
        )


def create_provider(
    *,
    provider_name: str = AI_PROVIDER,
    host: str = OLLAMA_HOST,
    api_key: str = GEMINI_API_KEY,
    base_url: str = GEMINI_API_BASE_URL,
    timeout_seconds: int = 60,
    temperature: float = LLM_TEMPERATURE,
    num_ctx: int = OLLAMA_NUM_CTX,
) -> LLMProvider:
    """Return the configured provider implementation."""
    normalized = str(provider_name or AI_PROVIDER).strip().lower()
    if normalized == "ollama":
        return OllamaProvider(
            host=host,
            timeout_seconds=timeout_seconds,
            temperature=temperature,
            num_ctx=num_ctx,
        )
    return GeminiProvider(
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=timeout_seconds,
        temperature=temperature,
    )


def _extract_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and str(error.get("message") or "").strip():
            return str(error.get("message") or "").strip()
        if str(payload.get("message") or "").strip():
            return str(payload.get("message") or "").strip()
    return response.text.strip()
