"""
Test model loading functionality
"""
import pytest
import torch
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm import ModelLoader


def test_model_loader_exists():
    """Test that ModelLoader class exists"""
    assert ModelLoader is not None


@pytest.mark.skipif(not torch.cuda.is_available(), reason="Requires GPU")
def test_load_model_4bit():
    """Test 4-bit model loading (requires GPU)"""
    # This test will be skipped if no GPU available
    # Actual testing should be done on Kaggle/Colab
    pass


def test_model_paths():
    """Test that model paths are configured"""
    from config import settings

    assert settings.MODELS_DIR is not None
    assert settings.LLAMA_MODEL_PATH is not None
    assert settings.MISTRAL_MODEL_PATH is not None
