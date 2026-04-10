# ADR-001: Local Gemma Deterministic Workflow Architecture

**Status:** Accepted  
**Date:** 2026-04-07  
**Deciders:** Sha8alny development team  
**Supersedes:** All prior references to OpenAI/Anthropic/LangChain/Pinecone as the active AI architecture.

---

## Context

Sha8alny is an AI-powered career development platform with four AI-backed features:
assessment, roadmap generation, career advisory, and job matching.

Previous documentation described a cloud-first AI approach using OpenAI GPT-4,
Anthropic Claude, LangChain orchestration, and Pinecone vector storage.
That approach was never implemented and is not compatible with the project's
actual constraints:

- **Budget:** $0 for API costs
- **Hardware:** MacBook M1 (16GB) or Lenovo Legion 5 (RTX 3050)
- **Timeline:** Graduation project with fixed delivery date

A feasibility review concluded that multi-agent orchestration is not justified
for this use case, and that a single local LLM with deterministic workflows
is the correct architecture.

## Decision

The project adopts the following architecture:

### Runtime
- **Model:** Google Gemma 4 E4B (4-bit quantized via Ollama)
- **Inference:** Single local Ollama instance, one inference at a time
- **Vector store:** ChromaDB (local, persistent)
- **Embeddings:** all-MiniLM-L6-v2 (CPU, lightweight)

### Orchestration
- **Pattern:** Deterministic workflow with LLM nodes (NOT multi-agent)
- **Routing:** Python service functions, not LLM-based
- **Scope classification:** Keyword/regex, not LLM-based
- **Background processing:** Celery with single-lane AI worker queue
- **Fallback:** Every LLM-backed feature has a deterministic fallback

### What we are NOT building
- Multi-agent orchestration system
- LLM-based routing or planning agents
- Concurrent multi-model execution
- Fine-tuning or LoRA training on local hardware
- LangChain integration
- OpenAI/Anthropic API integration
- Pinecone/Weaviate cloud vector databases

## Consequences

### Positive
- Zero API cost
- Runs on available hardware
- Simpler debugging and maintenance
- Every feature can be demoed end-to-end
- Architecture matches real capacity

### Negative
- Single-threaded LLM inference limits concurrent AI users
- Gemma 4 E4B (4B params) is less capable than cloud models for complex reasoning
- advisory quality depends on knowledge base quality (RAG is load-bearing)

### Neutral
- Old documentation must be updated to stop describing cloud-first as current
- ai-models/ continues as a support package, not a parallel runtime

## References

- [Greenfield Feasibility Review](../../../.gemini/antigravity/brain/bc541966-4058-4f55-90b5-c9b09f30ecfa/greenfield_feasibility_review.md)
- [Gemma Architecture Adoption Plan](GEMMA_ARCHITECTURE_ADOPTION_PLAN.md)
