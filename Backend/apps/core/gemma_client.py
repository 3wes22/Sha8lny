"""
Shared Ollama / Gemma client for backend AI features.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any, Iterable, Optional

import httpx

from apps.core.ai_contracts import AIInvocationMetadata
from apps.core.ai_logging import build_ai_metadata
from apps.core.ai_settings import (
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_RETRY_COUNT,
    OLLAMA_RETRY_BACKOFF_SECONDS,
    OLLAMA_TEMPERATURE,
    OLLAMA_TIMEOUT_SECONDS,
)
from apps.core.ai_validation import extract_json_object, require_keys
from apps.core.exceptions import AIServiceError


@dataclass(frozen=True)
class GemmaResponse:
    text: str
    payload: Optional[dict[str, Any]]
    metadata: AIInvocationMetadata
    prompt_tokens: int
    completion_tokens: int


class GemmaClient:
    """Thin shared client around the Ollama generate endpoint."""

    def __init__(
        self,
        *,
        host: str = OLLAMA_HOST,
        model: str = OLLAMA_MODEL,
        timeout_seconds: int = OLLAMA_TIMEOUT_SECONDS,
        retry_count: int = OLLAMA_RETRY_COUNT,
        retry_backoff_seconds: float = OLLAMA_RETRY_BACKOFF_SECONDS,
        temperature: float = OLLAMA_TEMPERATURE,
        num_ctx: int = OLLAMA_NUM_CTX,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_backoff_seconds = retry_backoff_seconds
        self.temperature = temperature
        self.num_ctx = num_ctx

    def generate_text(self, *, prompt: str, system: str = "") -> GemmaResponse:
        started_at = monotonic()
        raw = self._post_generate(
            {
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "format": "",
                "options": {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                },
            }
        )

        metadata = build_ai_metadata(
            source="llm",
            processing_time_ms=int((monotonic() - started_at) * 1000),
            model=self.model,
        )
        return GemmaResponse(
            text=(raw.get("response") or "").strip(),
            payload=None,
            metadata=metadata,
            prompt_tokens=int(raw.get("prompt_eval_count") or 0),
            completion_tokens=int(raw.get("eval_count") or 0),
        )

    def generate_structured(
        self,
        *,
        prompt: str,
        system: str = "",
        required_keys: Iterable[str] = (),
    ) -> GemmaResponse:
        started_at = monotonic()
        last_error: Optional[Exception] = None

        for attempt in range(self.retry_count + 1):
            raw = self._post_generate(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": self.temperature,
                        "num_ctx": self.num_ctx,
                    },
                }
            )

            text = (raw.get("response") or "").strip()
            try:
                payload = require_keys(extract_json_object(text), required_keys)
            except Exception as error:
                last_error = error
                if attempt >= self.retry_count:
                    break
                continue

            metadata = build_ai_metadata(
                source="llm",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=self.model,
            )
            return GemmaResponse(
                text=text,
                payload=payload,
                metadata=metadata,
                prompt_tokens=int(raw.get("prompt_eval_count") or 0),
                completion_tokens=int(raw.get("eval_count") or 0),
            )

        raise AIServiceError(
            "Structured generation failed validation",
            details={
                "reason": "structured_generation_failed",
                "last_error": str(last_error) if last_error else None,
            },
        )

    def _post_generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPError as error:
            raise AIServiceError(
                "Ollama request failed",
                details={"reason": "http_error", "message": str(error), "host": self.host},
            ) from error
        except ValueError as error:
            raise AIServiceError(
                "Ollama returned invalid JSON",
                details={"reason": "invalid_ollama_response", "message": str(error)},
            ) from error

        if not isinstance(result, dict):
            raise AIServiceError(
                "Ollama returned an unexpected payload",
                details={"reason": "unexpected_payload_type", "payload_type": type(result).__name__},
            )

        return result
