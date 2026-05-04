# Tasks: Two-Stage Adaptive Assessment Question Generation

**Input**: Design documents from `/specs/002-ai-rag-experiment/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Include test tasks whenever business logic, API behavior, data handling, or
user-critical flows change. If no automated test is possible yet, include the
required build/manual verification task and explain why.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare local cache, verification scaffolding, and acceptance notes shared by all staged-assessment work.

- [X] T001 Set the cache backend via the `DJANGO_CACHE_BACKEND` environment variable with default `django.core.cache.backends.locmem.LocMemCache` when unset (no external setup required), and allow production deployments to override this to Redis or equivalent in `Backend/config/settings/base.py` and `Backend/config/settings/development.py`
- [X] T002 [P] Add staged-assessment backend test scaffolding in `Backend/apps/assessments/tests/test_role_graph.py`, `Backend/apps/assessments/tests/test_engine.py`, `Backend/apps/assessments/tests/test_stage_cache.py`, and `Backend/apps/assessments/tests/test_staged_flow.py`
- [X] T003 [P] Extend stage-aware frontend test scaffolding in `Frontend/src/features/assessment/routes/AssessmentPage.test.tsx`, `Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx`, and `Frontend/src/features/assessment/routes/AssessmentResultsPage.test.tsx`
- [X] T004 [P] Add staged-assessment manual verification and fallback checkpoints in `specs/002-ai-rag-experiment/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create the shared contracts, persistence, and compatibility layer that block every user story.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T005 Implement role-graph dataclasses, supported-role resolution, loader entry point, and validation hooks in `Backend/apps/assessments/role_graph.py`
- [X] T006 Create six-role stub role-graph content in `Backend/apps/assessments/role_graph_data.py`
- [X] T007 [P] Add staged-assessment contracts for `StageQuestion`, `SubSkillEvidence`, `GapProfile`, and `RoadmapSignal` in `Backend/apps/core/ai_contracts.py`
- [X] T008 [P] Add staged assessment/result schema definitions and migration only, with no serializer, view, or service changes, in `Backend/apps/assessments/models.py` and `Backend/apps/assessments/migrations/0004_staged_assessment_fields.py`
- [X] T009 Extend shared assessment serializers and typed frontend models for staged fields in `Backend/apps/assessments/serializers.py` and `Frontend/src/lib/api.ts`
- [X] T010 [P] Add shared cache, fallback, and trace metadata helpers for the staged assessment flow in `Backend/apps/assessments/tasks.py` and `Backend/apps/core/ai_logging.py`
- [X] T011 Implement legacy-versus-staged transition helpers in `Backend/apps/assessments/services.py` and `Backend/apps/assessments/views.py`

**Checkpoint**: Shared contracts, staged persistence, and compatibility plumbing are ready. User stories can now proceed.

---

## Phase 3: User Story 1 - Receive targeted follow-up questions after an initial calibration (Priority: P1) 🎯 MVP

**Goal**: Replace the flat six-question flow with a staged skills assessment that calibrates broadly, targets follow-up questions, and completes end-to-end.

**Independent Test**: Create a new `skills` assessment for a supported role, wait for stage one to load, submit stage-one answers, confirm the analyzing transition leads to targeted stage-two questions, complete stage two, and receive a finished assessment result.

### Tests for User Story 1

