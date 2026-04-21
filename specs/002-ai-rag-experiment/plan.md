# Implementation Plan: Two-Stage Adaptive Assessment Question Generation

**Branch**: `[002-ai-rag-experiment]` | **Date**: 2026-04-21 | **Spec**: [/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/spec.md](/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/spec.md)
**Input**: Feature specification from `/specs/002-ai-rag-experiment/spec.md`

## Summary

Replace the flat six-question skills assessment with a staged adaptive flow that calibrates broadly in stage one, targets weak or uncertain areas in stage two, and emits a structured roadmap-ready signal on completion. The implementation runs deterministically as Django service code, uses local Gemma via Ollama for bounded question generation, and preserves a deterministic fallback so the assessment still completes when the model is unavailable. Curated role content lives behind a single loader in `Backend/apps/assessments/role_graph_data.py` so role content can evolve without touching the workflow, and completed assessments expose a typed `roadmap_signal` that the roadmap module consumes directly.

## Technical Context

**Language/Version**: Python 3.13 backend; TypeScript 5.8 on React 18.3 frontend
**Primary Dependencies**: Django 5, Django REST Framework, Celery, Redis cache/broker, Simple JWT, local Gemma via Ollama, React Router 6, TanStack Query 5, Vitest, Testing Library
**Storage**: Existing Django relational persistence with JSON-backed assessment payloads; Redis-backed cache in base/production; SQLite acceptable in development
**Testing**: pytest for backend unit/integration/contract coverage, Django `manage.py check`, Vitest + Testing Library for frontend assessment flows
**Target Platform**: Modular-monolith web application with Django backend, React SPA frontend, local Ollama runtime, and Redis-backed async support in non-local environments
**Project Type**: Web application with Django backend, React frontend, and support-only `ai-models/` package
**Performance Goals**: Exactly 5 questions per stage, version-bound stage-one cache reuse, and no more than 3 LLM calls per completed staged assessment (stage 1 generation, stage 2 generation, final evaluation)
**Constraints**: Deterministic fallback must keep the staged flow completable without Ollama; legacy non-staged assessments must remain readable and completable; the frontend typed contract for `AssessmentSubmissionState` must stay in sync with backend payloads; role-graph edits must not require changes outside `role_graph_data.py`
**Scale/Scope**: Six supported roles (backend, frontend, data science, fullstack, mobile, devops), staged skills assessments only (other assessment types remain on their existing flow), roadmap consumer integration through `roadmap_signal`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Module boundaries**: PASS. All work lives inside `Backend/apps/assessments/`, `Backend/apps/roadmaps/`, and typed frontend consumers in `Frontend/src/lib/` and `Frontend/src/features/assessment/`. No new runtime service is introduced.
- **Contract-first interfaces**: PASS. The staged API contract, role-graph handoff contract, and roadmap-signal contract are documented in `contracts/` and covered by contract tests before implementation changes.
- **Testable business logic**: PASS. Stage allocation, gap scoring, cache versioning, fallback completion, and frontend state transitions all have explicit pytest and Vitest coverage.
- **Responsible AI & data protection**: PASS. Inputs are limited to user answers and target-career context. Generation metadata (fallback usage, cache hits, failure signals) is surfaced through the API so the runtime stays observable.
- **Operational visibility & simplicity**: PASS. The feature reuses the existing Django orchestration path, adds no new service boundary, and keeps all model configuration environment-driven.

## Project Structure

### Documentation (this feature)

```text
specs/002-ai-rag-experiment/
├── plan.md
├── spec.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── checklists/
│   ├── requirements.md
│   └── role-graph-curation.md
└── contracts/
    ├── assessment-staged-api.md
    ├── role-graph-handoff.md
    └── roadmap-signal-contract.md
```

### Source Code (repository root)

```text
Backend/
├── apps/
│   ├── assessments/
│   │   ├── role_graph.py          # Dataclasses + loader + supported-role resolution
│   │   ├── role_graph_data.py     # Curated role-graph content (single handoff file)
│   │   ├── engine.py              # Deterministic stage allocators + gap-profile builder
│   │   ├── ai_pipeline.py         # Gemma-backed generation with deterministic fallback
│   │   ├── tasks.py               # Celery staged generation + evaluation tasks
│   │   ├── services.py            # Staged creation, stage submission, transitions
│   │   ├── serializers.py         # Stage-aware payloads including roadmap_signal
│   │   └── views.py               # Stage-aware create/get/submit API
│   ├── core/
│   │   ├── ai_contracts.py        # StageQuestion, SubSkillEvidence, GapProfile, RoadmapSignal
│   │   ├── ai_validation.py       # Shared validation helpers
│   │   └── ai_settings.py         # Environment-driven AI configuration
│   └── roadmaps/
│       └── services.py            # Prefer structured roadmap_signal when creating roadmaps
└── config/

Frontend/
├── src/
│   ├── features/
│   │   └── assessment/
│   │       ├── routes/            # AssessmentPage, AssessmentSessionPage, AssessmentResultsPage
│   │       └── components/        # AnalyzingTransition, AssessmentProgressRail, outcome cards
│   ├── lib/
│   │   └── api.ts                 # AssessmentSubmissionState, staged response types
│   └── shared/
└── package.json

ai-models/
└── src/
    └── assessment/                # Support-only; no runtime ownership
```

**Structure Decision**: Keep the existing web-application split. The staged assessment runs inside the Django modular monolith and reuses existing Celery, Redis cache, and Ollama integration. No new runtime boundary is introduced.

## Architecture

### End-to-end staged flow

