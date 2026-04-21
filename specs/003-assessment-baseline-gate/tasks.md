# Tasks: Staged Assessment Baseline Review Gate

**Input**: Design documents from `/specs/003-assessment-baseline-gate/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: This feature formalizes a review workflow around an existing staged-assessment candidate, so verification is captured through evidence files, checklists, the documented command suite, and the manual walkthrough in `quickstart.md` rather than through new automated product tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g. US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the evidence workspace and reviewer-facing document skeleton shared by the whole gate.

- [ ] T001 Create the review evidence index in `specs/003-assessment-baseline-gate/evidence/README.md`
- [ ] T002 [P] Create the candidate inventory template in `specs/003-assessment-baseline-gate/evidence/candidate-inventory.md`
- [ ] T003 [P] Create the verification log template in `specs/003-assessment-baseline-gate/evidence/verification-log.md`
- [ ] T004 [P] Create the manual walkthrough template in `specs/003-assessment-baseline-gate/evidence/manual-walkthrough.md`
- [ ] T005 [P] Create the contract review templates in `specs/003-assessment-baseline-gate/evidence/role-graph-review.md`, `specs/003-assessment-baseline-gate/evidence/runtime-review.md`, and `specs/003-assessment-baseline-gate/evidence/contract-review.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the shared checklists, artifact relationships, and execution rules that block every user story.

**⚠️ CRITICAL**: No user story work should begin until this phase is complete.

- [ ] T006 Create the blocking-surface checklist with pass/fail/needs-followup states in `specs/003-assessment-baseline-gate/checklists/review-surfaces.md`
- [ ] T007 [P] Create the decision-readiness checklist in `specs/003-assessment-baseline-gate/checklists/decision-readiness.md`
- [ ] T008 [P] Add the concrete evidence and decision artifact names to `specs/003-assessment-baseline-gate/data-model.md`
- [ ] T009 Update the execution steps and evidence-file destinations in `specs/003-assessment-baseline-gate/quickstart.md` and `specs/003-assessment-baseline-gate/contracts/baseline-review-gate.md`

**Checkpoint**: Evidence files, shared checklists, and reviewer rules are ready. User story work can now begin.

---

## Phase 3: User Story 1 - Review a Baseline Candidate (Priority: P1) 🎯 MVP

**Goal**: Define the exact candidate under review, collect the required evidence, and show that the review can reach an evidence-complete state.

**Independent Test**: Populate the candidate inventory, verification log, and manual walkthrough files for one staged-assessment candidate, then confirm every blocking review surface has linked evidence in the review-surface checklist.

### Tests for User Story 1

- [ ] T010 [P] [US1] Capture the direct-review file inventory and scope-freeze notes in `specs/003-assessment-baseline-gate/evidence/candidate-inventory.md`
- [ ] T011 [P] [US1] Record the blocking command results and observed pass/fail outcomes in `specs/003-assessment-baseline-gate/evidence/verification-log.md`
- [ ] T012 [P] [US1] Record the standard staged-flow walkthrough and fallback walkthrough outcomes in `specs/003-assessment-baseline-gate/evidence/manual-walkthrough.md`

### Implementation for User Story 1

- [ ] T013 [US1] Link the collected evidence to each blocking review surface in `specs/003-assessment-baseline-gate/checklists/review-surfaces.md`
- [ ] T014 [US1] Summarize evidence completeness, missing inputs, and reviewer handoff notes in `specs/003-assessment-baseline-gate/evidence/README.md`

**Checkpoint**: User Story 1 is complete when one candidate can be fully inventoried and its evidence set is ready for human review.

---

## Phase 4: User Story 2 - Record a Decision the Team Can Act On (Priority: P2)

**Goal**: Give reviewers a decision record that consistently captures the outcome, rationale, findings, and next actions.

**Independent Test**: Complete the decision template using sample `accept`, `revise`, and `reject` cases and confirm the decision-readiness checklist can validate the record without additional explanation.

### Tests for User Story 2

- [ ] T015 [P] [US2] Draft sample `accept`, `revise`, and `reject` validation cases in `specs/003-assessment-baseline-gate/evidence/decision-validation.md`
- [ ] T016 [P] [US2] Add required field checks for decision completion in `specs/003-assessment-baseline-gate/checklists/decision-readiness.md`

### Implementation for User Story 2

- [ ] T017 [US2] Create the decision record template with outcome, rationale, blocking findings, evidence reviewed, follow-up actions, approver, and date sections in `specs/003-assessment-baseline-gate/decision.md`
- [ ] T018 [US2] Add decision outcome semantics and required completion rules in `specs/003-assessment-baseline-gate/contracts/baseline-review-gate.md`
- [ ] T019 [US2] Link decision-record completion and team handoff steps in `specs/003-assessment-baseline-gate/quickstart.md` and `specs/003-assessment-baseline-gate/evidence/README.md`

**Checkpoint**: User Story 2 is complete when a reviewer can fill out a complete decision record that another teammate can use without attending the review.

---

## Phase 5: User Story 3 - Catch Cross-Surface Risk Before Baseline Adoption (Priority: P3)

**Goal**: Make the review explicitly inspect the candidate’s coupled behavior surfaces and prevent acceptance when those surfaces drift.

**Independent Test**: Record findings for role-graph integrity, runtime behavior, and contract alignment, then confirm the review-surface checklist blocks acceptance whenever any blocking surface remains failed or unresolved.

### Tests for User Story 3

