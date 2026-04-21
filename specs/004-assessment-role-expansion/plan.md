# Implementation Plan: Assessment Role Baseline Expansion

**Branch**: `[004-assessment-role-expansion]` | **Date**: 2026-04-21 | **Spec**: [/Users/mohamed3wes/Downloads/Grad-Project/specs/004-assessment-role-expansion/spec.md](/Users/mohamed3wes/Downloads/Grad-Project/specs/004-assessment-role-expansion/spec.md)
**Input**: Feature specification from `/specs/004-assessment-role-expansion/spec.md`

## Summary

Expand the staged assessment runtime baseline to eight approved roles while preserving legacy alias behavior and the current runtime graph contract. The change lands atomically: new curated graphs are added first, alias resolution is made label-precise, `SUPPORTED_ROLES` flips only after the new graphs exist, and product-facing consumers are synchronized to the new inventory. `origin/feature/skill-graph` remains an offline authoring input, not a runtime dependency.

## Technical Context

**Language/Version**: Python 3.13 backend; TypeScript 5.8 on React 18.3 frontend  
**Primary Dependencies**: Django 5, Django REST Framework, Celery, Redis cache/broker, local Gemma via Ollama, React Router 6, TanStack Query 5, Vitest, Testing Library  
**Storage**: Existing Django persistence; JSON-backed assessment payloads; cache keys bound to role key and `CURATED_VERSION`  
**Testing**: pytest backend suites, Django `manage.py check`, Vitest for the assessment picker  
**Constraints**: No API wire-shape change; no historical assessment backfill; keep the graph shape at 4 dimensions × 4 subskills per role in this wave  
**Scale/Scope**: Eight approved assessment roles only; broader mined inventory remains offline

## Architecture

1. **Documentation track**: Create a new 004 spec/plan/tasks set so the role-expansion wave is tracked independently from the already-shipped 002 staged-assessment work.
2. **Atomic backend inventory change**: Add the new curated graphs in `role_graph_data.py`, update `resolve_role_key(...)`, then flip `SUPPORTED_ROLES` and `CURATED_VERSION` in the same code change.
3. **Compatibility policy**: Keep ambiguous legacy strings routed to their pre-expansion meaning (`machine learning` and `ml` remain `data_science`; `ui` remains `frontend`), but route precise product labels to the new first-class roles.
4. **Consumer sync**: Update the frontend picker and deterministic recommendation/learning-path heuristics so they operate on resolved role keys and the approved eight-role catalog.
5. **Verification**: Cover loader validity, alias routing, cache invalidation, staged flow on new roles, and frontend picker submission.

## Key Decisions

- `mobile` becomes alias-only and resolves to `android`; it is no longer an approved first-class runtime role key.
- `Machine Learning Engineer` is first-class, but generic `machine learning` and `ml` remain compatibility aliases to `data_science`.
- `UI/UX Designer` is first-class, but generic `ui` remains a compatibility alias to `frontend`.
- A single `CURATED_VERSION` is retained for this wave even though the version bump invalidates cache for unchanged roles too.

## Deliverables

- New 004 docs: `spec.md`, `plan.md`, `tasks.md`
- Expanded curated runtime graphs in `Backend/apps/assessments/role_graph_data.py`
- Updated role resolution and supported-role inventory in `Backend/apps/assessments/role_graph.py`
- Updated deterministic heuristics in `Backend/apps/assessments/services.py`
- Updated frontend picker in `Frontend/src/features/assessment/routes/AssessmentPage.tsx`
- Updated backend/frontend tests for aliases, runtime inventory, new roles, and cache invalidation
