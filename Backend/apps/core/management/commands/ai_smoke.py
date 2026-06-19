"""Smoke-test the shared Gemini runtime with one structured call."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from apps.core.ai_settings import AI_PROVIDER, GEMINI_API_KEY
from apps.core.gemma_client import GemmaClient


class Command(BaseCommand):
    help = "Run one structured Gemini call to verify the AI runtime is reachable."

    def handle(self, *args, **options) -> None:
        if AI_PROVIDER != "gemini":
            self.stdout.write(
                self.style.WARNING(
                    f"AI_PROVIDER={AI_PROVIDER!r}; smoke test targets hosted Gemini."
                )
            )

        if not GEMINI_API_KEY:
            self.stderr.write(self.style.ERROR("GEMINI_API_KEY is not configured."))
            return

        client = GemmaClient(task_type="json_generation", max_output_tokens=64)
        response = client.generate_structured(
            prompt='Return JSON {"ok": true, "echo": "sha8alny-smoke"}',
            system="Return strict JSON only.",
            required_keys=("ok", "echo"),
        )

        result = {
            "validation_success": True,
            "provider": response.metadata.provider,
            "model": response.metadata.model,
            "latency_ms": response.metadata.processing_time_ms,
            "input_tokens": response.prompt_tokens,
            "output_tokens": response.completion_tokens,
            "trace_id": response.metadata.trace_id,
            "payload": response.payload,
            "fallback_used": response.metadata.fallback_used,
        }
        self.stdout.write(json.dumps(result, indent=2))
        self.stdout.write(self.style.SUCCESS("ai_smoke passed"))
