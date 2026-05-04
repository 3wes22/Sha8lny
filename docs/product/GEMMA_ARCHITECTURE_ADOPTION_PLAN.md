# Gemma Architecture Adoption Plan for Sha8alny

**Date:** 2026-04-07  
**Scope:** Replace the current mixed AI scaffolding with a deterministic workflow architecture powered by a single local Gemma runtime.  
**Primary Goal:** Ship working AI-driven assessment, roadmap, and advisory flows on current local hardware without introducing multi-agent complexity.

## 1. Executive Summary

This plan applies the April 7 architecture review to the current Sha8alny repository as it actually exists today.

The correct target is not a multi-agent system. The correct target is:

- one shared local LLM runtime
- one deterministic orchestration layer in Django
- one validation and fallback layer
- one retrieval stack for grounded advisory and matching
- one async queue for long-running AI work

For this repository, that means:

- keep the modular monolith in `Backend/`
- keep the feature-first frontend in `Frontend/`
- keep `ai-models/` for retrieval, seeding, experiments, and offline evaluation support
- standardize runtime inference on env-driven Gemma 4 through Ollama, with `gemma4:e2b` as the conservative local default and `gemma4:e4b` as the stronger override on larger hardware
- remove dependency on cloud-first assumptions such as OpenAI, Anthropic, LangChain routing, and Pinecone-first architecture

## 2. What We Have Right Now

The current repo is a good base for this migration, but the AI layer is only partially real.

| Area | Current state in repo | What it means |
|---|---|---|
| Shared AI contracts | `Backend/apps/core/ai_contracts.py` already defines `AIInvocationMetadata` and stable request/response contracts | This should remain the integration backbone |
| Assessment flow | `Backend/apps/assessments/services.py` still uses `BaselineAssessmentAnalyzer`; question generation is still a TODO | Assessment is contract-ready but not truly model-backed |
| Roadmap flow | `Backend/apps/roadmaps/services.py` still builds mostly static milestone structures in `_create_mvp_structure()` | Roadmap generation is deterministic scaffolding, not personalized AI generation |
| Advisory flow | `Backend/apps/advisory/llm_service.py` already bridges to `ai-models/src/rag/generator.py` through a local Ollama path | Advisory is the most advanced AI path, but it is still centered on `mistral` and contains a brittle `sys.path` bridge |
| Retrieval stack | `ai-models/src/rag/` already contains Chroma vector-store, embeddings, retrieval, and prompt assembly utilities | The project already has the right RAG direction and should keep building on it |
| Async infrastructure | Celery settings exist in `Backend/config/settings/*.py`, but there are no real AI task modules yet | Async AI processing is planned but not operationalized |
| Frontend integration | The rebuilt frontend already has feature boundaries and contract tests for assessments, roadmaps, and jobs | Frontend can absorb AI-state improvements without redesigning architecture again |
| Documentation and dependencies | `docs/product/ARCHITECTURE.md`, `Backend/README.md`, and `Backend/requirements.txt` still reference OpenAI, Anthropic, LangChain, and Pinecone | Documentation and dependency story are out of sync with the desired local-Gemma approach |

## 3. Target Architecture to Apply

### 3.1 Core runtime model

Sha8alny should run one env-configurable LLM model locally:

- **Model:** `OLLAMA_MODEL`, default `gemma4:e2b`, commonly overridden to `gemma4:e4b` on stronger hardware
- **Runtime:** Ollama
- **Concurrency model:** one active LLM inference at a time
- **Primary AI features:** assessment generation/evaluation, roadmap personalization, advisory chat

### 3.2 Orchestration model

All orchestration stays deterministic inside Django services:

- endpoint decides workflow
- service assembles context
- shared Gemma client performs one model call
- validation layer parses and verifies output
- service stores results or falls back

There should be no planner agent, reviewer agent, memory agent, or tool-calling agent layer.

### 3.3 Runtime ownership boundaries

| Path | Responsibility in target state |
|---|---|
| `Backend/apps/core/ai_contracts.py` | Shared request/response contracts and invocation metadata |
| `Backend/apps/core/` new AI helpers | Shared `GemmaClient`, JSON validation, retry policy, logging helpers, health checks |
| `Backend/apps/assessments/` | Assessment-specific prompts, tasks, persistence, API contract |
| `Backend/apps/roadmaps/` | Roadmap generation orchestration, deterministic structure, persistence |
| `Backend/apps/advisory/` | Advisory orchestration, history management, RAG response generation |
| `Backend/apps/jobs/` | Later-stage job skill extraction and matching enhancements |
| `Frontend/src/features/*` | Async state handling, result rendering, polling/status surfaces |
| `ai-models/src/rag/` | Retrieval, chunking, embedding, vector-store utilities, seeding scripts, evaluation tools |
| `ai-models/data/` | Knowledge base, seeded content, vector store persistence for development |