- [X] T012 [P] [US1] Add deterministic allocation and gap-scoring tests in `Backend/apps/assessments/tests/test_engine.py`
- [X] T013 [P] [US1] Add staged assessment lifecycle and API tests in `Backend/apps/assessments/tests/test_staged_flow.py` and `Backend/apps/assessments/tests/test_api.py`
- [X] T014 [P] [US1] Add stage-one and stage-two frontend flow tests in `Frontend/src/features/assessment/routes/AssessmentPage.test.tsx` and `Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement deterministic stage allocators, answer scoring, confidence calculation, and gap-profile building in `Backend/apps/assessments/engine.py`
- [X] T016 [US1] Refactor stage-one and stage-two question generation with validation, cache lookup, and deterministic fallback in `Backend/apps/assessments/ai_pipeline.py` and `Backend/apps/core/ai_validation.py`
- [X] T017 [US1] Replace the single-stage Celery flow with staged generation and evaluation tasks in `Backend/apps/assessments/tasks.py`
- [X] T018 [US1] Implement staged assessment creation, stage submission, and transition services in `Backend/apps/assessments/services.py`
- [X] T019 [US1] Implement stage-aware create/get/submit API behavior in `Backend/apps/assessments/views.py` and `Backend/apps/assessments/serializers.py`
- [X] T020 [P] [US1] Create the between-stage transition UI in `Frontend/src/features/assessment/components/AnalyzingTransition.tsx` and `Frontend/src/features/assessment/components/AssessmentProgressRail.tsx`
- [X] T021 [US1] Update assessment creation and session routing for staged question loading and submission in `Frontend/src/features/assessment/routes/AssessmentPage.tsx` and `Frontend/src/features/assessment/routes/AssessmentSessionPage.tsx`
- [X] T022 [P] [US1] Update assessment result polling for staged completion states in `Frontend/src/features/assessment/routes/AssessmentResultsPage.tsx`

**Checkpoint**: User Story 1 is independently functional and demonstrates the new adaptive question flow.

---

## Phase 4: User Story 2 - Produce roadmap-ready capability data instead of only broad scores (Priority: P2)

**Goal**: Make completed staged assessments emit structured roadmap-ready capability output and let roadmap generation consume it directly.

**Independent Test**: Complete a staged assessment, confirm the result includes `roadmap_signal`, and create or preview a roadmap that prefers that structured signal instead of relying only on broad score summaries.

### Tests for User Story 2

- [X] T023 [P] [US2] Add roadmap-signal result serialization tests in `Backend/apps/assessments/tests/test_api.py` and `Backend/apps/assessments/tests/test_frontend_contracts.py`
- [X] T024 [P] [US2] Add roadmap integration tests for structured assessment input in `Backend/apps/roadmaps/tests/test_api.py`
- [X] T025 [P] [US2] Add frontend results-page coverage for structured gap output and roadmap CTA behavior in `Frontend/src/features/assessment/routes/AssessmentResultsPage.test.tsx`

### Implementation for User Story 2

- [X] T026 [US2] Extend final staged evaluation to build `SubSkillEvidence` and `RoadmapSignal` in `Backend/apps/assessments/ai_pipeline.py` and `Backend/apps/assessments/services.py`
- [X] T027 [US2] Expose `roadmap_signal` through serializers, views, and services only, with no direct `models.py` edits, in `Backend/apps/assessments/serializers.py`, `Backend/apps/assessments/views.py`, and `Backend/apps/assessments/services.py` (depends on T008 completing first)
- [X] T028 [US2] Prefer `roadmap_signal` during roadmap creation while preserving legacy fallback in `Backend/apps/roadmaps/serializers.py`, `Backend/apps/roadmaps/services.py`, and `Backend/apps/roadmaps/views.py`
- [X] T029 [P] [US2] Update structured results presentation components in `Frontend/src/features/assessment/components/AssessmentOutcomeCards.tsx` and `Frontend/src/features/assessment/components/AssessmentResultHero.tsx`
- [X] T030 [US2] Update result typing and roadmap handoff behavior in `Frontend/src/lib/api.ts` and `Frontend/src/features/assessment/routes/AssessmentResultsPage.tsx`

**Checkpoint**: User Stories 1 and 2 now produce adaptive assessments and roadmap-ready capability output.

---

## Phase 5: User Story 3 - Evolve role content independently from workflow code (Priority: P3)

**Goal**: Let curated role-graph content land through one file, fail explicitly when invalid, and preserve compatibility for legacy assessments during rollout.

**Independent Test**: Replace stub role data in `role_graph_data.py` only, confirm staged assessment still works, verify invalid graph content fails explicitly, and confirm a legacy single-stage assessment remains readable and completable.

### Tests for User Story 3

- [X] T031 [P] [US3] Add role-graph contract and curated-file replacement tests in `Backend/apps/assessments/tests/test_role_graph.py`
- [X] T032 [P] [US3] Add stage-one cache versioning tests in `Backend/apps/assessments/tests/test_stage_cache.py`
- [X] T033 [P] [US3] Add legacy assessment compatibility tests in `Backend/apps/assessments/tests/test_api.py` and `Backend/apps/assessments/tests/test_frontend_contracts.py`

### Implementation for User Story 3

- [X] T034 [US3] Harden role-graph validation, explicit load failures, and supported-role resolution in `Backend/apps/assessments/role_graph.py` and `Backend/apps/assessments/role_graph_data.py`
- [X] T035 [US3] Implement versioned stage-one cache keys and invalidation-safe generation metadata in `Backend/apps/assessments/ai_pipeline.py` and `Backend/apps/assessments/tasks.py`
- [X] T036 [US3] Complete legacy single-stage compatibility handling for assessment consumers in `Backend/apps/assessments/services.py`, `Backend/apps/assessments/views.py`, and `Frontend/src/lib/api.ts`
- [X] T037 [US3] Document single-file curated-data handoff and local cache behavior in `specs/002-ai-rag-experiment/contracts/role-graph-handoff.md` and `specs/002-ai-rag-experiment/quickstart.md`

**Checkpoint**: All three user stories are independently testable, and curated content can land without refactoring the workflow.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Align environment defaults, remove test noise, and record final feature validation.

- [X] T038 [P] Align staged-assessment model/runtime defaults and docs in `Backend/apps/core/ai_settings.py`, `Backend/README.md`, and `docs/product/GEMMA_ARCHITECTURE_ADOPTION_PLAN.md`
- [ ] T039 [P] Remove staged assessment frontend test warnings and tighten async assertions in `Frontend/src/features/assessment/routes/AssessmentResultsPage.test.tsx` and `Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx`
- [X] T040 Run the full staged-assessment quickstart verification and record final acceptance notes in `specs/002-ai-rag-experiment/quickstart.md`
- [X] T041 Add an automated FR-009 and SC-003 enforcement test that mocks all Gemma/LLM calls, runs a full staged assessment end-to-end, asserts total LLM invocation count does not exceed 3, and fails if it does in `Backend/apps/assessments/tests/test_staged_flow.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on User Story 1 because it extends the completed staged assessment output.
- **User Story 3 (Phase 5)**: Depends on User Story 1 because it hardens role-graph and compatibility behavior around the staged flow.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts immediately after Foundational and defines the MVP slice.
- **US2 (P2)**: Starts after US1 and remains independently testable once the staged flow exists.
- **US3 (P3)**: Starts after US1 and remains independent from US2, focusing on handoff safety and legacy compatibility.

