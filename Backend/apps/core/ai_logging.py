"""
Structured AI logging and metadata helpers.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from uuid import uuid4

from apps.core.ai_settings import AI_PROVIDER
from apps.core.ai_contracts import AIInvocationMetadata


logger = logging.getLogger(__name__)


def build_ai_metadata(
    *,
    source: str,
    processing_time_ms: int,
    model: Optional[str],
    provider: Optional[str] = AI_PROVIDER,
    version: Optional[str] = None,
    fallback_used: bool = False,
    error_code: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> AIInvocationMetadata:
    metadata = AIInvocationMetadata(
        source=source,
        processing_time_ms=processing_time_ms,
        model=model,
        provider=provider,
        version=version,
        fallback_used=fallback_used,
        error_code=error_code,
        trace_id=trace_id or uuid4().hex,
    )
    return metadata


def log_ai_invocation(
    *,
    trace_id: str,
    feature: str,
    provider: str,
    model: Optional[str],
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    validation_success: bool,
    fallback_used: bool = False,
    task_type: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """Emit one structured JSON log line per LLM invocation."""
    payload = {
        "event": "ai_invocation",
        "trace_id": trace_id,
        "feature": feature,
        "provider": provider,
        "model": model,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "validation_success": validation_success,
        "fallback_used": fallback_used,
    }
    if task_type:
        payload["task_type"] = task_type
    if extra:
        payload.update(extra)

    logger.info("ai_invocation %s", json.dumps(payload, default=str))


def log_ai_failure(
    *,
    feature: str,
    error: Exception,
    trace_id: str,
    extra: Optional[dict[str, Any]] = None,
) -> None:
    logger.warning(
        "AI runtime failure for %s",
        feature,
        extra={
            "feature": feature,
            "trace_id": trace_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            **(extra or {}),
        },
    )
