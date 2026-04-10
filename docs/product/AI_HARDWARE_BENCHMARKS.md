# AI Hardware Benchmark Sheet

**Purpose:** Track actual local inference latency so the team makes decisions from measured data, not guesses.

**Last updated:** _Fill in after first benchmark run_

---

## Hardware Under Test

| Machine | CPU | GPU | RAM | OS | Ollama Version |
|---|---|---|---|---|---|
| MacBook M1 | Apple M1 | Integrated (Metal) | ___ GB | macOS ___ | ___ |
| Legion 5 | AMD/Intel ___ | RTX 3050 (___ GB VRAM) | ___ GB | ___ | ___ |

---

## Model Configuration

| Setting | Value |
|---|---|
| Model | `gemma4:e4b` |
| Quantization | 4-bit (Ollama default) |
| Context window (`num_ctx`) | 8192 |
| Temperature | 0.3 |

---

## Benchmark Results

### Cold Start (First inference after model load)

| Machine | Cold start time (s) | Notes |
|---|---|---|
| MacBook M1 | ___ | Time from `ollama run` to first token |
| Legion 5 | ___ | |

### Assessment Question Generation

Prompt: Generate 5 skill assessment questions for "Backend Developer"

| Machine | Tokens generated | Time to first token (s) | Total time (s) | Tokens/s |
|---|---|---|---|---|
| MacBook M1 | ___ | ___ | ___ | ___ |
| Legion 5 | ___ | ___ | ___ | ___ |

### Assessment Response Evaluation

Prompt: Evaluate user responses and produce JSON scores (~500 token input, ~300 token output)

| Machine | Tokens generated | Time to first token (s) | Total time (s) | Tokens/s |
|---|---|---|---|---|
| MacBook M1 | ___ | ___ | ___ | ___ |
| Legion 5 | ___ | ___ | ___ | ___ |

### Roadmap Phase Generation

Prompt: Generate 3-phase roadmap content for "Frontend Developer" with milestones (~700 token input, ~800 token output)

| Machine | Tokens generated | Time to first token (s) | Total time (s) | Tokens/s |
|---|---|---|---|---|
| MacBook M1 | ___ | ___ | ___ | ___ |
| Legion 5 | ___ | ___ | ___ | ___ |

### Advisory RAG Response

Prompt: Career advisory question with 3 retrieved context chunks (~1500 token input, ~400 token output)

| Machine | Tokens generated | Time to first token (s) | Total time (s) | Tokens/s |
|---|---|---|---|---|
| MacBook M1 | ___ | ___ | ___ | ___ |
| Legion 5 | ___ | ___ | ___ | ___ |

### JSON Output Reliability

Run each prompt 10 times. Record how many produce parseable JSON on first attempt.

| Task | Valid JSON (out of 10) | Retries needed | Notes |
|---|---|---|---|
| Assessment questions | ___/10 | ___ | |
| Assessment evaluation | ___/10 | ___ | |
| Roadmap generation | ___/10 | ___ | |

---

## Memory Observations

| Machine | Ollama process RSS (MB) | Free RAM during inference (MB) | Swap used? |
|---|---|---|---|
| MacBook M1 | ___ | ___ | Yes / No |
| Legion 5 | ___ | ___ | Yes / No |

---

## Context Window Scaling

Test with increasing `num_ctx` to find safe limits per machine.

| Machine | num_ctx=4096 (s) | num_ctx=8192 (s) | num_ctx=16384 (s) | OOM? |
|---|---|---|---|---|
| MacBook M1 | ___ | ___ | ___ | ___ |
| Legion 5 | ___ | ___ | ___ | ___ |

---

## How to Run Benchmarks

### Quick manual test
```bash
# 1. Make sure Ollama is running
ollama serve

# 2. Pull the model (one-time)
ollama pull gemma4:e4b

# 3. Time a generation
time ollama run gemma4:e4b "Generate 5 technical interview questions for a Backend Developer role. Return as JSON array." --format json

# 4. Check memory
# macOS:
vm_stat | head -5
# Linux:
nvidia-smi && free -h
```

### Scripted benchmark (future — Phase 1)
A proper benchmark script will be added to `ai-models/scripts/benchmark.py` during the shared runtime phase.

---

## Acceptable Thresholds (Phase 0 Baseline)

These are starting targets. Adjust as real measurements come in.

| Metric | Target | Hard limit |
|---|---|---|
| Cold start | < 30s | 60s |
| Single generation (assessment/roadmap) | < 15s | 30s |
| Advisory response (with RAG) | < 10s | 20s |
| JSON validity (first attempt) | > 85% | > 70% |
| Memory usage (model loaded, idle) | < 8 GB | < 12 GB |
