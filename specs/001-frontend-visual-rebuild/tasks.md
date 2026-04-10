# Tasks: Sha8alny Frontend Visual Reconstruction

**Input**: Design documents from `/specs/001-frontend-visual-rebuild/`  
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

**Purpose**: Establish the reusable visual system and test scaffolding that every story will rely on.

- [X] T001 Define the editorial career-atlas design tokens, two-type hierarchy, accent color, and motion variables in `Frontend/src/index.css` and `Frontend/src/App.css`
- [X] T002 [P] Create shared page-surface primitives for cardless layouts in `Frontend/src/shared/components/PageShell.tsx`, `Frontend/src/shared/components/SectionHeader.tsx`, and `Frontend/src/shared/components/StatePanel.tsx`
- [X] T003 [P] Create reusable journey and quiz interaction primitives in `Frontend/src/shared/components/JourneyProgress.tsx`, `Frontend/src/shared/components/ChoiceCard.tsx`, and `Frontend/src/shared/components/PosterHero.tsx`
- [X] T004 [P] Extend route rendering and navigation test helpers in `Frontend/src/test/utils.tsx` and `Frontend/src/test/route-smoke.test.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Complete the shared contracts, shell, and backend support that block every user story.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [X] T005 Normalize route metadata, shared navigation state, and authenticated shell behavior in `Frontend/src/app/routes.ts`, `Frontend/src/app/AppRoutes.tsx`, and `Frontend/src/shared/layout/MainLayout.tsx`
- [X] T006 Extend typed frontend contracts for journey, assessment, job, and notification presentation state in `Frontend/src/lib/api.ts`
- [X] T007 [P] Add roadmap hierarchy and next-action response support in `Backend/apps/roadmaps/serializers.py`, `Backend/apps/roadmaps/views.py`, and `Backend/apps/roadmaps/tests/test_frontend_contracts.py`
- [X] T008 [P] Add assessment presentation and status metadata support in `Backend/apps/assessments/serializers.py`, `Backend/apps/assessments/views.py`, and `Backend/apps/assessments/tests/test_frontend_contracts.py`
- [X] T009 [P] Add job-detail/save-state and notification-summary contract updates in `Backend/apps/jobs/serializers.py`, `Backend/apps/jobs/views.py`, `Backend/apps/jobs/tests/test_frontend_contracts.py`, `Backend/apps/notifications/serializers.py`, `Backend/apps/notifications/views.py`, and `Backend/apps/notifications/tests.py`
- [X] T010 Add blocking contract and route-regression verification for shared shell behavior in `Frontend/src/test/route-smoke.test.tsx`, `Backend/apps/roadmaps/tests/test_frontend_contracts.py`, `Backend/apps/assessments/tests/test_frontend_contracts.py`, and `Backend/apps/jobs/tests/test_frontend_contracts.py`

**Checkpoint**: Shared shell, typed contracts, and backend support are ready. User stories can now proceed independently.

---

## Phase 3: User Story 1 - Explore a clearer career journey (Priority: P1) 🎯 MVP

**Goal**: Give signed-in users a roadmap.sh-inspired dashboard and roadmap experience that makes progress, hierarchy, and next steps obvious.

**Independent Test**: Sign in, land on `/dashboard`, open `/roadmap`, and confirm the shell, progress summary, and roadmap journey are readable without extra explanation.

### Tests for User Story 1

- [X] T011 [P] [US1] Add dashboard route regression coverage in `Frontend/src/features/dashboard/routes/DashboardPage.test.tsx`
- [X] T012 [P] [US1] Add roadmap journey rendering coverage in `Frontend/src/features/roadmap/routes/RoadmapPage.test.tsx`
- [X] T013 [P] [US1] Add manual acceptance checkpoints for dashboard and roadmap in `specs/001-frontend-visual-rebuild/quickstart.md`

### Implementation for User Story 1

- [X] T014 [P] [US1] Create dashboard hero and progress-summary components in `Frontend/src/features/dashboard/components/CareerAtlasHero.tsx` and `Frontend/src/features/dashboard/components/ProgressSnapshot.tsx`
- [X] T015 [P] [US1] Create atlas-style roadmap presentation components in `Frontend/src/features/roadmap/components/RoadmapAtlas.tsx`, `Frontend/src/features/roadmap/components/RoadmapNodeCard.tsx`, and `Frontend/src/features/roadmap/components/RoadmapRail.tsx`
- [X] T016 [US1] Rebuild the dashboard surface around the new journey-first layout in `Frontend/src/features/dashboard/routes/DashboardPage.tsx`
- [X] T017 [US1] Rebuild the roadmap surface with desktop atlas and mobile sequential fallback in `Frontend/src/features/roadmap/routes/RoadmapPage.tsx` and `Frontend/src/features/roadmap/components/RoadmapProgressView.tsx`
- [X] T018 [US1] Wire dashboard and roadmap components to the updated summary and hierarchy contracts in `Frontend/src/lib/api.ts`, `Frontend/src/features/dashboard/routes/DashboardPage.tsx`, and `Frontend/src/features/roadmap/routes/RoadmapPage.tsx`
- [ ] T019 [US1] Validate responsive roadmap behavior and story acceptance in `specs/001-frontend-visual-rebuild/quickstart.md`

**Checkpoint**: User Story 1 is independently functional as the MVP slice.

---

## Phase 4: User Story 2 - Complete assessments in a more engaging way (Priority: P2)

**Goal**: Turn assessment entry, question flow, and results into a professional quiz-style experience with clear progression and async state communication.

**Independent Test**: Start an assessment, move through questions, submit it, and confirm both processing and completed result states are clear and visually intentional.

### Tests for User Story 2

- [X] T020 [P] [US2] Add assessment session interaction coverage in `Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx`
- [X] T021 [P] [US2] Add assessment results processing/result-state coverage in `Frontend/src/features/assessment/routes/AssessmentResultsPage.test.tsx`
- [X] T022 [P] [US2] Add backend assessment contract regression coverage in `Backend/apps/assessments/tests/test_frontend_contracts.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Create quiz-style assessment entry and question components in `Frontend/src/features/assessment/components/AssessmentIntroHero.tsx`, `Frontend/src/features/assessment/components/AssessmentQuestionCard.tsx`, `Frontend/src/features/assessment/components/AssessmentProgressRail.tsx`, and `Frontend/src/features/assessment/components/ChoiceReveal.tsx`
- [X] T024 [P] [US2] Create assessment result-surface components in `Frontend/src/features/assessment/components/AssessmentResultHero.tsx` and `Frontend/src/features/assessment/components/AssessmentOutcomeCards.tsx`
- [X] T025 [US2] Rebuild the assessment entry and session flow in `Frontend/src/features/assessment/routes/AssessmentPage.tsx` and `Frontend/src/features/assessment/routes/AssessmentSessionPage.tsx`
- [X] T026 [US2] Rebuild the processing and results presentation in `Frontend/src/features/assessment/routes/AssessmentResultsPage.tsx`
- [X] T027 [US2] Wire quiz progression, async status handling, and next-step actions to the updated contracts in `Frontend/src/lib/api.ts`, `Frontend/src/features/assessment/routes/AssessmentSessionPage.tsx`, and `Frontend/src/features/assessment/routes/AssessmentResultsPage.tsx`
- [ ] T028 [US2] Validate assessment flow acceptance and result-state messaging in `specs/001-frontend-visual-rebuild/quickstart.md`