### Within Each User Story

- Tests and verification tasks are defined before implementation.
- Deterministic engine and contract work come before API integration.
- Backend flow changes come before frontend route integration.
- Each story ends at an explicit checkpoint for independent validation.

### Parallel Opportunities

- Setup tasks T002-T004 can run in parallel after T001.
- Foundational tasks T007, T008, and T010 can run in parallel after T005 begins the role-graph contract.
- Within US1, test tasks T012-T014 can run in parallel, and implementation tasks T015, T020, and T022 can run in parallel once shared contracts are ready.
- Within US2, test tasks T023-T025 can run in parallel, and T029 can run in parallel with backend tasks T026-T028.
- Within US3, test tasks T031-T033 can run in parallel.
- Polish tasks T038 and T039 can run in parallel before final verification T040.

---

## Parallel Example: User Story 1

```bash
# Run US1 verification tasks together:
Task: "Add deterministic allocation and gap-scoring tests in Backend/apps/assessments/tests/test_engine.py"
Task: "Add staged assessment lifecycle and API tests in Backend/apps/assessments/tests/test_staged_flow.py and Backend/apps/assessments/tests/test_api.py"
Task: "Add stage-one and stage-two frontend flow tests in Frontend/src/features/assessment/routes/AssessmentPage.test.tsx and Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx"

# Build separate US1 areas together after contracts land:
Task: "Implement deterministic stage allocators, answer scoring, confidence calculation, and gap-profile building in Backend/apps/assessments/engine.py"
Task: "Create the between-stage transition UI in Frontend/src/features/assessment/components/AnalyzingTransition.tsx and Frontend/src/features/assessment/components/AssessmentProgressRail.tsx"
Task: "Update assessment result polling for staged completion states in Frontend/src/features/assessment/routes/AssessmentResultsPage.tsx"
```