1. **Create** (`views.py` → `services.py`): the user picks a target career, the service resolves it to a supported role key through `role_graph.resolve_role_key`, loads the curated graph from `role_graph_data.py`, and records a staged assessment in stage one.
2. **Stage 1 generation** (`tasks.py` → `ai_pipeline.py`): the deterministic allocator in `engine.py` picks 5 stage-one targets across the role's core dimensions, and `ai_pipeline.py` either returns a cached question set (keyed by `{role_key, version}`), calls Gemma once to generate fresh questions, or falls back to deterministic questions when Gemma is unavailable or returns invalid output. Generation metadata records cache hits and fallback usage.
3. **Stage 1 submission** (`services.py` → `engine.py`): user answers are scored deterministically, the gap-profile builder ranks subskills by gap size and answer uncertainty, and the assessment transitions to stage two.
4. **Stage 2 generation** (`tasks.py` → `ai_pipeline.py`): the allocator picks 5 stage-two targets biased toward high-priority gaps and uncertain areas, and `ai_pipeline.py` calls Gemma a second time (or deterministic fallback) to generate targeted questions.
5. **Stage 2 submission + final evaluation** (`services.py` → `ai_pipeline.py`): the pipeline builds `SubSkillEvidence` per subskill, a prioritized `GapProfile`, and a typed `RoadmapSignal`. A third and final Gemma call may enrich the evaluation narrative, but the structured output is always produced deterministically so the assessment completes without Ollama.
6. **Consumer handoff** (`roadmaps/services.py`): roadmap creation prefers the structured `roadmap_signal` when present and keeps legacy score-based fallback for pre-migration assessments.

### LLM budget and fallback

- At most 3 Gemma calls per completed staged assessment: stage-1 generation, stage-2 generation, final evaluation.
- Each call path has a deterministic fallback that returns valid typed output. Fallback usage is surfaced through `generation_metadata.fallback_used` so operators can distinguish model-backed and deterministic runs.
- `tests/test_staged_flow.py::test_staged_assessment_caps_llm_invocations_at_three` enforces the budget with mocked Gemma calls.

### Role-graph handoff

- `role_graph.py` owns dataclasses (`CoreDimension`, `SubSkill`, `RoleGraph`), supported-role resolution, and the loader.
- `role_graph_data.py` owns curated content and the `CURATED_VERSION` string. Replacing curated content is a single-file change.
- The loader rejects invalid graph content with explicit errors so bad curated data fails loudly instead of degrading runtime behavior.
- Stage-one cache keys embed `CURATED_VERSION`, so bumping the version invalidates cached questions automatically when curated content changes.

### Frontend integration

- `Frontend/src/lib/api.ts` defines the `AssessmentSubmissionState` union (`pending`, `stage_1_generating`, `stage_1_ready`, `stage_1_analyzing`, `stage_2_generating`, `stage_2_ready`, `stage_2_analyzing`, `completed`, `failed`) and the staged response shape.
- The session route renders `active_questions` plus stage metadata, the analyzing transition component covers between-stage polling, and the results route surfaces the structured `roadmap_signal` and roadmap CTA.

## Phase 0: Outline and Research

1. Confirm the existing Django assessment app is the right home for the staged flow and that no new runtime boundary is required.
2. Lock down deterministic stage allocation, gap-scoring, and confidence rules so the assessment remains completable without Gemma.
3. Choose a role-graph shape that supports stage targeting, prerequisite links, version-bound caching, and single-file curated content handoff.
4. Decide on the 3-call LLM ceiling and the caching strategy that keeps stage-one generation cheap while remaining safe across curated-content updates.

**Phase 0 Output**: `research.md`

## Phase 1: Design and Contracts

1. Write `data-model.md` around the staged feature entities: `RoleGraph`, `StageQuestion`, `GapProfile`, `RoadmapSignal`, and `StagedAssessmentSession`.
2. Define the staged API contract in `contracts/assessment-staged-api.md` covering creation, stage submission, and stage/submission-state transitions.
3. Define the curated role-graph handoff contract in `contracts/role-graph-handoff.md` so curated data can land without refactoring workflow code.
4. Define the roadmap-signal contract in `contracts/roadmap-signal-contract.md` so the roadmap module can consume structured output directly.
5. Write `quickstart.md` as the operational runbook for running the staged flow end-to-end, including Gemma on/off verification.

**Phase 1 Output**: `data-model.md`, `contracts/*`, `quickstart.md`

## Phase 2: Planning

1. Produce a task breakdown in `tasks.md` grouped by user story so each story is independently testable.
2. Keep deterministic engine work, shared contracts, and persistence changes in the foundational phase that blocks all user stories.
3. Sequence user stories so User Story 1 delivers the staged flow MVP, User Story 2 adds the roadmap signal, and User Story 3 hardens the curated-content handoff and legacy compatibility.

**Phase 2 Output**: `tasks.md` to be generated by `/speckit.tasks`

## Post-Design Constitution Check

- **Module boundaries**: PASS. The plan confines all runtime changes to existing Django apps and typed frontend consumers, and keeps curated content behind a single loader file.
- **Contract-first interfaces**: PASS. Staged API, role-graph handoff, and roadmap-signal contracts are defined before implementation and exercised by dedicated contract tests.
- **Testable business logic**: PASS. Stage allocation, gap profiling, cache versioning, fallback completion, the 3-call budget, and frontend state transitions all have explicit test coverage.
- **Responsible AI & data protection**: PASS. Deterministic fallback and explicit generation metadata remain non-negotiable acceptance conditions, and model configuration stays environment-driven.
- **Operational visibility & simplicity**: PASS. The feature reuses existing orchestration, adds no new service boundary, and keeps cache, queue, and model configuration observable through metadata on the API.

## Complexity Tracking

No constitutional violations are introduced by this plan. The staged flow stays inside the existing modular-monolith boundary and the existing local Gemma architecture.