- [ ] T020 [P] [US3] Record role-graph and cache/version findings in `specs/003-assessment-baseline-gate/evidence/role-graph-review.md`
- [ ] T021 [P] [US3] Record fallback, LLM budget, and runtime walkthrough findings in `specs/003-assessment-baseline-gate/evidence/runtime-review.md`
- [ ] T022 [P] [US3] Record roadmap-signal and frontend/backend contract findings in `specs/003-assessment-baseline-gate/evidence/contract-review.md`

### Implementation for User Story 3

- [ ] T023 [US3] Roll up pass/fail/needs-followup status and evidence links across all blocking surfaces in `specs/003-assessment-baseline-gate/checklists/review-surfaces.md`
- [ ] T024 [US3] Add explicit mismatch-blocks-acceptance guidance in `specs/003-assessment-baseline-gate/contracts/baseline-review-gate.md`, `specs/003-assessment-baseline-gate/contracts/assessment-staged-api.md`, and `specs/003-assessment-baseline-gate/contracts/roadmap-signal-contract.md`
- [ ] T025 [US3] Align role-graph handoff acceptance assertions with curation findings in `specs/003-assessment-baseline-gate/contracts/role-graph-handoff.md` and `specs/003-assessment-baseline-gate/checklists/role-graph-curation.md`

**Checkpoint**: User Story 3 is complete when the gate can show exactly which cross-surface findings permit or block baseline acceptance.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize the gate execution, record the outcome, and tighten the documentation after the first real run.

- [ ] T026 [P] Populate the final decision outcome, rationale, blocking findings, and follow-up actions in `specs/003-assessment-baseline-gate/decision.md`
- [ ] T027 [P] Update the evidence index and execution notes after the completed review in `specs/003-assessment-baseline-gate/evidence/README.md` and `specs/003-assessment-baseline-gate/quickstart.md`
- [ ] T028 Re-run the review checklists and confirm the gate is complete in `specs/003-assessment-baseline-gate/checklists/review-surfaces.md`, `specs/003-assessment-baseline-gate/checklists/decision-readiness.md`, and `specs/003-assessment-baseline-gate/decision.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion
- **User Story 2 (Phase 4)**: Depends on Foundational completion
- **User Story 3 (Phase 5)**: Depends on User Story 1 because it builds on the candidate inventory and verification evidence
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational - defines the MVP evidence-collection slice
- **User Story 2 (P2)**: Starts after Foundational - creates the decision framework independently of the final review outcome
- **User Story 3 (P3)**: Starts after User Story 1 - consumes the collected candidate evidence to evaluate cross-surface risk

### Within Each User Story

- Verification artifacts are created before story-specific implementation rules are finalized
- Evidence capture happens before checklist rollup
- Decision structure is created before the final decision is recorded
- Cross-surface findings are recorded before acceptance-blocking rules are finalized

### Parallel Opportunities

- Setup tasks T002-T005 can run in parallel after T001 creates the shared evidence workspace
- Foundational tasks T007 and T008 can run in parallel after T006 establishes the shared review-surface checklist
- Within US1, tasks T010-T012 can run in parallel because they write to different evidence files
- Within US2, tasks T015 and T016 can run in parallel because they use different files
- Within US3, tasks T020-T022 can run in parallel because they capture findings in different review files
- In Polish, T026 and T027 can run in parallel before the final confirmation task T028

---

## Parallel Example: User Story 1

```bash
# Capture the three US1 evidence streams together:
Task: "Capture the direct-review file inventory and scope-freeze notes in specs/003-assessment-baseline-gate/evidence/candidate-inventory.md"
Task: "Record the blocking command results and observed pass/fail outcomes in specs/003-assessment-baseline-gate/evidence/verification-log.md"
Task: "Record the standard staged-flow walkthrough and fallback walkthrough outcomes in specs/003-assessment-baseline-gate/evidence/manual-walkthrough.md"
```

---

## Parallel Example: User Story 2

```bash
# Prepare decision validation assets together:
Task: "Draft sample accept, revise, and reject validation cases in specs/003-assessment-baseline-gate/evidence/decision-validation.md"
Task: "Add required field checks for decision completion in specs/003-assessment-baseline-gate/checklists/decision-readiness.md"
```

---

## Parallel Example: User Story 3

```bash
# Review the coupled behavior surfaces together:
Task: "Record role-graph and cache/version findings in specs/003-assessment-baseline-gate/evidence/role-graph-review.md"
Task: "Record fallback, LLM budget, and runtime walkthrough findings in specs/003-assessment-baseline-gate/evidence/runtime-review.md"
Task: "Record roadmap-signal and frontend/backend contract findings in specs/003-assessment-baseline-gate/evidence/contract-review.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate that one candidate can be fully inventoried and evidenced
5. Review whether the evidence-collection slice is usable before expanding the decision layer

### Incremental Delivery

1. Finish Setup + Foundational once
2. Deliver US1 to make candidate review evidence repeatable
3. Deliver US2 to make the decision record consistent and reusable
4. Deliver US3 to make cross-surface risk review explicit and blocking
5. Finish with Phase 6 to record the first real decision and tighten the docs

### Parallel Team Strategy

1. One teammate owns the evidence workspace and quickstart execution notes
2. One teammate owns the decision template and readiness checklist
3. One teammate owns cross-surface contract review and blocking-surface rollup
4. Merge the three streams in Phase 6 when the final decision is recorded

---

## Notes

- Every task follows the required checklist format with task ID, optional parallel marker, optional story label, and exact file path
- `[P]` tasks are limited to work that can proceed without conflicting file ownership or incomplete prerequisites
- Suggested MVP scope: **Phase 3 / User Story 1 only**
- This feature’s verification is evidence-driven; the quickstart command suite and the manual walkthrough are part of the implementation, not optional extras
