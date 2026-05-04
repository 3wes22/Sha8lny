"""
Central AI runtime settings for Sha8alny.

Hosted Gemini is the default demo runtime.
Optional provider-specific settings remain available so switching back to a
local Ollama runtime later does not require another architecture rewrite.

See ADR-002: docs/product/ADR-002-HOSTED-DEMO-AI-RUNTIME.md
"""

from decouple import config


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------
AI_PROVIDER = config("AI_PROVIDER", default="gemini").strip().lower() or "gemini"

# ---------------------------------------------------------------------------
# Gemini API
# ---------------------------------------------------------------------------
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
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

# ---------------------------------------------------------------------------
# Optional Ollama inference tuning
# ---------------------------------------------------------------------------
OLLAMA_TIMEOUT_SECONDS = config(
    "OLLAMA_TIMEOUT_SECONDS",
    default=LLM_TIMEOUT_SECONDS,
    cast=int,
)
OLLAMA_RETRY_COUNT = config(
    "OLLAMA_RETRY_COUNT",
    default=LLM_RETRY_COUNT,
    cast=int,
)
OLLAMA_RETRY_BACKOFF_SECONDS = config(
    "OLLAMA_RETRY_BACKOFF_SECONDS",
    default=LLM_RETRY_BACKOFF_SECONDS,
    cast=float,
)
OLLAMA_TEMPERATURE = config(
    "OLLAMA_TEMPERATURE",
    default=LLM_TEMPERATURE,
    cast=float,
)

# Maximum context window tokens to request.
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
        "api_key_configured": bool(GEMINI_API_KEY),
        "ollama_host": OLLAMA_HOST if AI_PROVIDER == "ollama" else None,
        "ollama_model": OLLAMA_MODEL if AI_PROVIDER == "ollama" else None,
        "ollama_num_ctx": OLLAMA_NUM_CTX if AI_PROVIDER == "ollama" else None,
        "celery_queue": AI_CELERY_QUEUE,
        "celery_concurrency": AI_CELERY_CONCURRENCY,
        "embedding_model": EMBEDDING_MODEL,
    }
