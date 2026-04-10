"""
AI-models package bridge — temporary path-based import.

Decision (ADR-001, Phase 0):
    Keep the `sys.path` bridge for now.  The ai-models/ tree is a sibling
    directory, not a pip-installable package.  Converting it to a real package
    (e.g. `pip install -e ../ai-models`) is a Phase 1 improvement — it
    requires adding a proper pyproject.toml to ai-models/ and verifying
    that its dependency set (chromadb, sentence-transformers) does not
    conflict with the Backend venv.

    Until then, every module that needs to import from ai-models/ should
    call `ensure_ai_models_path()` from this file instead of doing its own
    `sys.path.insert()`.

Usage:
    from apps.core.ai_bridge import ensure_ai_models_path
    ensure_ai_models_path()

    # Now safe to import
    from rag import generate_response
"""

import sys
from pathlib import Path

_AI_MODELS_SRC = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "ai-models"
    / "src"
)


def ensure_ai_models_path() -> None:
    """Add ai-models/src to sys.path once, idempotently."""
    path_str = str(_AI_MODELS_SRC)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def get_ai_models_root() -> Path:
    """Return the resolved path to ai-models/src for debugging/logging."""
    return _AI_MODELS_SRC