### 3.4 Required new shared runtime pieces

The backend should add a small shared AI runtime layer instead of embedding Ollama logic in each feature:

- `Backend/apps/core/gemma_client.py`
- `Backend/apps/core/ai_validation.py`
- `Backend/apps/core/ai_logging.py`
- `Backend/apps/core/ai_settings.py`
- `Backend/apps/core/health_checks.py`

These modules should cover:

- Ollama request execution
- model selection through environment variables
- timeout and retry behavior
- JSON extraction from raw model output
- schema validation
- trace ID generation and logging
- standard metadata mapping into `AIInvocationMetadata`

## 4. Architecture Decisions We Should Lock Immediately

These decisions should be treated as project rules for this rollout:

1. **No multi-agent orchestration.** The backend controls workflow with Python services and Celery tasks.
2. **One LLM call per user action whenever possible.** Do not chain multiple synchronous model calls in request/response paths.
3. **Assessment, roadmap, and advisory all use the same shared Gemma client.** No per-feature direct Ollama implementations.
4. **RAG is mandatory for advisory and recommended for job extraction.** Do not rely on unguided general-model answers for domain-specific advice.
5. **Every LLM-backed feature must have a deterministic fallback.** Fallback quality can be simpler, but the product must not dead-end.
6. **Celery handles long-running AI work.** Configure the LLM worker effectively as a single-lane queue.
7. **`ai-models/` is not a second backend.** It is a support package for retrieval and experiments, not a parallel runtime architecture.
8. **Documentation must match reality.** The team should stop planning against OpenAI/LangChain/Pinecone assumptions if the project is committing to local Gemma.

## 5. Non-Goals for This Rollout

The team should explicitly avoid these items during the main adoption phase:

- multi-agent orchestrators
- LLM-based workflow routing
- concurrent multi-model execution
- fine-tuning or LoRA training on current hardware
- Gemma 26B production deployment on current machines
- WebSocket streaming as a first milestone
- large-scale production claims such as 300+ simultaneous AI inferences on local hardware

## 6. Performance Expectations to Reset

The current product docs still include aggressive AI performance expectations such as average AI responses under 7 seconds and support for 300+ concurrent users at MVP scale. Those targets do not match a single local-Gemma deployment on the hardware constraint described in the review.

The team should treat the rollout target as:

- non-AI API requests remain fast and synchronous
- AI requests are allowed to be queued
- assessment and roadmap generation are async-first workflows
- advisory can be near-real-time for one active user, but not for high parallel load
- demo success matters more than inflated concurrency claims

This does not mean the product is weak. It means the architecture is being aligned to the real capacity of the current machines.

## 7. Migration Strategy by Phase

### Phase 0: Alignment and Cleanup

**Duration:** 2-3 days  
**Goal:** Make the repo and team work from one architecture story before adding more AI code.

**Tasks**

- Freeze the architecture decision: deterministic workflow plus single Gemma runtime.
- Create a central environment contract for Ollama host, model name, timeouts, retry count, and queue settings.
- Update product docs that still mention OpenAI, Anthropic, LangChain orchestration, or Pinecone as the active path.
- Decide whether `ai-models` will remain imported through path bridging temporarily or be converted into a cleaner local package boundary.
- Define the AI worker operating mode: one worker process, one AI task at a time.
- Add a benchmark sheet for local hardware results so the team measures real latency instead of guessing.

**Exit criteria**

- Team agrees on the target architecture.
- All owners know which directories they own.
- Documentation stops describing the old cloud-first AI design as current reality.

### Phase 1: Shared Gemma Runtime

**Duration:** 4-5 days  
**Goal:** Build the shared backend runtime that every AI flow will call.

**Tasks**

- Create `GemmaClient` in `Backend/apps/core/`.
- Move Ollama HTTP details out of `Backend/apps/advisory/llm_service.py` and into the shared client.
- Implement response schema validation and retry-on-invalid-output logic.
- Normalize metadata logging using `AIInvocationMetadata`.
- Add health-check endpoints or management commands to verify:
  - Ollama availability
  - model availability
  - response latency
  - malformed-output retry path
