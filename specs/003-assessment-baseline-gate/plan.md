# Implementation Plan: Staged Assessment Baseline Review Gate

**Branch**: `[003-assessment-baseline-gate]` | **Date**: 2026-04-21 | **Spec**: [/Users/mohamed3wes/Downloads/Grad-Project/specs/003-assessment-baseline-gate/spec.md](/Users/mohamed3wes/Downloads/Grad-Project/specs/003-assessment-baseline-gate/spec.md)  
**Input**: Feature specification from `/specs/003-assessment-baseline-gate/spec.md`

## Summary

Review-gate the current staged-assessment candidate on `003-assessment-baseline-gate` and decide whether it becomes the new implementation baseline for follow-on work. The candidate already changes role-graph shape, cache/version semantics, deterministic fallback behavior, roadmap-signal generation, and frontend/backend contracts in one slice, so this plan treats it as a baseline candidate rather than an assumed baseline. The intended output is a human decision of `accept`, `revise`, or `reject`, supported by explicit evidence across code, tests, contracts, and manual workflow checks.

## Technical Context

**Language/Version**: Python 3.13 backend; TypeScript 5.8 on React 18.3 frontend  
**Primary Dependencies**: Django 5, Django REST Framework, Celery, Redis cache/broker, Simple JWT, local Gemma via Ollama, React Router 6, TanStack Query 5, Vitest, Testing Library  
**Storage**: Existing Django relational persistence with JSON-backed assessment payloads; Redis-backed cache in base/production; SQLite acceptable in development  
**Testing**: pytest for backend unit, integration, and contract coverage; Django `manage.py check`; Vitest plus Testing Library for frontend assessment flows  
**Target Platform**: Modular-monolith web application with Django backend, React SPA frontend, local Ollama runtime, and Redis-backed async support in non-local environments  
**Project Type**: Web application with Django backend, React frontend, and support-only `ai-models/` package  
**Performance Goals**: Preserve staged-flow invariants of 5 stage-one questions, 5 stage-two questions, version-bound stage-one cache reuse, and no more than 3 LLM calls per completed assessment  
**Constraints**: Human baseline decision is mandatory; no new runtime boundary may be introduced; fallback behavior must remain deterministic; legacy assessment records must remain readable; typed frontend and roadmap consumers must not absorb undocumented contract drift  
**Scale/Scope**: Baseline gate covers six supported roles, the curated role-graph handoff in `Backend/apps/assessments/role_graph_data.py`, backend staged-assessment runtime behavior, roadmap-consumer semantics, and typed frontend assessment contracts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Module boundaries**: PASS. The candidate is confined to `Backend/apps/assessments/`, `Backend/apps/roadmaps/`, and existing typed frontend consumers in `Frontend/src/lib/` and `Frontend/src/features/assessment/`. No new service boundary is proposed.
- **Contract impact**: PASS with explicit review scope. The gate must review staged assessment API payloads, role-graph loader expectations, roadmap-signal shape, and frontend `AssessmentSubmissionState` compatibility before the working tree is treated as baseline.
- **Verification**: PASS only with mandatory evidence. Targeted backend tests, roadmap consumer checks, frontend contract review, and a manual staged-flow walkthrough are required before a decision is recorded.
- **AI/data handling**: PASS. Inputs remain limited to user assessment answers, target-career context, and derived capability signals. The baseline gate is specifically responsible for confirming deterministic fallback still produces valid completion behavior.
- **Operational visibility**: PASS with blocking checks. Cache/version metadata, fallback usage, and staged completion signals must remain observable enough to debug rollout failures.

## Project Structure

### Documentation (this feature)

