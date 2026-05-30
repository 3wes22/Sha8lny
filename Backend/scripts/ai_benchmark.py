#!/usr/bin/env python3
"""Benchmark shared AI runtime latency and token usage (smoke-level)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django

django.setup()

from apps.core.gemma_client import GemmaClient


def run_case(name: str, *, prompt: str, required_keys: tuple[str, ...]) -> dict:
    client = GemmaClient(task_type="json_generation", max_output_tokens=128)
    response = client.generate_structured(
        prompt=prompt,
        system="Return strict JSON only.",
        required_keys=required_keys,
    )
    return {
        "case": name,
        "latency_ms": response.metadata.processing_time_ms,
        "input_tokens": response.prompt_tokens,
        "output_tokens": response.completion_tokens,
        "fallback_used": response.metadata.fallback_used,
        "model": response.metadata.model,
    }


def main() -> None:
    rows = [
        run_case(
            "structured_smoke",
            prompt='Return {"ok": true, "echo": "benchmark"}',
            required_keys=("ok", "echo"),
        )
    ]
    print(json.dumps({"results": rows}, indent=2))


if __name__ == "__main__":
    main()