- Update `ai-models/scripts/download_models.sh` to default to Gemma instead of Mistral.
- Add smoke tests around the client and validation layer.

**Exit criteria**

- One backend module can call Gemma through a shared client.
- Invalid JSON or timeout cases are handled predictably.
- Advisory no longer owns a special inference path.

### Phase 2: Assessment Modernization

**Duration:** 5-7 days  
**Goal:** Replace the baseline analyzer with a real Gemma-backed assessment flow while preserving fallback behavior.

**Tasks**

- Add question-generation prompts and schemas for assessment creation.
- Implement answer-evaluation prompts and schemas for result generation.
- Keep `BaselineAssessmentAnalyzer` as fallback, not as primary logic.
- Add Celery tasks for:
  - question generation
  - response evaluation
- Keep the staged `skills` assessment budget capped at 3 LLM calls per completed assessment:
  - stage 1 generation
  - stage 2 generation
  - final evaluation
- Extend persistence so stored results capture:
  - model metadata
  - validation failures
  - fallback usage
  - processing status
- Update assessment APIs to expose pending, completed, and failed states cleanly.
- Update the frontend assessment flow to handle async loading, retry, and explicit failure states.

**Exit criteria**

- A user can start an assessment, receive generated questions, submit answers, and receive validated Gemma-backed results.
- If Gemma fails, the system still returns a usable fallback result.

### Phase 3: Roadmap Generation Modernization

**Duration:** 5-7 days  
**Goal:** Replace static roadmap generation with a hybrid system that keeps deterministic structure and uses Gemma for personalization.

**Tasks**

- Extract current deterministic roadmap scaffolding into reusable structure helpers.
- Define a hybrid generation contract:
  - deterministic phase shell
  - Gemma-generated milestone content, descriptions, priorities, and sequencing hints
- Add roadmap generation Celery task and status tracking.
- Connect roadmap generation to assessment outputs through the shared contracts layer.
- Implement course matching through embeddings and metadata filters, not through a second LLM call.
- Update roadmap serializers and frontend contracts for richer AI-backed content.
- Preserve a template-only fallback path if Gemma output is invalid.

**Exit criteria**

- Roadmaps are personalized from actual assessment results.
- Course matching works deterministically from embeddings and available course metadata.
- Roadmap generation does not depend on multiple chained LLM calls in the request cycle.

### Phase 4: Advisory and RAG Hardening

**Duration:** 5-7 days  
**Goal:** Make advisory the most reliable AI experience in the product.

**Tasks**

- Replace advisory's hardcoded `mistral` usage with the shared Gemma runtime.
- Refactor `Backend/apps/advisory/llm_service.py` to stop owning transport logic and focus on advisory orchestration.
- Tighten context assembly:
  - last messages only
  - active roadmap summary
  - latest assessment summary
  - bounded retrieved context
- Audit and improve `ai-models/src/rag/` chunking, retrieval quality, and knowledge-source metadata.
- Add advisory evaluation cases for in-scope, out-of-scope, and fallback scenarios.
- Add storage for trace IDs and error states so failed responses are explainable in logs.

**Exit criteria**

- Advisory uses Gemma through the shared client.
- Advisory answers are grounded in retrieved content and user context.
- Context length is actively budgeted rather than blindly appended.

### Phase 5: Integration, Jobs, Observability, and Demo Readiness

**Duration:** 4-6 days  
**Goal:** Make the architecture demonstrable and safe for the graduation-project demo.

**Tasks**

- Add structured logs for every LLM invocation.
- Add a lightweight benchmark suite for question generation, evaluation, roadmap generation, and advisory latency.
- Align the jobs module with the new direction:
  - optional job skill extraction through Gemma
  - deterministic normalization and ranking
- Verify frontend status handling across assessments, roadmaps, and advisory.
- Update setup docs, demo scripts, and operator runbooks.
- Create a known-good demo dataset for at least three user personas.

**Exit criteria**

- The team can demo the AI flows end-to-end without hidden manual setup.
- The logs explain which model ran, how long it took, and whether fallback was used.

## 8. Recommended File-Level Migration Targets

These are the highest-value file targets for the rollout.

