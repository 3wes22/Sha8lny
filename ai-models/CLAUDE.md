# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **AI Models** component of **Sha8alny** - an AI-powered career development platform. This directory contains custom ML implementations for skill assessment, learning path generation, career advisory, and job recommendations.

**Key Constraint**: $0 budget - 100% custom models using free GPU tiers (Kaggle/Colab), no paid APIs.

**Approach**:
- Fine-tuned open-source LLMs (LLaMA 3.1 8B, Mistral 7B) with LoRA adapters
- 4-bit quantization for memory efficiency (~5GB VRAM)
- Self-hosted RAG system with ChromaDB
- Traditional ML for job recommendations

**Integration**: AI models expose Python functions called by Django backend via Celery async tasks.

## Repository Structure

```
ai-models/
├── config/                # Settings, hyperparameters, secrets
├── models/
│   ├── base/              # Downloaded base models (LLaMA, Mistral) - NOT committed
│   ├── adapters/          # Fine-tuned LoRA adapters - committed via Git LFS
│   └── custom/            # Custom trained models (LightGBM ranker)
├── data/
│   ├── raw/               # Raw training data - NOT committed
│   ├── processed/         # Processed datasets
│   ├── knowledge_base/    # RAG knowledge documents
│   └── vector_db/         # ChromaDB persistent storage
├── src/
│   ├── assessment/        # Question generation & evaluation
│   ├── roadmap/           # Learning path generation
│   ├── rag/               # RAG system (embeddings, retrieval, generation)
│   ├── recommendations/   # Job recommender (feature engineering, ranking)
│   ├── llm/               # Model loading, inference, quantization
│   └── utils/             # Shared utilities
├── notebooks/             # Jupyter experiments
├── scripts/               # download_models.sh, training scripts
├── tests/                 # pytest tests
└── deployment/            # Dockerfile, docker-compose
```

## Development Commands

### Environment Setup

```bash
cd ai-models

# Create Python 3.10 virtual environment (NOT 3.12 - compatibility issues)
python3.10 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Login to Hugging Face (required for LLaMA downloads)
huggingface-cli login  # Paste your HF token

# Login to Weights & Biases (experiment tracking)
wandb login
```

### Model Downloads (One-time, ~14GB)

```bash
# Download LLaMA 3.1 8B, Mistral 7B, Sentence-Transformers
chmod +x scripts/download_models.sh
./scripts/download_models.sh

# Models saved to models/base/:
# - llama-3.1-8b/
# - mistral-7b/
# - sentence-transformers/all-MiniLM-L6-v2/
```

**Note**: LLaMA 3.1 requires access approval. Request at https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct (usually approved in 1-2 hours).

### Common Development Tasks

```bash
# Run tests
pytest tests/

# Run tests for specific component
pytest tests/test_rag.py

# Launch Jupyter for experiments
jupyter notebook notebooks/

# Run inference locally (after models are downloaded)
python src/rag/retriever.py
python src/assessment/question_generator.py

# Train models (must be done on Kaggle/Colab, NOT locally)
# See FULL_CUSTOM_ML_GUIDE.md for Kaggle notebook setup
```

### GPU Platforms for Training

- **Kaggle**: 30 GPU hours/week (primary) - https://www.kaggle.com/code
- **Google Colab**: 15-20 GPU hours/month (backup) - https://colab.research.google.com
- **Lightning.AI**: 22 GPU hours/month (optional) - https://lightning.ai

**All training must happen on these platforms** - local machine only for development and inference.

## AI Components Architecture

### 1. AI Skill Assessment System

**Files**: [src/assessment/question_generator.py](src/assessment/question_generator.py), [src/assessment/evaluator.py](src/assessment/evaluator.py)

- **Model**: LLaMA 3.1 8B Instruct (4-bit quantized, ~5GB VRAM)
- **Fine-tuning**: LoRA adapters (~100MB) for question generation & evaluation
- **Input**: Career path, user profile, current skill level
- **Output**:
  - Generation: 20-25 questions (60% MCQ, 30% scenario, 10% self-rating) as JSON
  - Evaluation: Proficiency levels (Beginner/Intermediate/Advanced), skill scores, gaps, recommendations
- **Training**: Supervised fine-tuning on synthetic assessment datasets using QLoRA on Kaggle
- **Inference Time**: ~30 seconds generation, ~45 seconds evaluation (async via Celery)

### 2. Learning Roadmap Generator

**Files**: [src/roadmap/generator.py](src/roadmap/generator.py), [src/roadmap/prompts.py](src/roadmap/prompts.py)