## Parallel Example: User Story 2

```bash
# Run US2 verification tasks together:
Task: "Add roadmap-signal result serialization tests in Backend/apps/assessments/tests/test_api.py and Backend/apps/assessments/tests/test_frontend_contracts.py"
Task: "Add roadmap integration tests for structured assessment input in Backend/apps/roadmaps/tests/test_api.py"
Task: "Add frontend results-page coverage for structured gap output and roadmap CTA behavior in Frontend/src/features/assessment/routes/AssessmentResultsPage.test.tsx"

# Split backend and frontend US2 work:
Task: "Extend final staged evaluation to build SubSkillEvidence and RoadmapSignal in Backend/apps/assessments/ai_pipeline.py and Backend/apps/assessments/services.py"
Task: "Update structured results presentation components in Frontend/src/features/assessment/components/AssessmentOutcomeCards.tsx and Frontend/src/features/assessment/components/AssessmentResultHero.tsx"
```

## Parallel Example: User Story 3

```bash
# Run US3 verification tasks together:
Task: "Add role-graph contract and curated-file replacement tests in Backend/apps/assessments/tests/test_role_graph.py"
Task: "Add stage-one cache versioning tests in Backend/apps/assessments/tests/test_stage_cache.py"
Task: "Add legacy assessment compatibility tests in Backend/apps/assessments/tests/test_api.py and Backend/apps/assessments/tests/test_frontend_contracts.py"

# Split hardening and documentation work:
Task: "Harden role-graph validation, explicit load failures, and supported-role resolution in Backend/apps/assessments/role_graph.py and Backend/apps/assessments/role_graph_data.py"
Task: "Document single-file curated-data handoff and local cache behavior in specs/002-ai-rag-experiment/contracts/role-graph-handoff.md and specs/002-ai-rag-experiment/quickstart.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate the staged adaptive assessment flow end-to-end.
5. Demo or review the adaptive question-generation slice before adding roadmap-signal work.

### Incremental Delivery

1. Finish Setup + Foundational once.
2. Ship US1 to replace the flat question flow with a staged adaptive flow.
3. Add US2 to upgrade completed assessments into roadmap-ready structured output.
4. Add US3 to harden curated-data handoff, cache versioning, and legacy compatibility.
5. Finish with Polish tasks for runtime alignment, warning cleanup, and final validation.

### Parallel Team Strategy

1. One developer handles shared contracts, models, and legacy compatibility.
2. One developer handles staged generation, deterministic scoring, and task orchestration.
3. One developer handles frontend stage-aware assessment flows and results presentation.
4. After US1 lands, split roadmap integration (US2) and handoff hardening (US3).

---

## Notes

- Every task follows the required checklist format with task ID and file path.
- `[P]` tasks are limited to work that can proceed without conflicting file ownership or incomplete prerequisites.
- Suggested MVP scope: **Phase 3 / User Story 1 only**.
- Validation is required for cache behavior, fallback behavior, staged transitions, and final roadmap-signal output before calling the feature complete.
