"""
Central AI runtime settings for Sha8alny.

Hosted Gemini is the default demo runtime.
Optional provider-specific settings remain available so switching back to a
local Ollama runtime later does not require another architecture rewrite.

See ADR-002: docs/product/ADR-002-HOSTED-DEMO-AI-RUNTIME.md
"""

import os
import sys
from pathlib import Path

from decouple import config

from apps.core.gemini_keys import collect_gemini_api_keys


_BACKEND_BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Under pytest, never source Gemini keys from the developer's .env file. The
# suite is designed to run keyless (deterministic fallbacks) and must not depend
# on — or spend — a real key just because one is present in .env for the demo.
# Keys can still be injected explicitly via the process environment when a test
# needs them. This is what makes the documented `env -u GEMINI_API_KEY` run
# actually keyless regardless of .env contents.
_UNDER_PYTEST = "pytest" in sys.modules


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------
AI_PROVIDER = config("AI_PROVIDER", default="gemini").strip().lower() or "gemini"

# ---------------------------------------------------------------------------
# Gemini API
# ---------------------------------------------------------------------------
def _gemini_env_mapping() -> dict[str, str]:
    # decouple's config() also reads the .env file; under pytest read only the
    # actual process environment so a .env key cannot leak into tests.
    read = (lambda key: os.environ.get(key, "")) if _UNDER_PYTEST else (lambda key: config(key, default=""))
    mapping = {
        "GEMINI_API_KEY": read("GEMINI_API_KEY"),
        "GEMINI_API_KEYS": read("GEMINI_API_KEYS"),
    }
    for index in range(2, 10):
        mapping[f"GEMINI_API_KEY_{index}"] = read(f"GEMINI_API_KEY_{index}")
    return mapping


GEMINI_API_KEYS = collect_gemini_api_keys(
    env=_gemini_env_mapping(),
    env_file=None if _UNDER_PYTEST else _BACKEND_BASE_DIR / ".env",
)
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""
GEMINI_API_BASE_URL = config(
    "GEMINI_API_BASE_URL",
    default="https://generativelanguage.googleapis.com/v1beta",
).rstrip("/")
GEMINI_FLASH_LITE_MODEL = config(
    "GEMINI_FLASH_LITE_MODEL",
    default="gemini-2.5-flash-lite",
)
GEMINI_FLASH_MODEL = config(
    "GEMINI_FLASH_MODEL",
    default="gemini-2.5-flash",
)

# ---------------------------------------------------------------------------
# Shared inference behaviour
# ---------------------------------------------------------------------------
LLM_TIMEOUT_SECONDS = config("LLM_TIMEOUT_SECONDS", default=60, cast=int)
LLM_RETRY_COUNT = config("LLM_RETRY_COUNT", default=2, cast=int)
LLM_RETRY_BACKOFF_SECONDS = config(
    "LLM_RETRY_BACKOFF_SECONDS",
    default=1.0,
    cast=float,
)
LLM_TEMPERATURE = config("LLM_TEMPERATURE", default=0.2, cast=float)
LLM_MAX_OUTPUT_TOKENS = config("LLM_MAX_OUTPUT_TOKENS", default=1536, cast=int)

