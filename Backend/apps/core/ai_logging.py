"""
Structured AI logging and metadata helpers.
"""

from __future__ import annotations

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