**Checkpoint**: User Stories 1 and 2 are both independently testable and demonstrable.

---

## Phase 5: User Story 3 - Keep the platform credible across all major flows (Priority: P3)

**Goal**: Apply the reconstructed visual system consistently across jobs, advisory, notifications, profile, settings, and public/auth surfaces without breaking route behavior or state clarity.

**Independent Test**: Navigate across `/jobs`, `/jobs/saved`, `/jobs/:jobId`, `/notifications`, `/advisor`, `/profile`, `/settings`, `/`, `/login`, and `/register` and confirm consistent layout, state treatment, and navigation behavior.

### Tests for User Story 3

- [X] T029 [P] [US3] Add jobs and notifications regression coverage in `Frontend/src/features/jobs/routes/JobsPage.test.tsx` and `Frontend/src/features/notifications/routes/NotificationsPage.test.tsx`
- [X] T030 [P] [US3] Add shared shell consistency coverage in `Frontend/src/test/app-shell-consistency.test.tsx`
- [X] T031 [P] [US3] Add backend contract regression coverage for jobs and notifications in `Backend/apps/jobs/tests/test_frontend_contracts.py` and `Backend/apps/notifications/tests.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Rebuild jobs discovery and detail surfaces in `Frontend/src/features/jobs/routes/JobsPage.tsx`, `Frontend/src/features/jobs/routes/SavedJobsPage.tsx`, and `Frontend/src/features/jobs/routes/JobDetailPage.tsx`
- [X] T033 [P] [US3] Rebuild notifications, profile, and settings surfaces in `Frontend/src/features/notifications/routes/NotificationsPage.tsx`, `Frontend/src/features/profile/routes/ProfilePage.tsx`, and `Frontend/src/features/settings/routes/SettingsPage.tsx`
- [X] T034 [P] [US3] Rebuild advisory and public/auth surfaces with a brand-first poster hero and restrained auth layouts in `Frontend/src/features/advisory/routes/AdvisoryPage.tsx`, `Frontend/src/features/marketing/routes/LandingPage.tsx`, `Frontend/src/features/auth/routes/LoginPage.tsx`, `Frontend/src/features/auth/routes/RegisterPage.tsx`, and `Frontend/src/features/auth/routes/ForgotPasswordPage.tsx`
- [X] T035 [US3] Align cross-route loading, empty, processing, and error states in `Frontend/src/shared/layout/MainLayout.tsx` and `Frontend/src/shared/components/StatePanel.tsx`
- [ ] T036 [US3] Validate cross-route consistency and responsive behavior in `specs/001-frontend-visual-rebuild/quickstart.md`

**Checkpoint**: All three user stories are now independently functional within one coherent frontend system.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improve performance, clean up warnings, and finalize delivery documentation.

- [X] T037 [P] Optimize route-level code splitting, motion performance, and lazy loading in `Frontend/src/app/AppRoutes.tsx` and `Frontend/src/App.tsx`
- [X] T038 [P] Remove current frontend test warnings and improve shared test ergonomics in `Frontend/src/features/auth/routes/LoginPage.test.tsx` and `Frontend/src/test/utils.tsx`
- [X] T039 [P] Update product-facing implementation documentation in `README.md` and `docs/product/FRONTEND_INTEGRATION.md`
- [ ] T040 Run the full quickstart validation and record final acceptance notes in `specs/001-frontend-visual-rebuild/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup completion and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational completion.
- **User Story 2 (Phase 4)**: Depends on Foundational completion.
- **User Story 3 (Phase 5)**: Depends on Foundational completion.
- **Polish (Phase 6)**: Depends on the user stories you intend to ship.