- **Model**: Mistral 7B Instruct (4-bit quantized, ~4.5GB VRAM)
- **Approach**: Advanced prompt engineering (NO fine-tuning needed - Mistral excels at structured output)
- **Input**: Assessment results, user preferences (timeframe, hours/week, learning style)
- **Output**: Hierarchical roadmap (Phases → Milestones → Skills) as validated JSON
- **Structure**: Minimum 2 phases, 3 milestones/phase, 2 skills/milestone
- **Context Window**: 32K tokens (excellent for long prompts with examples)
- **Inference Time**: ~60 seconds

### 3. RAG Career Advisory System

**Files**: [src/rag/embeddings.py](src/rag/embeddings.py), [src/rag/vector_store.py](src/rag/vector_store.py), [src/rag/retriever.py](src/rag/retriever.py), [src/rag/generator.py](src/rag/generator.py)

- **Embeddings**: Sentence-Transformers (all-MiniLM-L6-v2, 384 dimensions)
  - Parameters: 22 million (tiny, runs on CPU)
  - Speed: ~3000 sentences/second on CPU
  - Memory: <500MB
- **Vector DB**: ChromaDB (self-hosted, persistent storage in `data/vector_db/`)
- **Generator**: Mistral 7B Instruct (same model as roadmap generator)
- **Knowledge Base**: Career guides, skill documentation, industry trends (stored in `data/knowledge_base/`)
- **Input**: User question + conversation history (last 3 exchanges)
- **Output**: Contextual answer (200-400 words) with source citations
- **Retrieval**: Top-k semantic search (k=5 default), re-ranked by relevance

### 4. Job Recommendation Engine

**Files**: [src/recommendations/feature_engineering.py](src/recommendations/feature_engineering.py), [src/recommendations/ranker.py](src/recommendations/ranker.py), [src/recommendations/explainer.py](src/recommendations/explainer.py)

- **Type**: Hybrid traditional ML (NO LLM needed)
- **Models**:
  - Sentence-Transformers (same as RAG) for skill embeddings
  - LightGBM Ranker for final ranking
- **Features**: User skill embeddings, experience level, job requirements, location preferences
- **Input**: User profile, pool of job postings
- **Output**: Ranked job recommendations with explainability scores (why this job matches)
- **Training**: <1 hour on CPU with historical job match data
- **Model Size**: <10MB
- **Inference Time**: <100ms for ranking 1000 jobs

### Integration with Backend

- **Django Backend**: https://github.com/sha8alny/Sha8alny_BE (Django REST Framework)
- **Frontend**: https://github.com/sha8alny/Sha8alny_Frontend (Next.js)
- **Task Queue**: Celery for all AI operations (never block HTTP requests)
- **Caching**: Redis for model outputs, embeddings, API responses
- **Database**: PostgreSQL for results storage

AI functions are called via Celery tasks:
```python
# Django view triggers Celery task
result = generate_assessment_questions.delay(user_id, career_path)

# Celery worker (in ai-models) executes
# Result cached in Redis, stored in PostgreSQL
```

## Implementation Roadmap

See [FULL_CUSTOM_ML_GUIDE.md](FULL_CUSTOM_ML_GUIDE.md) for detailed week-by-week implementation guide (1373 lines).

**Recommended Order** (easiest to hardest):

1. **Week 1-2: RAG System** ⭐ Start here
   - Implement embedding engine
   - Set up ChromaDB vector database
   - Build retrieval pipeline
   - Integrate with Mistral 7B for generation
   - **No fine-tuning needed, fastest to implement**

2. **Week 3-4: Job Recommender**
   - Feature engineering pipeline
   - Train LightGBM ranker (traditional ML)
   - Build explainability module
   - **No GPU needed, trains on CPU**

3. **Week 5-6: Assessment System** ⚠️ Most complex
   - Collect/create training data
   - Fine-tune LLaMA 3.1 with LoRA on Kaggle
   - Implement question generation API
   - Implement evaluation API
   - **Requires GPU training**

4. **Week 7-8: Roadmap Generator**
   - Design comprehensive prompts with few-shot examples
   - Test with Mistral 7B
   - Validate JSON output structure
   - **Prompt engineering only, no training**

5. **Week 9-10: Django Integration**
   - Create Celery tasks for each component
   - Implement caching layer (Redis)
   - Error handling and retries
   - API endpoint integration

6. **Week 11-12: Testing & Optimization**
   - Unit tests for all components
   - Load testing, latency optimization
   - Model quantization improvements

7. **Week 13-14: Deployment**
   - Dockerize AI services
   - Deploy to free/low-cost platforms (Hugging Face Spaces, Railway)
   - Set up monitoring (Weights & Biases)

## Technology Stack

**Core ML**:
- PyTorch 2.1+ (deep learning framework)
- Transformers 4.35+ (Hugging Face models)
- Accelerate 0.24+ (distributed training)
- bitsandbytes 0.41+ (4-bit/8-bit quantization)
- PEFT 0.6+ (LoRA fine-tuning)
- TRL 0.7+ (transformer training utilities)

