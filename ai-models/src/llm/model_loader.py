"""
Model loading utilities with quantization support
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class ModelLoader:
    """Load models with 4-bit quantization for memory efficiency"""

    @staticmethod
    def load_model_4bit(
        model_path: str,
        device_map: str = "auto",
        trust_remote_code: bool = True
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Load model in 4-bit quantization

        Args:
            model_path: Path to model directory
            device_map: Device mapping strategy
            trust_remote_code: Whether to trust remote code

        Returns:
            Tuple of (model, tokenizer)

        Memory usage:
            - 8B model: ~5GB VRAM (instead of 16GB)
            - 7B model: ~4.5GB VRAM (instead of 14GB)
        """
        logger.info(f"Loading model from {model_path} with 4-bit quantization...")

        # 4-bit quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",  # Normal Float 4-bit
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True  # Nested quantization
        )

        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=bnb_config,
            device_map=device_map,
            trust_remote_code=trust_remote_code
        )

        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Set pad token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info(f"Model loaded successfully on {model.device}")
        if torch.cuda.is_available():
            logger.info(f"GPU memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

        return model, tokenizer

    @staticmethod
    def load_model_8bit(
        model_path: str,
        device_map: str = "auto"
    ) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Load model in 8-bit quantization (more stable than 4-bit)

        Args:
            model_path: Path to model directory
            device_map: Device mapping strategy

        Returns:
            Tuple of (model, tokenizer)
        """
        logger.info(f"Loading model from {model_path} with 8-bit quantization...")

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            load_in_8bit=True,
            device_map=device_map
        )

        tokenizer = AutoTokenizer.from_pretrained(model_path)

        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        return model, tokenizer
