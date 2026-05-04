"""
Compatibility client for backend AI features.

The class name is kept stable for existing imports, but requests now route
through provider abstractions so Gemini is the active hosted runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from time import monotonic, sleep
from typing import Any, Iterable, Optional

from apps.core.ai_contracts import AIInvocationMetadata
from apps.core.ai_logging import build_ai_metadata
from apps.core.ai_settings import (
    AI_PROVIDER,
    GEMINI_API_BASE_URL,
    GEMINI_API_KEY,
    LLM_MAX_OUTPUT_TOKENS,
    LLM_RETRY_BACKOFF_SECONDS,
    LLM_RETRY_COUNT,
    LLM_TEMPERATURE,
    LLM_TIMEOUT_SECONDS,
    OLLAMA_HOST,
    OLLAMA_NUM_CTX,
)
from apps.core.ai_validation import extract_json_object, require_keys
from apps.core.exceptions import AIServiceError
from apps.core.llm_provider import create_provider, select_model_for_task


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GemmaResponse:
    text: str
    payload: Optional[dict[str, Any]]
    metadata: AIInvocationMetadata
    prompt_tokens: int
    completion_tokens: int


class GemmaClient:
    """Shared client that routes requests to the configured LLM provider."""

    def __init__(
        self,
        *,
        provider: str = AI_PROVIDER,
        host: str = OLLAMA_HOST,
        api_key: str = GEMINI_API_KEY,
        base_url: str = GEMINI_API_BASE_URL,
        model: Optional[str] = None,
        timeout_seconds: int = LLM_TIMEOUT_SECONDS,
        retry_count: int = LLM_RETRY_COUNT,
        retry_backoff_seconds: float = LLM_RETRY_BACKOFF_SECONDS,
        temperature: float = LLM_TEMPERATURE,
        num_ctx: int = OLLAMA_NUM_CTX,
        task_type: str = "json_generation",
        max_output_tokens: int = LLM_MAX_OUTPUT_TOKENS,
    ) -> None:
        self.provider_name = str(provider or AI_PROVIDER).strip().lower()
        self.host = host.rstrip("/")
        self.api_key = str(api_key or "").strip()
        self.base_url = str(base_url or GEMINI_API_BASE_URL).rstrip("/")
        self.task_type = task_type
        self.model = model or select_model_for_task(
            task_type,
            provider=self.provider_name,
        )
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_backoff_seconds = retry_backoff_seconds
        self.temperature = temperature
        self.num_ctx = num_ctx
        self.max_output_tokens = max_output_tokens
        self._provider = create_provider(
            provider_name=self.provider_name,
            host=self.host,
            api_key=self.api_key,
            base_url=self.base_url,
            timeout_seconds=self.timeout_seconds,
            temperature=self.temperature,
            num_ctx=self.num_ctx,
        )

    def generate_text(self, *, prompt: str, system: str = "") -> GemmaResponse:
        started_at = monotonic()
        last_error: Optional[Exception] = None
        prompt_tokens_total = 0
        completion_tokens_total = 0

        for attempt in range(self.retry_count + 1):
            raw = self._post_generate(self._build_payload(prompt=prompt, system=system))
            prompt_tokens, completion_tokens = self._provider.extract_usage(raw)
            prompt_tokens_total += prompt_tokens
            completion_tokens_total += completion_tokens
            text = self._provider.extract_text(raw)
            if text:
                return self._build_response(
                    raw=raw,
                    text=text,
                    payload=None,
                    started_at=started_at,
                    prompt_tokens=prompt_tokens_total,
                    completion_tokens=completion_tokens_total,
                )

            last_error = AIServiceError(
                "Model returned an empty response",
                details={"reason": "empty_response", "retryable": True},
            )
            if attempt >= self.retry_count:
                break
            self._log_retry_event(
                reason="empty_response",
                attempt=attempt + 1,
                retryable=True,
            )
            sleep(self._retry_delay(attempt))

        raise AIServiceError(
            "Text generation failed validation",
            details={
                "reason": "empty_response",
                "last_error": str(last_error) if last_error else None,
            },
        )

    def generate_structured(
        self,
        *,
        prompt: str,
        system: str = "",
        required_keys: Iterable[str] = (),
        response_json_schema: Optional[dict[str, Any]] = None,
    ) -> GemmaResponse:
        started_at = monotonic()
        last_error: Optional[Exception] = None
        last_text = ""
        prompt_tokens_total = 0
        completion_tokens_total = 0

        for attempt in range(self.retry_count + 1):
            raw = self._post_generate(
                self._build_payload(
                    prompt=prompt,
                    system=system,
                    structured=True,
                    response_json_schema=response_json_schema,
                )
            )

            prompt_tokens, completion_tokens = self._provider.extract_usage(raw)
            prompt_tokens_total += prompt_tokens
            completion_tokens_total += completion_tokens
            text = self._provider.extract_text(raw)
            last_text = text
            try:
                payload = require_keys(extract_json_object(text), required_keys)
            except Exception as error:
                last_error = error
                if attempt >= self.retry_count:
                    break
                self._log_retry_event(
                    reason=getattr(error, "details", {}).get("reason", "invalid_json")
                    if isinstance(error, AIServiceError)
                    else "invalid_json",
                    attempt=attempt + 1,
                    retryable=True,
                )
                sleep(self._retry_delay(attempt))
                continue

            return self._build_response(
                raw=raw,
                text=text,
                payload=payload,
                started_at=started_at,
                prompt_tokens=prompt_tokens_total,
                completion_tokens=completion_tokens_total,
            )

        if last_text:
            repaired = self._repair_invalid_json(
                prompt=prompt,
                invalid_text=last_text,
                required_keys=required_keys,
                started_at=started_at,
                prompt_tokens_total=prompt_tokens_total,
                completion_tokens_total=completion_tokens_total,
                response_json_schema=response_json_schema,
            )
            if repaired is not None:
                return repaired

        raise AIServiceError(
            "Structured generation failed validation",
            details={
                "reason": "structured_generation_failed",
                "last_error": str(last_error) if last_error else None,
                "raw_text": last_text,
            },
        )

    def _post_generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Optional[Exception] = None
        for attempt in range(self.retry_count + 1):
            try:
                return self._provider.send(payload)
            except AIServiceError as error:
                last_error = error
                retryable = bool((error.details or {}).get("retryable"))
                if not retryable or attempt >= self.retry_count:
                    raise
                self._log_retry_event(
                    reason=(error.details or {}).get("reason", type(error).__name__),
                    attempt=attempt + 1,
                    retryable=retryable,
                    status_code=(error.details or {}).get("status_code"),
                )
                sleep(self._retry_delay(attempt))
        raise AIServiceError(
            "LLM request failed",
            details={"reason": "provider_failure", "last_error": str(last_error)},
        )

    def _build_payload(
        self,
        *,
        prompt: str,
        system: str,
        structured: bool = False,
        model_override: Optional[str] = None,
        response_json_schema: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return {
            "model": model_override or self.model,
            "prompt": prompt,
            "system": system,
            "structured": structured,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "response_json_schema": response_json_schema,
            "task_type": self.task_type,
        }

    def _build_response(
        self,
        *,
        raw: dict[str, Any],
        text: str,
        payload: Optional[dict[str, Any]],
        started_at: float,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> GemmaResponse:
        if prompt_tokens is None or completion_tokens is None:
            prompt_tokens, completion_tokens = self._provider.extract_usage(raw)
        metadata = build_ai_metadata(
            source="llm",
            processing_time_ms=int((monotonic() - started_at) * 1000),
            model=self.model,
            provider=self.provider_name,
        )
        logger.info(
            "LLM request completed",
            extra={
                "provider": self.provider_name,
                "model": self.model,
                "task_type": self.task_type,
                "latency_ms": metadata.processing_time_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "trace_id": metadata.trace_id,
            },
        )
        return GemmaResponse(
            text=text,
            payload=payload,
            metadata=metadata,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    def _repair_invalid_json(
        self,
        *,
        prompt: str,
        invalid_text: str,
        required_keys: Iterable[str],
        started_at: float,
        prompt_tokens_total: int,
        completion_tokens_total: int,
        response_json_schema: Optional[dict[str, Any]] = None,
    ) -> Optional[GemmaResponse]:
        repair_model = select_model_for_task("json_repair", provider=self.provider_name)
        repair_payload = self._build_payload(
            prompt=self._build_json_repair_prompt(
                original_prompt=prompt,
                invalid_text=invalid_text,
                required_keys=required_keys,
            ),
            system="Return valid JSON only. No markdown. No explanation.",
            structured=True,
            model_override=repair_model,
            response_json_schema=response_json_schema,
        )
        raw = self._post_generate(repair_payload)
        text = self._provider.extract_text(raw)
        payload = require_keys(extract_json_object(text), required_keys)
        repair_prompt_tokens, repair_completion_tokens = self._provider.extract_usage(raw)
        prompt_tokens_total += repair_prompt_tokens
        completion_tokens_total += repair_completion_tokens
        metadata = build_ai_metadata(
            source="llm",
            processing_time_ms=int((monotonic() - started_at) * 1000),
            model=repair_model,
            provider=self.provider_name,
        )
        logger.info(
            "LLM JSON repair completed",
            extra={
                "provider": self.provider_name,
                "model": repair_model,
                "task_type": "json_repair",
                "latency_ms": metadata.processing_time_ms,
                "prompt_tokens": prompt_tokens_total,
                "completion_tokens": completion_tokens_total,
                "trace_id": metadata.trace_id,
            },
        )
        return GemmaResponse(
            text=text,
            payload=payload,
            metadata=metadata,
            prompt_tokens=prompt_tokens_total,
            completion_tokens=completion_tokens_total,
        )

    @staticmethod
    def _build_json_repair_prompt(
        *,
        original_prompt: str,
        invalid_text: str,
        required_keys: Iterable[str],
    ) -> str:
        required = ", ".join(required_keys) if required_keys else "the required contract"
        return (
            "Repair the following invalid JSON response. Return JSON only.\n"
            f"Required top-level keys: {required}.\n"
            f"Original prompt:\n{original_prompt}\n\n"
            f"Invalid response:\n{invalid_text}"
        )

    def _retry_delay(self, attempt: int) -> float:
        return self.retry_backoff_seconds * (2**attempt)

    def _log_retry_event(
        self,
        *,
        reason: str,
        attempt: int,
        retryable: bool,
        status_code: Optional[int] = None,
    ) -> None:
        logger.warning(
            "LLM request retry scheduled: provider=%s model=%s task_type=%s reason=%s attempt=%s status_code=%s",
            self.provider_name,
            self.model,
            self.task_type,
            reason,
            attempt,
            status_code,
            extra={
                "provider": self.provider_name,
                "model": self.model,
                "task_type": self.task_type,
                "reason": reason,
                "attempt": attempt,
                "retryable": retryable,
                "status_code": status_code,
            },
        )