**Embeddings & RAG**:
- sentence-transformers 2.2+ (semantic embeddings)
- ChromaDB 0.4+ (vector database)

**Traditional ML**:
- scikit-learn 1.3+ (preprocessing, metrics)
- LightGBM 4.1+ (gradient boosting)
- NumPy, Pandas (data processing)

**Django Integration**:
- Django 4.2+, Django REST Framework 3.14+
- Celery 5.3+ (async task queue)
- Redis 5.0+ (caching, broker)

**Development**:
- Jupyter (experimentation)
- pytest (testing)
- wandb (experiment tracking)
- Git LFS (large file storage for LoRA adapters)

## Model Specifications

### LLaMA 3.1 8B Instruct
- **Parameters**: 8 billion
- **Context Window**: 8K tokens
- **Quantization**: 4-bit NF4 (~5GB VRAM vs 16GB unquantized)
- **Use Case**: Assessment question generation & evaluation
- **Fine-tuning**: QLoRA (4-bit quantized LoRA)
- **Adapter Size**: ~100MB (vs 16GB full model)
- **Training Platform**: Kaggle (T4 GPU, 16GB VRAM)
- **Access**: Requires approval at https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct

### Mistral 7B Instruct v0.2
- **Parameters**: 7 billion
- **Context Window**: 32K tokens (excellent for long prompts)
- **Quantization**: 4-bit NF4 (~4.5GB VRAM)
- **Use Case**: Roadmap generation, RAG response generation
- **Approach**: Prompt engineering only (NO fine-tuning)
- **Why**: Mistral excels at structured JSON output with good prompts
- **Access**: Open access, no approval needed

### Sentence-Transformers (all-MiniLM-L6-v2)
- **Parameters**: 22 million (tiny!)
- **Embedding Dimension**: 384
- **Use Case**: RAG embeddings, job skill matching
- **Performance**: ~3000 sentences/second on CPU
- **Memory**: <500MB
- **Hardware**: Runs efficiently on CPU (no GPU needed)

### LightGBM
- **Type**: Gradient boosting (traditional ML)
- **Use Case**: Job recommendation ranking
- **Training Time**: <1 hour on CPU
- **Model Size**: <10MB
- **Features**: Handles categorical and numerical features well

## Critical Constraints & Best Practices