### User Story Dependencies

- **US1 (P1)**: Starts immediately after Foundational and defines the MVP slice.
- **US2 (P2)**: Starts after Foundational and remains independently testable from US1.
- **US3 (P3)**: Starts after Foundational and remains independently testable from US1 and US2.

### Within Each User Story

- Tests and acceptance checkpoints are defined before implementation tasks.
- Shared components come before route rewrites.
- Route rewrites come before final validation for that story.
- Each story stops at an explicit checkpoint for independent verification.

### Parallel Opportunities

- Setup tasks T002-T004 can run in parallel after T001 starts the design-token layer.
- Foundational backend contract tasks T007-T009 can run in parallel after T005-T006 define the frontend shell and typed consumers.
- Within US1, component tasks T014-T015 and test tasks T011-T013 can run in parallel.
- Within US2, component tasks T023-T024 and test tasks T020-T022 can run in parallel.
- Within US3, implementation tasks T032-T034 and test tasks T029-T031 can run in parallel.
- Polish tasks T037-T039 can run in parallel before T040 final validation.

---

## Parallel Example: User Story 1

```bash
# Run US1 verification tasks together:
Task: "Add dashboard route regression coverage in Frontend/src/features/dashboard/routes/DashboardPage.test.tsx"
Task: "Add roadmap journey rendering coverage in Frontend/src/features/roadmap/routes/RoadmapPage.test.tsx"
Task: "Add manual acceptance checkpoints for dashboard and roadmap in specs/001-frontend-visual-rebuild/quickstart.md"

# Build US1 visual components together:
Task: "Create dashboard hero and progress-summary components in Frontend/src/features/dashboard/components/CareerAtlasHero.tsx and Frontend/src/features/dashboard/components/ProgressSnapshot.tsx"
Task: "Create atlas-style roadmap presentation components in Frontend/src/features/roadmap/components/RoadmapAtlas.tsx and Frontend/src/features/roadmap/components/RoadmapNodeCard.tsx"
```