| Area | Create or modify |
|---|---|
| Shared AI runtime | `Backend/apps/core/ai_contracts.py`, `Backend/apps/core/gemma_client.py`, `Backend/apps/core/ai_validation.py`, `Backend/apps/core/ai_logging.py` |
| Assessment | `Backend/apps/assessments/services.py`, `Backend/apps/assessments/views.py`, `Backend/apps/assessments/serializers.py`, `Backend/apps/assessments/tasks.py`, `Backend/apps/assessments/tests/` |
| Roadmap | `Backend/apps/roadmaps/services.py`, `Backend/apps/roadmaps/serializers.py`, `Backend/apps/roadmaps/views.py`, `Backend/apps/roadmaps/tasks.py`, `Backend/apps/roadmaps/tests/` |
| Advisory | `Backend/apps/advisory/llm_service.py`, `Backend/apps/advisory/services.py`, `Backend/apps/advisory/views.py`, `Backend/apps/advisory/tasks.py`, `Backend/apps/advisory/tests.py` |
| Retrieval | `ai-models/src/rag/generator.py`, `ai-models/src/rag/retriever.py`, `ai-models/src/rag/vector_store.py`, `ai-models/src/rag/build_vector_db.py`, `ai-models/src/rag/seeder.py` |
| Model setup | `ai-models/scripts/download_models.sh`, `ai-models/README.md`, `ai-models/requirements.txt` |
| Docs and config | `docs/product/ARCHITECTURE.md`, `docs/product/TECH_STACK.md`, `Backend/README.md`, `Backend/requirements.txt`, `Backend/config/settings/*.py` |
| Frontend integration | `Frontend/src/lib/api.ts`, `Frontend/src/features/assessment/`, `Frontend/src/features/roadmap/`, `Frontend/src/features/advisory/`, `Frontend/src/features/jobs/` |

## 9. Feasible Team Split for 5 People

The safest split is by bounded ownership, not by abstract roles.

| Person | Ownership | Main directories |
|---|---|---|
| Person 1 | Shared AI platform and runtime | `Backend/apps/core/`, `Backend/config/settings/`, `ai-models/scripts/`, core docs |
| Person 2 | Assessment end-to-end | `Backend/apps/assessments/`, `Frontend/src/features/assessment/` |
| Person 3 | Roadmap and course matching | `Backend/apps/roadmaps/`, `Backend/apps/courses/`, `Frontend/src/features/roadmap/` |
| Person 4 | Advisory and RAG | `Backend/apps/advisory/`, `ai-models/src/rag/`, `Frontend/src/features/advisory/` |
| Person 5 | Integration, observability, jobs, and demo QA | `Backend/apps/jobs/`, `Backend/apps/notifications/`, `Frontend/src/features/jobs/`, docs, benchmarks, integration tests |

### Person 1: Shared AI Platform

**Mission:** Build the runtime that everyone else depends on.

**Tasks**

- Add shared Gemma client and response-validation utilities.
- Standardize env vars and config defaults.
- Replace model-specific transport code in advisory with shared infrastructure.
- Add health checks and smoke tests.
- Update model download/setup scripts.
- Own doc corrections for architecture and runtime setup.

**Done when**

- Other owners can call the same client without duplicating transport code.
- Ollama + Gemma setup is documented and reproducible.

### Person 2: Assessment Flow

**Mission:** Deliver the first real Gemma-backed workflow.

**Tasks**

- Design assessment question and evaluation schemas.
- Replace primary use of `BaselineAssessmentAnalyzer`.
- Add async task processing and status handling.
- Extend backend tests for valid output, invalid output, fallback, and serialization.
- Update frontend assessment pages to show loading, failure, and AI metadata cleanly.

**Done when**

- Assessment creation and result generation work end-to-end with Gemma and fallback.

### Person 3: Roadmap and Course Matching

**Mission:** Turn static roadmap generation into a personalized system.

**Tasks**

- Refactor the current roadmap structure builder into deterministic template utilities.
- Add hybrid AI generation for milestone content and sequencing.
- Implement course-to-milestone matching using embeddings and course metadata.
- Update roadmap serializers and frontend contract expectations.
- Add regression tests for roadmap structure stability.

**Done when**

- A completed assessment can produce a personalized roadmap with matched learning resources.

### Person 4: Advisory and RAG

**Mission:** Make advisory the strongest and most reliable AI feature.

**Tasks**

- Migrate advisory inference to the shared Gemma runtime.
- Improve retrieval relevance and context budgeting.
- Audit and expand the knowledge base for Egyptian-market career guidance.
- Add advisory test cases covering in-scope, out-of-scope, missing context, and fallback paths.
- Update the frontend advisory UI for explicit pending and error states.

**Done when**

- Advisory responses are grounded, personalized, and no longer tied to the old Mistral-only implementation.

### Person 5: Integration, Jobs, Observability, Demo

**Mission:** Keep the system shippable while others build features.

**Tasks**