### Constraints
- **Budget**: $0 - no paid APIs (OpenAI, Claude, etc.)
- **Hardware**: Models must run in 4-bit quantization (~5GB VRAM max)
- **GPU Access**: Free tiers only (Kaggle 30h/week, Colab 15-20h/month)
- **Model Size**: Maximum 8B parameters (larger models won't fit in free GPU memory)
- **Timeline**: 12-16 weeks for complete implementation

### Best Practices

**Memory Optimization**:
- ✅ Always use 4-bit quantization for inference (NF4 or INT4)
- ✅ Use 8-bit quantization for training (more stable than 4-bit)
- ✅ Clear CUDA cache after model loading: `torch.cuda.empty_cache()`
- ❌ Never load multiple large models simultaneously

**Fine-tuning**:
- ✅ Use LoRA adapters (parameter-efficient, ~100MB)
- ✅ Use QLoRA for 4-bit quantized training (max memory efficiency)
- ✅ Save checkpoints every epoch (Kaggle sessions can disconnect)
- ❌ Never full fine-tune (requires >40GB VRAM for 8B models)

**Prompt Engineering**:
- ✅ Try prompt engineering before fine-tuning (cheaper, faster)
- ✅ Use few-shot examples (3-5 examples in prompt)
- ✅ Request JSON output explicitly, provide schema
- ✅ Implement retry logic for malformed JSON (3 attempts max)

**Caching**:
- ✅ Cache all embeddings (slow to compute, fast to reuse)
- ✅ Cache LLM outputs for identical prompts (Redis with 24h TTL)
- ✅ Cache vector search results for common queries
- ❌ Don't cache user-specific sensitive data

**Async Processing**:
- ✅ Use Celery for ALL AI operations (never block HTTP)
- ✅ Set reasonable timeouts (60s roadmap, 30s questions, 45s evaluation)
- ✅ Implement exponential backoff retries (3 attempts)
- ✅ Return task ID immediately, poll for results

**Monitoring**:
- ✅ Use Weights & Biases for training metrics, hyperparameters
- ✅ Log inference latency, error rates, cache hit rates
- ✅ Track GPU memory usage during inference
- ✅ Monitor Celery queue length, task success/failure rates

**Version Control**:
- ✅ Use Git LFS for LoRA adapters (<500MB)
- ❌ Never commit base models (14GB, use .gitignore)
- ✅ Commit processed datasets if <100MB
- ✅ Version prompts in code (track which prompt version produced results)

## Documentation & Resources

### Local Documentation
- **[FULL_CUSTOM_ML_GUIDE.md](FULL_CUSTOM_ML_GUIDE.md)** - Comprehensive 1373-line implementation guide
  - Week-by-week detailed tasks
  - Code examples for each component
  - Training scripts and notebooks
  - Troubleshooting common issues
- **[AI_MODELS_PLAN.md](AI_MODELS_PLAN.md)** - High-level planning document
- **[README.md](README.md)** - AI components overview

### GitHub Repositories (Up-to-date)
- **Backend**: https://github.com/sha8alny/Sha8alny_BE (Django REST API)
- **Frontend**: https://github.com/sha8alny/Sha8alny_Frontend (Next.js)

### Learning Resources
- **PyTorch Basics**: https://pytorch.org/tutorials/
- **Hugging Face NLP Course**: https://huggingface.co/learn/nlp-course/ (Chapters 1-3 essential)
- **LoRA Paper**: https://arxiv.org/abs/2106.09685
- **QLoRA (4-bit training)**: https://arxiv.org/abs/2305.14314
- **RAG Tutorial**: https://www.youtube.com/watch?v=sVcwVQRHIc8
- **ChromaDB Docs**: https://docs.trychroma.com/

### Required Accounts
- **Hugging Face**: https://huggingface.co/ (model downloads)
  - Create account
  - Generate access token (Settings → Access Tokens)
  - Request LLaMA 3.1 access (approval in 1-2 hours)
- **Kaggle**: https://www.kaggle.com/ (free GPU training, 30h/week)
  - Create account
  - **Verify phone number** (required for GPU access)
  - Enable GPU in notebook settings
- **Weights & Biases**: https://wandb.ai/ (experiment tracking, free tier)
  - Create account
  - Generate API key

## Quick Start Checklist

### Phase 0: Setup (Before Implementation)

```bash
# Accounts
□ Create Hugging Face account + request LLaMA access
□ Create Kaggle account + verify phone number
□ Create Weights & Biases account

# Software
□ Install Python 3.10 (NOT 3.12 due to library compatibility)
□ Install Git + Git LFS (for model adapters)

# Environment
□ Clone repository
□ cd ai-models
□ python3.10 -m venv venv && source venv/bin/activate
□ pip install -r requirements.txt

# Authentication
□ huggingface-cli login (paste HF token)
□ wandb login (paste W&B API key)

# Models
□ chmod +x scripts/download_models.sh
□ ./scripts/download_models.sh (~14GB download)
□ Test model loading on Kaggle/Colab (see FULL_CUSTOM_ML_GUIDE.md)
```

### Learning Prerequisites (Recommended, 2 weeks)

```bash
□ PyTorch basics (1 week) - pytorch.org/tutorials/beginner/basics/
□ Transformers basics (1 week) - huggingface.co/learn/nlp-course/chapter1-3
□ Build simple text classifier (practice project)
□ Complete LoRA tutorial - github.com/huggingface/peft#lora
```

### Implementation Phases (12-16 weeks)

```bash
□ Week 1-2: RAG system (start here!)
□ Week 3-4: Job recommender
□ Week 5-6: Assessment system (requires GPU training)
□ Week 7-8: Roadmap generator
□ Week 9-10: Django integration
□ Week 11-12: Testing & optimization
□ Week 13-14: Deployment
```

## Troubleshooting

### Common Issues

**"CUDA out of memory"**
- Reduce batch size (try batch_size=1 for inference)
- Ensure 4-bit quantization is enabled
- Clear cache: `torch.cuda.empty_cache()`
- Check no other models are loaded

**"LLaMA access denied"**
- Request access at model page
- Wait 1-2 hours for approval
- Re-run `huggingface-cli login` after approval

**"JSON decode error from LLM output"**
- Implement retry logic (3 attempts)
- Use regex to extract JSON from surrounding text
- Increase temperature for more varied outputs
- Add JSON schema example to prompt

**"Kaggle kernel disconnected"**
- Save checkpoints every epoch
- Enable auto-save in notebook settings
- Resume from latest checkpoint

**"ChromaDB persistence error"**
- Ensure `data/vector_db/` directory exists
- Check write permissions
- Verify ChromaDB version compatibility

For detailed troubleshooting, see [FULL_CUSTOM_ML_GUIDE.md](FULL_CUSTOM_ML_GUIDE.md) Section 8.

---

**Status**: Ready for implementation
**Next Steps**: Complete Phase 0 setup, then start with RAG system (Week 1-2)
**Questions?**: See FULL_CUSTOM_ML_GUIDE.md or raise an issue on GitHub