# ---------------------------------------------------------------------------
# Optional Ollama connection
# ---------------------------------------------------------------------------
OLLAMA_HOST = config("OLLAMA_HOST", default="http://127.0.0.1:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="gemma4:e2b")

# Maximum context window tokens to request (Ollama emergency fallback only).
OLLAMA_NUM_CTX = config("OLLAMA_NUM_CTX", default=4096, cast=int)

# ---------------------------------------------------------------------------
# Celery AI queue - controlled provider runtime by design (see ADR-002)
# ---------------------------------------------------------------------------
AI_CELERY_QUEUE = config("AI_CELERY_QUEUE", default="ai")
AI_CELERY_CONCURRENCY = config("AI_CELERY_CONCURRENCY", default=1, cast=int)
AI_TASK_SOFT_TIME_LIMIT = config("AI_TASK_SOFT_TIME_LIMIT", default=120, cast=int)
AI_TASK_HARD_TIME_LIMIT = config("AI_TASK_HARD_TIME_LIMIT", default=180, cast=int)

# ---------------------------------------------------------------------------
# Retrieval / vector store
# ---------------------------------------------------------------------------
CHROMA_PERSIST_DIR = config(
    "CHROMA_PERSIST_DIR",
    default="",  # empty → falls back to ai-models default location
)
EMBEDDING_MODEL = config("EMBEDDING_MODEL", default="all-MiniLM-L6-v2")

# ---------------------------------------------------------------------------
# Assessment scenario RAG corpus (feature 005-scenario-rag-corpus)
# ---------------------------------------------------------------------------
# Global on/off switch. When false, ai_pipeline._build_stage_prompt produces
# byte-identical output to the pre-feature behaviour.
ASSESSMENT_SCENARIO_RAG_ENABLED = config(
    "ASSESSMENT_SCENARIO_RAG_ENABLED",
    default=True,
    cast=bool,
)
# Dedicated on-disk Chroma directory for the scenario corpus. Kept separate
# from CHROMA_PERSIST_DIR (advisory RAG) so the two indexes can evolve
# independently and so wiping one cannot affect the other.
SCENARIO_VECTOR_DB_PATH = config(
    "SCENARIO_VECTOR_DB_PATH",
    default=str(_BACKEND_BASE_DIR / "data" / "scenario_vector_db"),
)
# Per-blueprint nearest-neighbour count requested from Chroma.
SCENARIO_RAG_TOP_K = config(
    "SCENARIO_RAG_TOP_K",
    default=1,
    cast=int,
)
# Hard ceiling on retrieved few-shot examples appended to any single prompt
# regardless of the blueprint count, so prompt size stays bounded.
SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT = config(
    "SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT",
    default=5,
    cast=int,
)

# Assessment question generation: "batched" (one Gemini call) or "per_question".
ASSESSMENT_GENERATION_MODE = config(
    "ASSESSMENT_GENERATION_MODE",
    default="batched",
).strip().lower()

# When True, CoverageTracker.assert_complete() raises if dimension mins are not met.
ASSESSMENT_COVERAGE_STRICT = config(
    "ASSESSMENT_COVERAGE_STRICT",
    default=False,
    cast=bool,
)

# Second-pass LLM calls (quota-sensitive; off by default in dev/free tier).
ASSESSMENT_AMBIGUITY_VALIDATION_ENABLED = config(
    "ASSESSMENT_AMBIGUITY_VALIDATION_ENABLED",
    default=False,
    cast=bool,
)

ASSESSMENT_RUBRIC_LLM_ENABLED = config(
    "ASSESSMENT_RUBRIC_LLM_ENABLED",
    default=False,
    cast=bool,
)

# ---------------------------------------------------------------------------
# Course embedding index (roadmap course matching)
# ---------------------------------------------------------------------------
COURSE_VECTOR_DB_PATH = config(
    "COURSE_VECTOR_DB_PATH",
    default=str(_BACKEND_BASE_DIR / "data" / "course_vector_db"),
)
COURSE_INDEX_TOP_K = config("COURSE_INDEX_TOP_K", default=2, cast=int)

# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def get_ollama_generate_url() -> str:
    """Return the full Ollama /api/generate endpoint."""
    return f"{OLLAMA_HOST.rstrip('/')}/api/generate"


def get_ollama_chat_url() -> str:
    """Return the full Ollama /api/chat endpoint."""
    return f"{OLLAMA_HOST.rstrip('/')}/api/chat"


def get_gemini_generate_url(model: str) -> str:
    """Return the full Gemini generateContent endpoint for a model."""
    return f"{GEMINI_API_BASE_URL}/models/{model}:generateContent"


def get_ai_settings_summary() -> dict:
    """Return a dict for logging / health-check display."""
    return {
        "provider": AI_PROVIDER,
        "default_model": GEMINI_FLASH_LITE_MODEL,
        "reasoning_model": GEMINI_FLASH_MODEL,
        "timeout_s": LLM_TIMEOUT_SECONDS,
        "retry_count": LLM_RETRY_COUNT,
        "temperature": LLM_TEMPERATURE,
        "max_output_tokens": LLM_MAX_OUTPUT_TOKENS,
        "api_key_configured": bool(GEMINI_API_KEYS),
        "gemini_api_key_count": len(GEMINI_API_KEYS),
        "ollama_host": OLLAMA_HOST if AI_PROVIDER == "ollama" else None,
        "ollama_model": OLLAMA_MODEL if AI_PROVIDER == "ollama" else None,
        "ollama_num_ctx": OLLAMA_NUM_CTX if AI_PROVIDER == "ollama" else None,
        "celery_queue": AI_CELERY_QUEUE,
        "celery_concurrency": AI_CELERY_CONCURRENCY,
        "embedding_model": EMBEDDING_MODEL,
        "assessment_scenario_rag_enabled": ASSESSMENT_SCENARIO_RAG_ENABLED,
        "scenario_vector_db_path": SCENARIO_VECTOR_DB_PATH,
        "scenario_rag_top_k": SCENARIO_RAG_TOP_K,
        "scenario_rag_max_examples_per_prompt": SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT,
    }