- Add benchmark scripts and latency tracking.
- Add integration tests across assessment -> roadmap -> advisory flows.
- Update jobs module planning for optional Gemma-based skill extraction and deterministic ranking.
- Wire notification or polling expectations for async AI completion.
- Maintain rollout checklist, demo dataset, and final operator docs.

**Done when**

- The team can prove the architecture works end-to-end and can demo it reliably.

## 10. Suggested 4-Week Execution Calendar

| Week | Person 1 | Person 2 | Person 3 | Person 4 | Person 5 |
|---|---|---|---|---|---|
| Week 1 | Shared Gemma runtime, config, health checks | Assessment schemas and service refactor | Roadmap contract review and structure refactor | RAG audit, knowledge-base cleanup, advisory context review | Docs cleanup, benchmark sheet, integration test plan |
| Week 2 | Validation/retry/logging, task skeletons | Question generation and evaluation tasks | Hybrid roadmap generation and serializers | Shared-client advisory migration | Frontend async-state wiring and status contracts |
| Week 3 | Infra hardening and smoke tests | Assessment frontend integration and fallback testing | Course matching and roadmap frontend integration | Advisory testing, retrieval tuning, fallback paths | Jobs alignment, observability, end-to-end test harness |
| Week 4 | Release support and cleanup | Bug fixes and demo readiness | Bug fixes and demo readiness | Bug fixes and demo readiness | Full demo rehearsal, docs, benchmark summary |

## 11. Dependency Order

The team should respect these dependencies to avoid blocking itself:

1. Person 1 must finish the shared Gemma runtime first.
2. Person 2 and Person 4 can start schema and service refactors in parallel before the runtime is complete.
3. Person 3 should begin by extracting deterministic roadmap structure, then plug Gemma in after the shared runtime lands.
4. Person 5 should start immediately on docs, benchmarks, and integration planning rather than waiting for feature completion.
5. Frontend UI changes should follow stable backend status contracts, not guessed temporary payloads.

## 12. Risk Register and Mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Malformed JSON from Gemma | Can break assessment and roadmap persistence | Validate every structured response and retry with explicit error feedback |
| Slow local inference | Can make sync flows feel broken | Keep to one LLM call per action and offload long jobs to Celery |
| Old docs keep steering decisions | Team may keep implementing the wrong architecture | Update docs in Phase 0 and treat this file as the active rollout source |
| Advisory context bloat | Gemma quality drops if prompts become too large | Enforce bounded history and bounded retrieved context |
| Queue bottleneck under demo load | Local hardware only supports one active inference lane | Use async processing, explicit statuses, and controlled demo traffic |
| Frontend assumes immediate completion | Async workflows will look flaky | Add clear pending, retry, and failed states in UI |

## 13. Success Criteria

This rollout is successful when all of the following are true:

- `gemma4:e4b` is the standard local runtime for AI features
- assessments, roadmaps, and advisory all call the same shared backend client
- each AI workflow has validation, metadata, and deterministic fallback
- advisory uses grounded retrieval instead of generic unsupported answers
- roadmap generation is personalized without becoming an agentic workflow
- the repo docs match the actual deployed architecture
- the team can run and demo the full flow locally with repeatable setup steps

## 14. Immediate Start Checklist

If the team wants to begin tomorrow, the first execution block should be:

1. Approve this architecture direction and stop all multi-agent design work.
2. Create five branches or tickets aligned to the five ownership areas above.
3. Have Person 1 implement the shared Gemma runtime contract first.
4. Have Person 2 and Person 3 define assessment and roadmap JSON schemas in parallel.
5. Have Person 4 audit the current knowledge base and retrieval quality.
6. Have Person 5 update the docs and set up the benchmark sheet and integration checklist.
7. Switch all model setup docs from Mistral-first to Gemma-first.
8. Add AI task modules in backend apps before wiring heavy async flows.
9. Define demo personas and sample data early so the team builds against realistic inputs.
10. Review progress at the end of Week 1 against the exit criteria for Phase 1.

## 15. Final Recommendation

Sha8alny should move forward with a **single-model, deterministic, workflow-first AI architecture**. The current codebase already contains the right foundations:

- stable contracts in `Backend/apps/core/ai_contracts.py`
- a modular backend structure
- a retrieval layer in `ai-models/src/rag/`
- a frontend already organized around clear feature boundaries

The right move now is not to invent more agents. The right move is to unify the runtime, replace the placeholder logic in assessment and roadmap services, harden advisory, and make the system demonstrably reliable on the hardware the team already has.
