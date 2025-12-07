# Full Custom ML Implementation Guide
## Sha8alny - Zero Budget AI Models

**Status**: Implementation Guide
**Timeline**: 12-16 Weeks
**Budget**: $0
**Approach**: 100% Custom ML Models (No External APIs)

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Implementation Setup](#pre-implementation-setup)
3. [Learning Prerequisites](#learning-prerequisites)
4. [Project Architecture](#project-architecture)
5. [Week-by-Week Implementation](#week-by-week-implementation)
6. [Component-Specific Guides](#component-specific-guides)
7. [Deployment Strategy](#deployment-strategy)
8. [Troubleshooting](#troubleshooting)
9. [Resources](#resources)

---

## System Requirements

### Minimum Hardware

```yaml
Development Machine:
  CPU: Any modern processor (Intel i5/AMD Ryzen 5 or better)
  RAM: 16GB minimum (32GB recommended)
  Storage: 100GB free space
  GPU: Not required for development (will use cloud GPUs)
  Internet: Stable connection for model downloads

Note: Models will run on free cloud GPUs (Kaggle, Colab)
      Your laptop only needs to handle code editing and testing
```

### Software Requirements

```bash
# Operating System
- macOS 10.15+ / Ubuntu 20.04+ / Windows 10+ with WSL2

# Python
- Python 3.10 or 3.11 (NOT 3.12, compatibility issues with some libraries)

# Git & Git LFS (for large model files)
- Git 2.30+
- Git LFS 2.13+

# Optional but Recommended
- Docker Desktop (for containerized deployment)
- VSCode with Python extensions
```

---

## Pre-Implementation Setup

### Phase 0: Account Creation & Access (Week 0)

#### 1. Hugging Face Account (Critical!)

```bash
# Sign up at https://huggingface.co/join

# After signup:
1. Go to Settings → Access Tokens
2. Create new token with 'read' permissions
3. Save token securely

# Accept model licenses:
- LLaMA 3.1: https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct
  (Request access, usually approved in 1-2 hours)
- Mistral 7B: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2
  (Open access, no approval needed)
```

**Why?** All open-source models are hosted on Hugging Face. You need an account to download them.

#### 2. Kaggle Account (Free GPU Access)

```bash
# Sign up at https://www.kaggle.com/account/login

# Phone Verification Required:
- Settings → Account → Phone Verification
- Verify your phone number to access free GPUs

# GPU Quota:
- 30 hours/week of FREE GPU time
- T4 or P100 GPUs (excellent for fine-tuning)

# API Token:
1. Settings → API → Create New Token
2. Download kaggle.json
3. Save to ~/.kaggle/kaggle.json (Linux/Mac) or %USERPROFILE%\.kaggle\kaggle.json (Windows)
```

**Why?** Kaggle provides the best free GPU access for training models.

#### 3. Google Colab Account

```bash
# Sign up with Google account at https://colab.research.google.com/

# Free Tier:
- ~15-20 hours/month of GPU time
- T4 GPUs
- 12-hour session limit

# Tips for maximizing free tier:
- Don't leave notebooks idle
- Save checkpoints frequently
- Use Kaggle for long training, Colab for experimentation
```

**Why?** Backup GPU access and quick experimentation.

#### 4. Lightning.AI Account (Optional)

```bash
# Sign up at https://lightning.ai/

# Free Tier:
- 22 GPU hours/month
- Good for inference/deployment testing
```

#### 5. GitHub Account & Repository

```bash
# Create repository
git init sha8alny-ai-models
cd sha8alny-ai-models

# Install Git LFS (for storing model adapters)
git lfs install
git lfs track "*.bin"
git lfs track "*.safetensors"
git lfs track "*.pt"

# Create .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Models (large files)
models/base/
*.gguf
*.pth
*.ckpt

# Data
data/raw/
*.csv
*.json.gz

# Secrets
.env
*.key
kaggle.json

# IDEs
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
EOF

git add .gitignore
git commit -m "Initial commit: Setup Git LFS and gitignore"
```

---

### Phase 0.5: Local Development Environment Setup

#### 1. Python Environment Setup

```bash
# Install Python 3.10 (recommended for compatibility)
# macOS with Homebrew
brew install python@3.10

# Ubuntu
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Windows (WSL2 recommended)
# Download from python.org

# Create project directory
mkdir -p ~/projects/sha8alny-ai-models
cd ~/projects/sha8alny-ai-models

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

#### 2. Install Core Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << EOF
# Core ML Libraries
torch>=2.1.0
transformers>=4.35.0
accelerate>=0.24.0
bitsandbytes>=0.41.0  # For quantization
peft>=0.6.0  # For LoRA fine-tuning
trl>=0.7.4  # For training

# Sentence Transformers (Embeddings)
sentence-transformers>=2.2.2

# Vector Database
chromadb>=0.4.15

# Traditional ML
scikit-learn>=1.3.0
lightgbm>=4.1.0
numpy>=1.24.0
pandas>=2.1.0

# Django Integration
django>=4.2.0
djangorestframework>=3.14.0
celery>=5.3.0
redis>=5.0.0

# Utilities
python-dotenv>=1.0.0
datasets>=2.14.0  # Hugging Face datasets
huggingface-hub>=0.19.0

# Development
jupyter>=1.0.0
ipython>=8.12.0
pytest>=7.4.0

# Monitoring
wandb>=0.15.0  # Free ML experiment tracking
EOF

# Install all dependencies
pip install -r requirements.txt

# Verify installations
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'Transformers: {transformers.__version__}')"
python -c "import sentence_transformers; print('Sentence Transformers: OK')"
python -c "import chromadb; print('ChromaDB: OK')"
```

#### 3. Hugging Face CLI Setup

```bash
# Login to Hugging Face
huggingface-cli login

# Paste your access token when prompted
# Token will be saved to ~/.huggingface/token

# Test access to LLaMA
huggingface-cli repo info meta-llama/Meta-Llama-3.1-8B-Instruct
```

#### 4. Weights & Biases Setup (Free ML Tracking)

```bash
# Sign up at https://wandb.ai/
# Free tier: unlimited projects, runs, storage

# Login
wandb login

# Paste your API key when prompted
```

**Why?** W&B tracks your training runs, metrics, and hyperparameters automatically.

---

## Learning Prerequisites

### Required Knowledge Before Starting

| Topic | Current Level | Target Level | Learning Time | Priority |
|-------|---------------|--------------|---------------|----------|
| Python | Intermediate | Advanced | 1 week | HIGH |
| PyTorch Basics | None | Intermediate | 2 weeks | CRITICAL |
| Transformers | None | Intermediate | 2 weeks | CRITICAL |
| Fine-tuning | None | Basic | 1 week | HIGH |
| Vector Embeddings | None | Intermediate | 3 days | MEDIUM |
| ML Fundamentals | Basic | Intermediate | 1 week | HIGH |

### Week -2 to 0: Crash Course (Before Implementation)

#### Week -2: PyTorch Fundamentals

**Day 1-2: Tensors & Basic Operations**
```bash
# Follow this tutorial:
https://pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html

# Exercises:
1. Create tensors from Python lists
2. Perform matrix multiplication
3. Move tensors to GPU (if available)
4. Understand tensor shapes and reshaping

# Time: 8 hours
```

**Day 3-4: Neural Networks Basics**
```bash
# Follow:
https://pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html

# Build:
1. Simple linear regression model
2. Multi-layer perceptron
3. Understand forward/backward pass
4. Implement custom loss function

# Time: 10 hours
```

**Day 5-7: Practical Project**
```python
# Mini-Project: Build a simple text classifier
# File: learning/week-2/text_classifier.py

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class SimpleTextClassifier(nn.Module):
    def __init__(self, vocab_size, embed_dim, num_classes):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.fc1 = nn.Linear(embed_dim, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        # x: [batch_size, seq_len]
        x = self.embedding(x)  # [batch_size, seq_len, embed_dim]
        x = x.mean(dim=1)  # Average pooling: [batch_size, embed_dim]
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Train this on a simple dataset (IMDB reviews, etc.)
# Time: 12 hours
```

**Week -2 Checkpoint**: Can build and train basic PyTorch models

---

#### Week -1: Transformers & Hugging Face

**Day 1-3: Hugging Face Transformers Library**
```bash
# Official Course (FREE):
https://huggingface.co/learn/nlp-course/chapter1/1

# Focus on:
- Chapter 1: Transformer models (what they are)
- Chapter 2: Using transformers (inference)
- Chapter 3: Fine-tuning (basics)

# Time: 15 hours
```

**Day 4-5: Hands-On Practice**
```python
# Exercise: Use pre-trained model for inference
# File: learning/week-1/transformer_inference.py

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load a small model first (for learning)
model_name = "gpt2"  # Small (124M params, fast download)

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Generate text
prompt = "The future of AI is"
inputs = tokenizer(prompt, return_tensors="pt")

outputs = model.generate(
    **inputs,
    max_length=50,
    temperature=0.7,
    do_sample=True
)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))

# Exercises:
# 1. Try different prompts
# 2. Experiment with temperature
# 3. Try different models (GPT-2, OPT-125M, etc.)
# Time: 10 hours
```

**Day 6-7: LoRA Fine-tuning Basics**
```bash
# Read LoRA paper (skim, focus on concept):
https://arxiv.org/abs/2106.09685

# Key concept: Instead of updating all model weights,
# only train small "adapter" layers (saves memory & time)

# Follow this tutorial:
https://github.com/huggingface/peft#lora

# Time: 10 hours
```

**Week -1 Checkpoint**: Understand transformers, can load models, basic fine-tuning concept

---

### Learning Resources (Curated)

```yaml
PyTorch:
  - Official Tutorials: https://pytorch.org/tutorials/
  - Fast.ai Course (Practical): https://course.fast.ai/
  - Video: "PyTorch in 100 Seconds": https://www.youtube.com/watch?v=ORMx45xqWkA

Transformers:
  - Hugging Face Course: https://huggingface.co/learn/nlp-course/
  - Illustrated Transformer: https://jalammar.github.io/illustrated-transformer/
  - Andrej Karpathy's "Let's build GPT": https://www.youtube.com/watch?v=kCc8FmEb1nY

Fine-tuning:
  - LoRA Paper: https://arxiv.org/abs/2106.09685
  - QLoRA (4-bit): https://arxiv.org/abs/2305.14314
  - Practical Guide: https://github.com/huggingface/peft/tree/main/examples

RAG:
  - LangChain RAG Tutorial: https://python.langchain.com/docs/use_cases/question_answering/
  - RAG from Scratch (YouTube): https://www.youtube.com/watch?v=sVcwVQRHIc8
  - ChromaDB Docs: https://docs.trychroma.com/

Traditional ML:
  - Scikit-learn User Guide: https://scikit-learn.org/stable/user_guide.html
  - LightGBM Docs: https://lightgbm.readthedocs.io/
  - Recommendation Systems Book (Free): https://www.rec-sys.com/
```

---

## Project Architecture

### Directory Structure

```bash
sha8alny-ai-models/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── config/
│   ├── __init__.py
│   ├── settings.py          # Model paths, hyperparameters
│   └── secrets.py            # API keys (not committed)
│
├── models/
│   ├── base/                 # Downloaded base models (not committed)
│   │   ├── llama-3.1-8b/
│   │   ├── mistral-7b/
│   │   └── sentence-transformers/
│   ├── adapters/             # Fine-tuned LoRA adapters (committed via Git LFS)
│   │   ├── question-generator/
│   │   ├── evaluator/
│   │   └── roadmap-generator/
│   └── custom/               # Custom trained models
│       └── job-recommender/
│
├── data/
│   ├── raw/                  # Raw training data (not committed)
│   ├── processed/            # Processed datasets
│   ├── knowledge_base/       # RAG knowledge documents
│   └── vector_db/            # ChromaDB storage
│
├── src/
│   ├── __init__.py
│   │
│   ├── assessment/
│   │   ├── __init__.py
│   │   ├── question_generator.py
│   │   ├── evaluator.py
│   │   ├── prompts.py
│   │   └── train_question_gen.py
│   │
│   ├── roadmap/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── prompts.py
│   │   └── models.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── generator.py
│   │   └── knowledge_manager.py
│   │
│   ├── recommendations/
│   │   ├── __init__.py
│   │   ├── feature_engineering.py
│   │   ├── ranker.py
│   │   ├── explainer.py
│   │   └── train_recommender.py
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── model_loader.py
│   │   ├── inference.py
│   │   └── quantization.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── data_processing.py
│       ├── metrics.py
│       └── logging_config.py
│
├── notebooks/
│   ├── 01_explore_data.ipynb
│   ├── 02_test_embeddings.ipynb
│   ├── 03_rag_experiments.ipynb
│   └── 04_recommender_analysis.ipynb
│
├── scripts/
│   ├── download_models.sh
│   ├── setup_environment.sh
│   └── run_training.sh
│
├── tests/
│   ├── test_assessment.py
│   ├── test_rag.py
│   └── test_recommendations.py
│
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── gunicorn_config.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── TRAINING_GUIDE.md
    └── API_REFERENCE.md
```

### Component Overview

```yaml
1. Assessment System:
  Base Model: LLaMA 3.1 8B Instruct
  Fine-tuning: LoRA adapters for question generation & evaluation
  Input: Career path, user profile
  Output: 20-25 structured questions + evaluation results

2. Roadmap Generator:
  Base Model: Mistral 7B Instruct
  Approach: Prompt engineering (no fine-tuning needed)
  Input: Assessment results, user preferences
  Output: Hierarchical learning roadmap (JSON)

3. RAG Career Advisory:
  Embeddings: Sentence-Transformers (all-MiniLM-L6-v2)
  Vector DB: ChromaDB (self-hosted)
  Generator: Mistral 7B Instruct
  Input: User question + conversation context
  Output: Contextual answer with citations

4. Job Recommender:
  Type: Custom ML (no LLM needed)
  Models: Sentence-Transformers + LightGBM Ranker
  Input: User profile, job pool
  Output: Ranked recommendations with explanations
```

---

## Week-by-Week Implementation

### Week 1-2: Foundation & Model Setup

#### Week 1: Download Models & Basic Setup

**Day 1: Download Base Models**

```bash
# Create download script
# File: scripts/download_models.sh

#!/bin/bash

# Create directories
mkdir -p models/base
cd models/base

# 1. Download Sentence Transformers (small, fast)
echo "Downloading Sentence Transformers..."
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
model.save('sentence-transformers/all-MiniLM-L6-v2')
print('✓ Sentence Transformers downloaded')
"

# 2. Download Mistral 7B (7GB, takes ~30 min on good connection)
echo "Downloading Mistral 7B Instruct..."
python -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import snapshot_download

model_name = 'mistralai/Mistral-7B-Instruct-v0.2'

# Download model files
snapshot_download(
    repo_id=model_name,
    local_dir='mistral-7b',
    local_dir_use_symlinks=False
)
print('✓ Mistral 7B downloaded')
"

# 3. Download LLaMA 3.1 8B (requires approval)
echo "Downloading LLaMA 3.1 8B..."
python -c "
from huggingface_hub import snapshot_download

model_name = 'meta-llama/Meta-Llama-3.1-8B-Instruct'

# This will fail if you haven't been approved
# Request access at: https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct

snapshot_download(
    repo_id=model_name,
    local_dir='llama-3.1-8b',
    local_dir_use_symlinks=False
)
print('✓ LLaMA 3.1 8B downloaded')
"

echo "All models downloaded!"
echo "Total size: ~14GB"
```

```bash
# Run the script
chmod +x scripts/download_models.sh
./scripts/download_models.sh

# Expected time: 1-2 hours depending on connection
```

**Day 2-3: Test Model Loading & Quantization**

```python
# File: src/llm/model_loader.py

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from typing import Optional

class ModelLoader:
    """Load models with 4-bit quantization for memory efficiency"""

    @staticmethod
    def load_model_4bit(
        model_path: str,
        device_map: str = "auto"
    ):
        """
        Load model in 4-bit quantization

        Memory usage:
        - 8B model: ~5GB VRAM (instead of 16GB)
        - 7B model: ~4.5GB VRAM (instead of 14GB)
        """

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
            trust_remote_code=True
        )

        tokenizer = AutoTokenizer.from_pretrained(model_path)

        # Set pad token if not present
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        return model, tokenizer

    @staticmethod
    def load_model_8bit(model_path: str):
        """Load in 8-bit (less aggressive compression)"""

        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            load_in_8bit=True,
            device_map="auto"
        )

        tokenizer = AutoTokenizer.from_pretrained(model_path)

        return model, tokenizer


# Test script
# File: tests/test_model_loading.py

from src.llm.model_loader import ModelLoader
import torch

def test_mistral_loading():
    """Test Mistral 7B loading"""

    print("Loading Mistral 7B in 4-bit...")
    model, tokenizer = ModelLoader.load_model_4bit(
        "models/base/mistral-7b"
    )

    print(f"Model loaded on: {model.device}")
    print(f"Memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

    # Test inference
    prompt = "Hello, how are you?"
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=50)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print(f"Response: {response}")
    print("✓ Mistral 7B working!")

def test_llama_loading():
    """Test LLaMA 3.1 8B loading"""

    print("\nLoading LLaMA 3.1 8B in 4-bit...")
    model, tokenizer = ModelLoader.load_model_4bit(
        "models/base/llama-3.1-8b"
    )

    print(f"Model loaded on: {model.device}")
    print(f"Memory allocated: {torch.cuda.memory_allocated() / 1024**3:.2f} GB")

    # Test inference with LLaMA chat format
    messages = [
        {"role": "user", "content": "What is machine learning?"}
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=100)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print(f"Response: {response}")
    print("✓ LLaMA 3.1 8B working!")

if __name__ == "__main__":
    # Run on Kaggle or Colab (needs GPU)
    test_mistral_loading()
    test_llama_loading()
```

**Day 4-5: Prompt Engineering Framework**

```python
# File: src/llm/prompts.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import json

@dataclass
class PromptTemplate:
    """Base prompt template"""
    system: str
    user_template: str
    few_shot_examples: Optional[List[Dict]] = None

    def format(self, **kwargs) -> str:
        """Format prompt with variables"""
        user_prompt = self.user_template.format(**kwargs)

        # Add few-shot examples if present
        if self.few_shot_examples:
            examples_text = "\n\n".join([
                f"Example {i+1}:\nInput: {ex['input']}\nOutput: {ex['output']}"
                for i, ex in enumerate(self.few_shot_examples)
            ])
            user_prompt = f"{examples_text}\n\n{user_prompt}"

        return user_prompt


class AssessmentPrompts:
    """Prompts for assessment generation"""

    QUESTION_GENERATION = PromptTemplate(
        system="You are an expert technical assessment creator. Generate high-quality, practical questions that accurately assess skill levels.",

        user_template="""Generate {count} assessment questions for a {level} level {career_path} candidate.

User's current skills: {user_skills}

Requirements:
- Question types: 60% multiple choice, 30% scenario-based, 10% self-rating
- Difficulty distribution: 40% medium, 30% easy, 30% hard
- Cover both technical skills AND soft skills
- Each question must be practical and job-relevant

Output as JSON array:
{{
  "questions": [
    {{
      "id": 1,
      "question": "question text here",
      "type": "multiple_choice|scenario|rating",
      "difficulty": "easy|medium|hard",
      "skill_category": "technical|soft_skill",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},  // MCQ only
      "correct_answer": "A",  // MCQ only
      "explanation": "why this answer is correct",  // MCQ only
      "evaluation_criteria": ["criterion 1", "criterion 2"],  // Scenario only
      "sample_answer": "example good answer"  // Scenario only
    }}
  ]
}}

Generate ONLY valid JSON, no additional text.""",

        few_shot_examples=[
            {
                "input": "Python, intermediate, Software Engineer",
                "output": json.dumps({
                    "questions": [{
                        "id": 1,
                        "question": "What is the time complexity of accessing an element in a Python dictionary?",
                        "type": "multiple_choice",
                        "difficulty": "medium",
                        "skill_category": "technical",
                        "options": {
                            "A": "O(1) average case",
                            "B": "O(n)",
                            "C": "O(log n)",
                            "D": "O(n^2)"
                        },
                        "correct_answer": "A",
                        "explanation": "Python dictionaries use hash tables, providing O(1) average-case lookup time."
                    }]
                }, indent=2)
            }
        ]
    )

    EVALUATION = PromptTemplate(
        system="You are an expert skill evaluator. Analyze assessment responses objectively and provide actionable feedback.",

        user_template="""Evaluate this {career_path} assessment.

Questions and User Answers:
{questions_and_answers}

Provide evaluation as JSON:
{{
  "overall_proficiency": "Beginner|Intermediate|Advanced",
  "overall_score": 0-100,
  "skill_scores": {{
    "Python": 85,
    "Problem Solving": 70,
    "Communication": 65
  }},
  "strengths": ["specific strength 1", "specific strength 2"],
  "skill_gaps": ["specific gap 1", "specific gap 2"],
  "recommendations": [
    "actionable recommendation 1",
    "actionable recommendation 2"
  ],
  "reasoning": "brief explanation of the evaluation"
}}

Output ONLY valid JSON."""
    )


class RoadmapPrompts:
    """Prompts for roadmap generation"""

    GENERATE_ROADMAP = PromptTemplate(
        system="You are an expert learning path designer. Create realistic, achievable roadmaps based on user constraints.",

        user_template="""Create a learning roadmap for a {career_path} learner.

Assessment Results:
{assessment_results}

User Preferences:
- Target timeframe: {timeframe}
- Available hours/week: {hours_per_week}
- Current proficiency: {proficiency_level}
- Skill gaps: {skill_gaps}

Requirements:
- Minimum 2 phases, 3 milestones per phase, 2 skills per milestone
- Realistic time estimates based on {hours_per_week} hours/week
- Identify prerequisites for proper sequencing
- Include both technical skills and soft skills

Output as JSON:
{{
  "roadmap": {{
    "total_duration_weeks": 24,
    "phases": [
      {{
        "phase_number": 1,
        "title": "Foundation",
        "duration_weeks": 8,
        "milestones": [
          {{
            "milestone_number": 1,
            "title": "Python Basics",
            "duration_weeks": 3,
            "skills": [
              {{
                "name": "Python Syntax",
                "description": "Learn basic syntax, data types, control flow",
                "estimated_hours": 20,
                "resources": ["resource 1", "resource 2"],
                "prerequisites": []
              }}
            ]
          }}
        ]
      }}
    ]
  }}
}}

Generate ONLY valid JSON."""
    )


class RAGPrompts:
    """Prompts for RAG responses"""

    GENERATE_ANSWER = PromptTemplate(
        system="You are a knowledgeable career advisor. Answer questions accurately using the provided context. Always cite sources.",

        user_template="""Answer the user's question using the provided context.

Context (from knowledge base):
{context_chunks}

Conversation History (last 3 exchanges):
{conversation_history}

User Question: {question}

Instructions:
- Answer in 200-400 words
- Be specific and actionable
- Cite sources using [Source: Title]
- If context is insufficient, acknowledge limitations
- Maintain conversational tone

Answer:"""
    )


# Usage example
def generate_assessment_prompt(career_path: str, level: str, skills: List[str], count: int = 25):
    """Generate formatted prompt for question generation"""

    prompt = AssessmentPrompts.QUESTION_GENERATION.format(
        career_path=career_path,
        level=level,
        user_skills=", ".join(skills),
        count=count
    )

    return prompt
```

**Day 6-7: Basic Inference Engine**

```python
# File: src/llm/inference.py

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Dict, Optional, List
import json
import re

class LLMInference:
    """Inference engine for custom models"""

    def __init__(self, model, tokenizer, device="auto"):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        do_sample: bool = True,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """Generate text from prompt"""

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=do_sample,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode
        generated_text = self.tokenizer.decode(
            outputs[0],
            skip_special_tokens=True
        )

        # Extract only the generated part (remove prompt)
        generated_text = generated_text[len(prompt):].strip()

        return generated_text

    def generate_json(
        self,
        prompt: str,
        max_retries: int = 3,
        **kwargs
    ) -> Dict:
        """Generate and parse JSON output"""

        for attempt in range(max_retries):
            try:
                # Generate text
                output = self.generate(prompt, **kwargs)

                # Extract JSON (handle cases where model adds extra text)
                json_match = re.search(r'\{.*\}', output, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = output

                # Parse JSON
                result = json.loads(json_str)
                return result

            except json.JSONDecodeError as e:
                print(f"JSON parse error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
                continue

        raise ValueError("Failed to generate valid JSON after retries")


# Test inference
# File: tests/test_inference.py

from src.llm.model_loader import ModelLoader
from src.llm.inference import LLMInference
from src.llm.prompts import generate_assessment_prompt

def test_question_generation():
    """Test question generation end-to-end"""

    # Load model
    print("Loading Mistral 7B...")
    model, tokenizer = ModelLoader.load_model_4bit("models/base/mistral-7b")

    # Create inference engine
    inference = LLMInference(model, tokenizer)

    # Generate prompt
    prompt = generate_assessment_prompt(
        career_path="Software Engineer",
        level="intermediate",
        skills=["Python", "Django", "REST APIs"],
        count=3  # Start small for testing
    )

    print("Generating questions...")

    # Generate
    result = inference.generate_json(
        prompt,
        max_new_tokens=1024,
        temperature=0.8
    )

    print(json.dumps(result, indent=2))
    print(f"✓ Generated {len(result.get('questions', []))} questions")

if __name__ == "__main__":
    test_question_generation()
```

**Week 1 Deliverables:**
- ✅ All base models downloaded
- ✅ Can load models in 4-bit quantization
- ✅ Prompt templates created
- ✅ Basic inference working

---

#### Week 2: RAG System Implementation (Easiest Component First)

**Day 1-2: Embedding Pipeline**

```python
# File: src/rag/embeddings.py

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import torch

class EmbeddingEngine:
    """Generate embeddings for text"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = None
    ):
        """
        Initialize embedding model

        Args:
            model_name: Sentence transformer model name
            device: 'cuda', 'cpu', or None (auto-detect)
        """

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.model = SentenceTransformer(model_name, device=device)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()

        print(f"Embedding model loaded: {model_name}")
        print(f"Embedding dimension: {self.embedding_dim}")
        print(f"Device: {device}")

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> np.ndarray:
        """
        Generate embeddings for text(s)

        Args:
            texts: Single string or list of strings
            batch_size: Batch size for encoding
            show_progress: Show progress bar

        Returns:
            Numpy array of shape (n, embedding_dim)
        """

        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_numpy=True
        )

        return embeddings

    def similarity(
        self,
        text1: Union[str, np.ndarray],
        text2: Union[str, np.ndarray]
    ) -> float:
        """
        Compute cosine similarity between two texts or embeddings

        Args:
            text1: Text string or embedding array
            text2: Text string or embedding array

        Returns:
            Similarity score (0-1)
        """

        # Encode if strings
        if isinstance(text1, str):
            emb1 = self.encode(text1)
        else:
            emb1 = text1

        if isinstance(text2, str):
            emb2 = self.encode(text2)
        else:
            emb2 = text2

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )

        return float(similarity)


# Test embeddings
# File: tests/test_embeddings.py

from src.rag.embeddings import EmbeddingEngine

def test_embeddings():
    """Test embedding generation"""

    engine = EmbeddingEngine()

    # Test single text
    text = "Machine learning is a subset of artificial intelligence"
    embedding = engine.encode(text)

    print(f"Embedding shape: {embedding.shape}")
    print(f"Embedding (first 10 dims): {embedding[0][:10]}")

    # Test batch
    texts = [
        "Python is a programming language",
        "JavaScript is used for web development",
        "Machine learning requires data"
    ]

    embeddings = engine.encode(texts)
    print(f"\nBatch embeddings shape: {embeddings.shape}")

    # Test similarity
    sim1 = engine.similarity(texts[0], texts[1])
    sim2 = engine.similarity(texts[0], texts[2])

    print(f"\nSimilarity (Python vs JavaScript): {sim1:.3f}")
    print(f"Similarity (Python vs ML): {sim2:.3f}")

    print("✓ Embeddings working!")

if __name__ == "__main__":
    test_embeddings()
```

**Continue in next part due to length limit...**

---

## [Next Sections Preview]

The complete guide continues with:

- **Week 2 (Day 3-7)**: Vector database setup, retrieval, RAG integration
- **Week 3-4**: Job recommender system implementation
- **Week 5-6**: Assessment system fine-tuning
- **Week 7-8**: Roadmap generator
- **Week 9-10**: Django integration
- **Week 11-12**: Testing & optimization
- **Week 13-14**: Deployment
- **Week 15-16**: Documentation & polish

Would you like me to:
1. Continue with Week 2-16 detailed implementation?
2. Focus on a specific component first?
3. Create separate detailed guides for each component?

---

## Quick Start Checklist

```bash
# Phase 0: Setup (Do this first!)
□ Create Hugging Face account + get LLaMA access
□ Create Kaggle account + verify phone
□ Install Python 3.10
□ Install Git + Git LFS
□ Create virtual environment
□ Install dependencies (pip install -r requirements.txt)
□ Download base models (~14GB)
□ Test model loading on Kaggle/Colab

# Phase 1: Learning (2 weeks)
□ Complete PyTorch basics tutorial
□ Complete Hugging Face NLP course (Chapters 1-3)
□ Build simple text classifier
□ Test inference with GPT-2

# Phase 2: Implementation (Start Week 1)
□ Set up project structure
□ Implement embedding engine
□ Build RAG system
□ ... (see week-by-week plan above)
```

---

**Status**: Part 1 of Full Custom ML Guide
**Next**: Week 2-16 detailed implementation, component-specific training guides
**Questions?** Ready to create detailed guides for any specific component!