```text
specs/003-assessment-baseline-gate/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── checklists/
│   ├── requirements.md
│   └── role-graph-curation.md
├── contracts/
│   ├── assessment-staged-api.md
│   ├── baseline-review-gate.md
│   ├── roadmap-signal-contract.md
│   └── role-graph-handoff.md
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

**Structure Decision**: Keep the existing web-application split. The review gate evaluates whether the current backend-heavy candidate can become the branch baseline without forcing a new runtime abstraction or hidden contract migration.

## Review Gate Scope

### Candidate files under direct review

- `Backend/apps/assessments/role_graph_data.py`
- `Backend/apps/assessments/role_graph.py`
- `Backend/apps/assessments/ai_pipeline.py`
- `Backend/apps/assessments/services.py`
- `Backend/apps/assessments/tests/test_engine.py`
- `Backend/apps/assessments/tests/test_role_graph.py`
- `Backend/apps/assessments/tests/test_stage_cache.py`
- `Backend/apps/assessments/tests/test_staged_flow.py`
- `Frontend/src/lib/api.ts`
- `Backend/apps/roadmaps/services.py`

### Out of scope for this gate

- Unrelated frontend visual redesign work
- New feature expansion beyond the current staged `skills` assessment scope
- Re-architecting AI runtime ownership away from the existing Django orchestration

### Decision states

- `accept`: the current working tree becomes the new baseline for continued implementation.
- `revise`: the direction is kept, but the current working tree cannot become baseline until named blockers are fixed.
- `reject`: the working tree is not fit to become baseline and follow-on implementation must not build on it.

## Gate Matrix

| Surface | Key review question | Required evidence | Blocking failure |
|---------|---------------------|-------------------|------------------|
| Role graph shape and loader contract | Does the curated candidate preserve supported-role coverage, exact graph ownership, and explicit load failures? | `test_role_graph.py`, `role-graph-handoff.md`, `checklists/role-graph-curation.md`, code review of `role_graph.py` and `role_graph_data.py` | Missing supported role, key mismatch, invalid graph shape, or silent handoff drift |
| Cache and version semantics | Does stage-one caching stay safely version-bound when curated content changes? | `test_stage_cache.py`, cache-key review, metadata inspection | Version-insensitive cache reuse or undocumented cache-key contract change |
| Fallback behavior and LLM budget | Can the staged flow still complete deterministically within the 3-call ceiling? | `test_staged_flow.py`, `test_engine.py`, `ai_pipeline.py` review | Broken fallback completion path or more than 3 calls per completed assessment |
| Roadmap signal and recommendations | Does the candidate generate roadmap-ready output without drifting from roadmap consumer expectations? | `roadmap-signal-contract.md`, `Backend/apps/roadmaps/services.py`, staged result tests | Missing structured signal, invalid priority/prerequisite data, or consumer mismatch |
| Frontend/backend contract compatibility | Do API payloads and typed frontend states still line up exactly? | `assessment-staged-api.md`, `Backend/apps/assessments/tests/test_frontend_contracts.py`, `Frontend/src/lib/api.ts` | Undocumented payload drift, missing state union coverage, or ambiguous frontend rendering contract |
| Legacy compatibility and observability | Are legacy records still readable and are failure/cache/fallback signals inspectable? | serializer/view review, result contract review, manual walkthrough | Old records become unreadable or rollout diagnosis depends on guesswork |

## Phase 0: Outline and Research

1. Inventory the current working tree diff and isolate the contract-bearing files from general code churn.
2. Resolve all review ambiguities by writing down the baseline-decision policy, required evidence, and blocking conditions in `research.md`.
3. Confirm the gate is reviewing the staged-assessment working tree rather than Git staging state so the decision target stays unambiguous.

**Phase 0 Output**: `research.md`

## Phase 1: Design and Contracts

1. Define the review-gate entities that govern evidence, criteria, and the final decision record in `data-model.md`.
2. Document the staged API, role-graph handoff, and roadmap-signal contracts as stable acceptance targets for the review.
3. Add a dedicated `baseline-review-gate.md` contract describing outcome states, evidence requirements, and decision-record shape.
4. Write `quickstart.md` as the operational runbook for executing the gate end-to-end.

**Phase 1 Output**: `data-model.md`, `contracts/*`, `quickstart.md`

## Phase 2: Planning

1. Generate implementation tasks that collect evidence, review each blocking surface, and record a final human decision.
2. Keep decision logging separate from fix execution so the team can clearly distinguish "candidate accepted" from "candidate needs revision."
3. Treat any blocker found during gate execution as a branch-level stop sign until the decision is updated.

**Phase 2 Output**: `tasks.md` to be generated later by `/speckit.tasks`

## Post-Design Constitution Check

- **Module boundaries**: PASS. The gate keeps all review work inside the existing modular-monolith boundaries and reviews changed ownership rather than creating new ownership.
- **Contract-first interfaces**: PASS. The gate now has explicit contracts for staged assessment payloads, role-graph handoff, roadmap-signal output, and the baseline-decision process itself.
- **Testable business logic**: PASS. Blocking review surfaces map directly to automated backend checks and typed frontend contract validation.
- **Responsible AI & data protection**: PASS. Deterministic fallback and explicit generation metadata remain non-negotiable acceptance conditions.
- **Operational visibility & simplicity**: PASS. The plan avoids introducing more machinery and instead forces a decision on whether the current working tree is safe to build on.

## Complexity Tracking

No constitutional violations are currently justified for this review gate.
