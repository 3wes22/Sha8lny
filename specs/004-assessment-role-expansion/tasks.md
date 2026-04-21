# Tasks: Assessment Role Baseline Expansion

**Input**: Design documents from `/specs/004-assessment-role-expansion/`  
**Prerequisites**: `spec.md`, `plan.md`

## Phase 1: Docs and scope

- [ ] T001 Create the new 004 role-expansion spec track in `specs/004-assessment-role-expansion/` without editing completed 002 task history.
- [ ] T002 Record the approved eight-role baseline, alias policy, and cache invalidation assumptions in the 004 docs.

## Phase 2: Atomic backend role expansion

- [ ] T003 Add curated runtime role graphs for `android`, `machine_learning_engineer`, and `ui_ux_designer` in `Backend/apps/assessments/role_graph_data.py`.
- [ ] T004 Update `Backend/apps/assessments/role_graph.py` so alias resolution is label-precise and legacy-safe.
- [ ] T005 Flip `SUPPORTED_ROLES` to the approved eight-role inventory only after all eight runtime graphs exist, and bump `CURATED_VERSION` in the same change.
- [ ] T006 Update deterministic adjacent-career and learning-path heuristics in `Backend/apps/assessments/services.py` to branch on resolved role keys.

## Phase 3: Frontend sync

- [ ] T007 Expand `Frontend/src/features/assessment/routes/AssessmentPage.tsx` to the approved eight product-facing labels.
- [ ] T008 Update assessment page tests so the picker proves each supported label can submit an assessment request.

## Phase 4: Verification

- [ ] T009 Extend role-graph and alias tests in `Backend/apps/assessments/tests/test_role_graph.py` for the eight-role baseline and compatibility aliases.
- [ ] T010 Add staged-flow coverage for at least the three new roles in `Backend/apps/assessments/tests/test_staged_flow.py`.
- [ ] T011 Update cache-version and compatibility assertions in `Backend/apps/assessments/tests/test_stage_cache.py` and related suites.
- [ ] T012 Run targeted backend and frontend verification for loader validity, alias routing, staged flow, and picker behavior.
