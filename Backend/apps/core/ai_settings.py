"""
Central AI runtime settings for Sha8alny.

All Ollama / Gemma configuration lives here.
Every AI feature reads from these values — no per-feature Ollama config.

See ADR-001: docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md
"""

from decouple import config


# ---------------------------------------------------------------------------
# Ollama connection
# ---------------------------------------------------------------------------
OLLAMA_HOST = config("OLLAMA_HOST", default="http://127.0.0.1:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="gemma4:e2b")

# ---------------------------------------------------------------------------
# Inference behaviour
# ---------------------------------------------------------------------------
OLLAMA_TIMEOUT_SECONDS = config("OLLAMA_TIMEOUT_SECONDS", default=60, cast=int)
OLLAMA_RETRY_COUNT = config("OLLAMA_RETRY_COUNT", default=2, cast=int)
OLLAMA_RETRY_BACKOFF_SECONDS = config(
    "OLLAMA_RETRY_BACKOFF_SECONDS", default=1.0, cast=float
)
OLLAMA_TEMPERATURE = config("OLLAMA_TEMPERATURE", default=0.3, cast=float)

# Maximum context window tokens to request.
# Keep conservative so the KV cache fits in memory alongside the model.
#   M1 8 GB   → safe up to ~4 096  (default)
#   16 GB RAM → safe up to ~8 192  (set in .env)
OLLAMA_NUM_CTX = config("OLLAMA_NUM_CTX", default=4096, cast=int)

# ---------------------------------------------------------------------------
# Celery AI queue – single-lane by design (see ADR-001)
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


def get_ai_settings_summary() -> dict:
    """Return a dict for logging / health-check display."""
    return {
        "ollama_host": OLLAMA_HOST,
        "model": OLLAMA_MODEL,
        "timeout_s": OLLAMA_TIMEOUT_SECONDS,
        "retry_count": OLLAMA_RETRY_COUNT,
        "temperature": OLLAMA_TEMPERATURE,
        "num_ctx": OLLAMA_NUM_CTX,
        "celery_queue": AI_CELERY_QUEUE,
        "celery_concurrency": AI_CELERY_CONCURRENCY,
        "embedding_model": EMBEDDING_MODEL,
    }
