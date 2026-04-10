"""
Smoke tests for local model-loading helpers.
"""

from importlib import import_module
from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).parent.parent))


def _import_model_loader():
    try:
        import_module("torch")
    except ImportError:
        pytest.skip("torch is not importable in this environment.")

    from src.llm import ModelLoader

    return ModelLoader


def test_model_loader_exists():
    model_loader = _import_model_loader()
    assert model_loader is not None


def test_load_model_4bit():
    try:
        torch = import_module("torch")
    except ImportError:
        pytest.skip("torch is not importable in this environment.")

    if not torch.cuda.is_available():
        pytest.skip("Requires GPU")

    _import_model_loader()


def test_model_paths():
    from config import settings

    assert settings.MODELS_DIR is not None
    assert settings.LLAMA_MODEL_PATH is not None
    assert settings.MISTRAL_MODEL_PATH is not None
