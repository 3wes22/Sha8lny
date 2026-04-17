# Implementation Plan: Two-Stage Adaptive Assessment Question Generation

**Branch**: `[002-ai-rag-experiment]` | **Date**: 2026-04-14 | **Spec**: [/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/spec.md](/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/spec.md)  
**Input**: Feature specification from `/specs/002-ai-rag-experiment/spec.md`

## Summary

Replace the current flat six-question role bank for new `skills` assessments with a staged adaptive flow that delivers five calibration questions followed by five targeted follow-up questions, while preserving the project’s deterministic local-Gemma architecture and keeping compute cost bounded to a maximum of 3 LLM calls per completed assessment: Stage 1 generation (call 1), Stage 2 generation (call 2), and final evaluation (call 3). The design keeps production orchestration in `Backend/`, introduces a role-graph loader contract plus stub data for parallel content handoff, adds deterministic mid-stage scoring and cache-backed stage-one reuse, and upgrades the assessment result contract to produce roadmap-ready structured capability data rather than only broad scores and prose.

## Technical Context

**Language/Version**: Python 3.13 backend; TypeScript 5.8 on React 18.3 frontend  
**Primary Dependencies**: Django 5, Django REST Framework, Celery, Redis cache/broker, Simple JWT, local Gemma via Ollama, React Router 6, TanStack Query 5, Vitest, Testing Library  
**Storage**: Existing Django relational persistence with JSON-backed assessment payloads; Redis-backed cache and queue in base/production; SQLite remains acceptable in development  
**Testing**: pytest for backend unit/integration/contract coverage, Django `manage.py check`, Vitest + Testing Library for frontend assessment flows  
**Target Platform**: Modular-monolith web application with desktop/mobile frontend, local Ollama runtime, and single-lane AI worker queue  
**Project Type**: Web application with Django backend, React SPA frontend, and support-only `ai-models/` package  
**Performance Goals**: Stage-one questions become immediately reusable after cache warm-up for the same role and graph version, stage-two generation stays bounded behind an analyzing transition, and the full assessment flow records at most 3 LLM calls per completed staged assessment: Stage 1 generation (call 1), Stage 2 generation (call 2), and final evaluation (call 3)  
**Constraints**: Zero cloud-model budget, one shared local Gemma runtime, no dependency on curated role data landing before infrastructure work, deterministic fallback for every model-backed stage, backward compatibility for legacy assessments, and no new service boundary outside current monorepo modules  
**Scale/Scope**: New staged flow for `skills` assessments only, six supported roles, ten total questions per completed assessment, roadmap-ready output for downstream roadmap generation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Module boundaries**: PASS. Production logic stays inside `Backend/apps/assessments/`, `Backend/apps/core/`, `Backend/apps/roadmaps/`, and `Frontend/src/features/assessment/` plus `Frontend/src/lib/`. No new top-level runtime or cross-repo service is introduced.
- **Contract impact**: PASS. This plan defines the staged assessment API, role-graph handoff contract, and roadmap-signal contract before implementation. Typed frontend consumers in `Frontend/src/lib/api.ts` are explicitly affected.
- **Verification**: PASS with required follow-through. Backend needs new unit, integration, API, cache, and contract coverage; frontend needs stage-aware assessment session and results coverage; manual verification remains necessary for transition-state UX and fallback behavior with Ollama unavailable.
- **AI/data handling**: PASS. Inputs remain limited to assessment answers, target-career context, and derived capability signals. Local Gemma via Ollama remains the only model dependency, and deterministic fallbacks are required for both question-generation stages and final evaluation.
- **Operational visibility**: PASS. The design requires structured logging or metadata for cache hits, fallback usage, validation failures, trace IDs, and background-task state changes so the frontend never stalls silently.

## Project Structure

### Documentation (this feature)

```text
specs/002-ai-rag-experiment/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   └── requirements.md
├── contracts/
│   ├── assessment-staged-api.md
│   ├── role-graph-handoff.md
│   └── roadmap-signal-contract.md
└── tasks.md
```

### Source Code (repository root)

```text
Backend/
├── apps/
│   ├── assessments/
│   ├── core/
│   └── roadmaps/
└── config/

Frontend/
├── src/
│   ├── features/
│   │   └── assessment/
│   ├── lib/
│   └── shared/
└── package.json

ai-models/
└── src/
    └── assessment/
```

**Structure Decision**: Use the existing web-application split already adopted by the repository. All production behavior for this feature lives in the Django backend and typed React frontend, while `ai-models/` remains an offline/support area rather than a second runtime path. New shared abstractions are limited to explicit contracts and helpers inside existing modules.

## Post-Design Constitution Check

- **Module boundaries**: PASS. New abstractions are bounded to assessment runtime contracts (`role_graph`, staged engine helpers, staged serializers) and a roadmap-consumer contract inside existing apps.
- **Contract-first interfaces**: PASS. The staged API, role-graph handoff, and roadmap-signal shapes are documented before implementation tasks.
- **Testable business logic**: PASS. Deterministic scoring, cache behavior, staged transitions, and result contracts are all captured as automated test requirements in `quickstart.md`.
- **Responsible AI & data protection**: PASS. The feature keeps local Gemma bounded, model choice environment-driven, and fallback behavior explicit. No new external secrets or providers are introduced.
- **Operational visibility & simplicity**: PASS. The plan stays within the modular monolith, avoids per-question adaptive loops, and requires explicit metadata for recovery and debugging.

## Complexity Tracking

No constitutional violations are currently justified for this feature.
