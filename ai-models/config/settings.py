"""
Configuration settings for AI models
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

# Model paths
LLAMA_MODEL_PATH = MODELS_DIR / "base" / "llama-3.1-8b"
MISTRAL_MODEL_PATH = MODELS_DIR / "base" / "mistral-7b"
SENTENCE_TRANSFORMER_PATH = MODELS_DIR / "base" / "sentence-transformers" / "all-MiniLM-L6-v2"

# LoRA adapter paths
QUESTION_GEN_ADAPTER_PATH = MODELS_DIR / "adapters" / "question-generator"
EVALUATOR_ADAPTER_PATH = MODELS_DIR / "adapters" / "evaluator"

# Data paths
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

# Model hyperparameters
QUANTIZATION_CONFIG = {
    "load_in_4bit": True,
    "bnb_4bit_quant_type": "nf4",
    "bnb_4bit_compute_dtype": "float16",
    "bnb_4bit_use_double_quant": True,
}

# LoRA config
LORA_CONFIG = {
    "r": 16,  # LoRA rank
    "lora_alpha": 32,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"],
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": "CAUSAL_LM",
}

# Training config
TRAINING_CONFIG = {
    "num_epochs": 3,
    "batch_size": 4,
    "gradient_accumulation_steps": 4,
    "learning_rate": 2e-4,
    "max_grad_norm": 0.3,
    "warmup_ratio": 0.03,
    "lr_scheduler_type": "cosine",
}

# RAG config
RAG_CONFIG = {
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "chunk_size": 512,
    "chunk_overlap": 50,
    "top_k": 5,
    "collection_name": "career_knowledge_base",
}

# Inference config
INFERENCE_CONFIG = {
    "max_new_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "do_sample": True,
}

# Environment variables
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
WANDB_API_KEY = os.getenv("WANDB_API_KEY")