## Parallel Example: User Story 2

```bash
# Run US2 verification tasks together:
Task: "Add assessment session interaction coverage in Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx"
Task: "Add assessment results processing/result-state coverage in Frontend/src/features/assessment/routes/AssessmentResultsPage.test.tsx"
Task: "Add backend assessment contract regression coverage in Backend/apps/assessments/tests/test_frontend_contracts.py"

# Build US2 assessment components together:
Task: "Create quiz-style assessment entry and question components in Frontend/src/features/assessment/components/AssessmentIntroHero.tsx, Frontend/src/features/assessment/components/AssessmentQuestionCard.tsx, and Frontend/src/features/assessment/components/AssessmentProgressRail.tsx"
Task: "Create assessment result-surface components in Frontend/src/features/assessment/components/AssessmentResultHero.tsx and Frontend/src/features/assessment/components/AssessmentOutcomeCards.tsx"
```

## Parallel Example: User Story 3

```bash
# Run US3 verification tasks together:
Task: "Add jobs and notifications regression coverage in Frontend/src/features/jobs/routes/JobsPage.test.tsx and Frontend/src/features/notifications/routes/NotificationsPage.test.tsx"
Task: "Add shared shell consistency coverage in Frontend/src/test/app-shell-consistency.test.tsx"
Task: "Add backend contract regression coverage for jobs and notifications in Backend/apps/jobs/tests/test_frontend_contracts.py and Backend/apps/notifications/tests.py"

# Rebuild separate route groups together:
Task: "Rebuild jobs discovery and detail surfaces in Frontend/src/features/jobs/routes/JobsPage.tsx, Frontend/src/features/jobs/routes/SavedJobsPage.tsx, and Frontend/src/features/jobs/routes/JobDetailPage.tsx"
Task: "Rebuild notifications, profile, and settings surfaces in Frontend/src/features/notifications/routes/NotificationsPage.tsx, Frontend/src/features/profile/routes/ProfilePage.tsx, and Frontend/src/features/settings/routes/SettingsPage.tsx"
Task: "Rebuild advisory and public/auth surfaces in Frontend/src/features/advisory/routes/AdvisoryPage.tsx, Frontend/src/features/marketing/routes/LandingPage.tsx, Frontend/src/features/auth/routes/LoginPage.tsx, Frontend/src/features/auth/routes/RegisterPage.tsx, and Frontend/src/features/auth/routes/ForgotPasswordPage.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Stop and validate the dashboard/roadmap slice with the quickstart checks.
5. Demo the new “career atlas” direction before expanding into other flows.

### Incremental Delivery

1. Finish Setup + Foundational once.
2. Ship US1 as the first visible redesign slice.
3. Add US2 to turn assessments into the second major showcase flow.
4. Add US3 to unify the remaining surfaces and remove inconsistent legacy presentation.
5. Finish with Phase 6 performance, warning cleanup, and documentation updates.

### Parallel Team Strategy

1. One developer focuses on shared shell and typed frontend contracts.
2. One developer handles backend payload upgrades in `roadmaps`, `assessments`, `jobs`, and `notifications`.
3. After Foundational, split by story:
   - Developer A: US1 dashboard + roadmap
   - Developer B: US2 assessment flow
   - Developer C: US3 jobs/profile/notifications/advisory/public surfaces

---

## Notes

- Every task follows the required checklist format with task ID and file path.
- `[P]` tasks are limited to work that can proceed without conflicting file ownership.
- User-critical flows include explicit test or manual-validation work because this feature changes route behavior, async state presentation, and backend contract usage.
- Suggested MVP scope: **Phase 3 / User Story 1 only**.
