# ADR-002: Hosted Demo AI Runtime With Local Fallback

**Status:** Accepted  
**Date:** 2026-05-04  
**Deciders:** Sha8alny development team  
**Supersedes for demo operations:** [ADR-001](ADR-001-LOCAL-GEMMA-ARCHITECTURE.md)

## Context

ADR-001 moved the project away from unimplemented OpenAI/Anthropic/LangChain/Pinecone assumptions and standardized the AI workflow around deterministic Django services with a local Gemma/Ollama runtime.

For the graduation evaluator demo, the product now needs a more reliable hosted path while preserving a local fallback. The backend already exposes provider selection through `Backend/apps/core/ai_settings.py`.

## Decision

The active demo runtime is:

- **Default provider:** hosted Gemini API through `AI_PROVIDER=gemini`
- **Fallback provider:** local Gemma via Ollama through `AI_PROVIDER=ollama`
- **Orchestration:** deterministic Django services, not agentic runtime planning
- **Vector store and embeddings:** ChromaDB plus `all-MiniLM-L6-v2` where retrieval is needed
- **Failure behavior:** AI-backed features must return controlled fallback responses instead of raw provider errors

## Consequences

- Hosted demos require `GEMINI_API_KEY`.
- Local fallback remains documented and supported for offline development or hosted provider outages.
- Older local-only Gemma documents are historical unless they are explicitly describing the fallback path.
- Future AI docs should describe the provider contract, not a single hard-coded runtime.
