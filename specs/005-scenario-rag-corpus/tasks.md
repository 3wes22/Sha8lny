---

description: "Task list for Scenario RAG Corpus for Staged Assessment Question Generation"
---

# Tasks: Scenario RAG Corpus for Staged Assessment Question Generation

**Input**: Design documents from `/specs/005-scenario-rag-corpus/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Included. Spec FR-008/FR-010/FR-014 and Constitution Principle III require regression coverage at the layer where behavior lives, and Success Criteria SC-003 requires a re-runnable byte-equality test for flag-off behavior.

**Organization**: Tasks are grouped by user story (US1, US2, US3 from `spec.md`). All paths are absolute or relative to the repo root, consistent with `plan.md`'s "Source Code (repository root)" tree.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are explicit and reference the structure in `plan.md`.

## Path Conventions

- Web service (Django modular monolith). All new code under `Backend/apps/assessments/` and `Backend/apps/core/`.
- Tests under `Backend/apps/assessments/tests/`.
- Settings under `Backend/apps/core/ai_settings.py`. No edits to `Backend/config/settings/base.py`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add new settings, ensure the new package directories exist, and confirm dependencies are present. No behavior change yet.

- [ ] T001 Verify `chromadb>=0.5,<1.0` and `sentence-transformers>=2.2,<3.0` are already declared in `Backend/requirements.txt` (no edit expected). If a future Python interpreter change removes them, add them back; otherwise no change. Document confirmation in the PR description.
- [ ] T002 Add new settings to `Backend/apps/core/ai_settings.py`: `ASSESSMENT_SCENARIO_RAG_ENABLED` (bool, default `False`), `SCENARIO_VECTOR_DB_PATH` (str path, default `<BASE_DIR>/data/scenario_vector_db`), `SCENARIO_RAG_TOP_K` (int, default `1`), `SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT` (int, default `5`). Extend `get_ai_settings_summary()` so the new keys appear in the health-check / log output.
- [ ] T003 [P] Add `data/scenario_vector_db/` to `.gitignore` at the repo root so the local Chroma persistent directory never lands in version control.
- [ ] T004 [P] Create empty package skeleton directories: `Backend/apps/assessments/scenario_corpus/__init__.py`, `Backend/apps/assessments/management/__init__.py`, `Backend/apps/assessments/management/commands/__init__.py`. Each is an empty file.

**Checkpoint**: New settings exist with safe defaults; new package directories exist; no runtime behavior has changed yet.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Author the schema, validator, registry, and retriever. These are required by every user story. No user-visible behavior change yet because the feature flag is off and the index is empty.

- [ ] T005 Create `Backend/apps/assessments/scenario_corpus/schema.py` with `ScenarioOption`, `ScenarioOptionRationale`, `ScenarioDocument` TypedDicts matching `data-model.md` Entity 1, and a `validate_scenario(doc: ScenarioDocument) -> list[str]` function implementing every rule from the "Validation rules" section of `data-model.md`, including delegation to `apps.core.ai_validation.build_stage_validation_flags()`.
- [ ] T006 Create `Backend/apps/assessments/scenario_corpus/registry.py` defining `SCENARIO_CORPUS_VERSION = "scenario-v1"`, `iter_all_scenarios()` (yields from each per-role module's `SCENARIOS` list), and `assert_corpus_integrity()` (validates every doc, asserts unique `doc_id`s, raises a descriptive `ImproperlyConfigured` on first failure).
- [ ] T007 [P] Create empty per-role corpus modules with module-level `SCENARIOS: list[ScenarioDocument] = []`: `Backend/apps/assessments/scenario_corpus/frontend.py`, `fullstack.py`, `data_science.py`, `devops.py`, `android.py`, `machine_learning_engineer.py`, `ui_ux_designer.py`. Backend will be created in T009 (US1) because it carries the seed content.
- [ ] T008 [P] Create `Backend/apps/assessments/scenario_corpus/taxonomy_map.py` with skeleton `LINKEDIN_TO_ROLE_GRAPH: dict[tuple[str, str, str], tuple[str, str]] = {}` and `CSV_TO_ROLE_GRAPH: dict[str, tuple[str, str]] = {}`. Empty maps for v1; populated incrementally in follow-up content PRs.

**Checkpoint**: Schema, validator, registry, and empty per-role corpora exist. `assert_corpus_integrity()` succeeds against an empty corpus. No retriever and no splice yet — staged assessment behavior is still byte-identical to pre-feature.

---

## Phase 3: User Story 1 - Stronger generated questions for every supported role (Priority: P1) 🎯 MVP

**Goal**: Backend assessments generate questions enriched with on-topic retrieved scenarios. Other roles fall through gracefully because their corpora are empty.

**Independent Test**: With `ASSESSMENT_SCENARIO_RAG_ENABLED=true` and the index built from the seed, generate a backend stage-1 assessment and confirm each prompt includes a backend-flavored retrieved example block. Generate a frontend stage-1 assessment and confirm the prompt produces a valid staged assessment using the static block alone, with `results_count=0` in the log.

### Implementation tasks for US1

- [ ] T009 [US1] Create `Backend/apps/assessments/scenario_corpus/backend.py` with `SCENARIOS: list[ScenarioDocument]` populated by converting all 10 entries in `Backend/apps/assessments/fallback_scenarios.py:BACKEND_FALLBACK_SCENARIOS` into `ScenarioDocument` literals per Decision 9 in `research.md`. Use stable `doc_id` `backend.<subskill_key>.s<stage>.<question_type>.fallback-seed`, `author="internal-seed-from-fallback-scenarios"`, `license="internal"`, `review_status="approved"`, `created_at="2026-05-17"`, `corpus_version=SCENARIO_CORPUS_VERSION`. Cross-reference `competency` and `dimension_key` from `role_graph_data.ROLE_GRAPHS["backend"]`.
- [ ] T010 [US1] Create `Backend/apps/assessments/scenario_retriever.py` implementing the `ScenarioRetriever` contract in `contracts/retriever_interface.md`: class-level lazy singletons for embedder and Chroma collection, `retrieve_for_blueprint()` with the metadata filter `(role_key, question_type, stage)`, full try/except returning `[]` on any failure, dedup-by-`doc_id` callsite-side, and the exact `scenario_retrieval` / `scenario_retrieval_failed` structured logging keys from Decision 15 in `research.md`.
- [ ] T011 [US1] Modify `Backend/apps/assessments/ai_pipeline.py` to add `AssessmentAIService._build_retrieved_examples_block(*, role_graph, blueprints, stage) -> str` per the splice point in `contracts/retriever_interface.md`. The method must early-return the empty string when `ASSESSMENT_SCENARIO_RAG_ENABLED` is false. Splice its return value into `_build_stage_prompt()` between `STAGE_QUESTION_FEW_SHOT_EXAMPLES` and `"Blueprints:\n..."`. Behavior with the flag off must be byte-identical to today.
- [ ] T012 [US1] Modify `Backend/apps/assessments/ai_pipeline.py:AssessmentAIService._stage_one_cache_key()` to append `SCENARIO_CORPUS_VERSION` to the cache key suffix (after `graph_version`). Import `SCENARIO_CORPUS_VERSION` from `apps.assessments.scenario_corpus.registry`. No other change to caching.
- [ ] T013 [US1] Create `Backend/apps/assessments/management/commands/rebuild_scenario_index.py` per Phase 4 of the plan: validates corpus via `assert_corpus_integrity()`, filters to `review_status == "approved"`, wipes the `assessment_scenarios` collection, computes embeddings with `all-MiniLM-L6-v2`, and re-adds all approved scenarios with the metadata schema from `data-model.md` Entity 3. Idempotent; prints summary.
- [ ] T014 [US1] Modify `Backend/apps/assessments/apps.py` so `AssessmentsConfig.ready()` invokes `assert_corpus_integrity()` from `apps.assessments.scenario_corpus.registry`. Wrap in a defensive try/except that re-raises in dev/test but logs and continues in production-style boot if a settings-level override (e.g. `SKIP_CORPUS_INTEGRITY=true`) is set — to avoid bricking deployments on a bad content commit. Default behavior is "raise".

### Tests for US1

- [ ] T015 [P] [US1] Create `Backend/apps/assessments/tests/test_scenario_corpus.py` covering: every approved scenario passes `validate_scenario()` with zero errors; every `doc_id` is unique; every `role_key`/`subskill_key` exists in `ROLE_GRAPHS`; every `dimension_key` matches the role graph for that subskill; every approved doc's `corpus_version == SCENARIO_CORPUS_VERSION`.
- [ ] T016 [P] [US1] Create `Backend/apps/assessments/tests/test_scenario_retriever.py` covering: returns `[]` when flag is off; returns `[]` when the collection is empty (use a temp `SCENARIO_VECTOR_DB_PATH`); returns `[]` and emits one `scenario_retrieval_failed` log when Chroma raises (mock the client); applies the `(role_key, question_type, stage)` filter correctly; deduplicates by `doc_id` across blueprints; honors the global cap of 5; emits one `scenario_retrieval` info log per call with the documented keys.
- [ ] T017 [US1] Extend `Backend/apps/assessments/tests/test_staged_flow.py` with `test_stage_one_prompt_matches_legacy_when_flag_off` that captures the rendered stage-one prompt for backend with `ASSESSMENT_SCENARIO_RAG_ENABLED=False` and asserts it is byte-identical to the pre-change baseline (snapshot stored at `Backend/apps/assessments/tests/fixtures/stage_one_prompt_backend.txt`). This is the SC-003 regression net.
- [ ] T018 [US1] Extend `Backend/apps/assessments/tests/test_staged_flow.py` with `test_stage_one_prompt_includes_retrieved_block_when_flag_on_and_corpus_populated` that builds a fresh temp Chroma collection seeded from `scenario_corpus.backend.SCENARIOS`, sets `ASSESSMENT_SCENARIO_RAG_ENABLED=True`, and asserts the generated stage-one prompt contains the retrieved-examples header phrase plus at least one `scenario_context` substring from the backend seed.

**Checkpoint**: US1 is complete and independently verifiable. Backend gets retrieval enrichment; every other role's prompts still produce valid assessments using the static block alone.

---

## Phase 4: User Story 2 - Zero new operational risk during rollout (Priority: P1)

**Goal**: The feature is operationally reversible by a single flag flip, generation never fails when the vector store is missing or broken, and cache invalidation works on version bump.

**Independent Test**: Delete `SCENARIO_VECTOR_DB_PATH` entirely, set `ASSESSMENT_SCENARIO_RAG_ENABLED=True`, and generate a backend assessment — it must complete with one `scenario_retrieval_failed` log. Bump `SCENARIO_CORPUS_VERSION`, observe that the previously cached stage-one result for backend is regenerated on next request.

### Implementation tasks for US2

- [ ] T019 [US2] Verify the failure-path guarantees from FR-003 by hand-running `python manage.py runserver` with `SCENARIO_VECTOR_DB_PATH` set to a non-existent directory and the feature flag on; expand `ScenarioRetriever` if any code path raises instead of returning `[]`. No source change expected if T010 is implemented correctly; this task is the live verification step against the quickstart.
- [ ] T020 [US2] Ensure `rebuild_scenario_index` is safe to run when `SCENARIO_VECTOR_DB_PATH` does not yet exist (create the directory if absent) and when the collection already exists (delete and recreate). Add log lines describing each step.

### Tests for US2

- [ ] T021 [P] [US2] Add to `Backend/apps/assessments/tests/test_scenario_retriever.py`: `test_retrieval_returns_empty_when_persist_dir_missing` — point `SCENARIO_VECTOR_DB_PATH` at a non-existent directory and confirm the call returns `[]` without raising and emits one warning.
- [ ] T022 [P] [US2] Add to `Backend/apps/assessments/tests/test_stage_cache.py` (existing file): `test_stage_one_cache_invalidates_on_scenario_corpus_version_bump` — generate stage one, monkeypatch `apps.assessments.scenario_corpus.registry.SCENARIO_CORPUS_VERSION` to a new value, and confirm the next call regenerates (cache miss) instead of returning the cached payload.
- [ ] T023 [P] [US2] Add to `Backend/apps/assessments/tests/test_staged_flow.py`: `test_generation_completes_when_corpus_is_empty_and_flag_is_on` — start with an empty `scenario_corpus.backend.SCENARIOS` (use `monkeypatch.setattr`) and confirm stage-one generation still produces a valid 5-question payload using the static few-shot block alone.

**Checkpoint**: US2 is complete. Rollback is a flag flip; corpus failures degrade gracefully; cache invalidation works.

---

## Phase 5: User Story 3 - Authoring loop that prevents corpus quality regressions (Priority: P2)

**Goal**: Authors and CI can mechanically detect contract violations, missing coverage cells, and near-duplicates.

**Independent Test**: Add a deliberately invalid scenario (e.g. multi_select with one correct option) to `scenario_corpus/backend.py` with `review_status="draft"` then `="approved"`; run `python manage.py scenario_corpus_audit` and confirm a non-zero exit with a precise diagnostic. Remove the invalid scenario, then delete all stage-2 `open_ended` entries from backend; re-run the audit and confirm the coverage gap is reported with a non-zero exit.

### Implementation tasks for US3

- [ ] T024 [US3] Create `Backend/apps/assessments/management/commands/scenario_corpus_audit.py` implementing: (a) validate every approved scenario; (b) compute the coverage matrix per Decision 12 in `research.md` (stage 1 single_choice ≥ 2 per stage-1 allocation subskill; stage 2 single_choice ≥ 2 per role subskill; stage 2 multi_select ≥ 1 per role subskill; stage 2 open_ended ≥ 1 per role subskill); (c) embed all approved docs and compute pairwise cosine similarity within each `(role_key, subskill_key, question_type)` cluster, flag pairs > 0.92 as near-duplicates; (d) print a human-readable report; (e) exit non-zero if any validation fails, any coverage cell is below floor, or any near-duplicate pair exists.
- [ ] T025 [US3] Create `Backend/apps/assessments/scenario_corpus/AUTHOR_GUIDE.md` per Phase 3.1 of the plan: rule summary mirroring the validator, per-question-type checklists, the canonical scenario template (a Python dict literal authors can copy/paste), and the audit/rebuild loop.

### Tests for US3

- [ ] T026 [P] [US3] Add to `Backend/apps/assessments/tests/test_scenario_corpus.py`: `test_coverage_floor_per_role_stage_question_type` — programmatically computes coverage from `iter_all_scenarios()` and asserts the floor for the v1 seed (backend stage-1 `single_choice` ≥ 2 per stage-1 allocation subskill). Other roles/cells are below floor and the test currently asserts they are reported as missing — proving the audit detects gaps. The test does NOT fail CI for unfilled cells in v1; that is the audit command's job in follow-up content PRs.
- [ ] T027 [P] [US3] Add to `Backend/apps/assessments/tests/test_scenario_corpus.py`: `test_validator_rejects_intentional_violations` — constructs in-memory `ScenarioDocument`s violating each rule (missing required field, wrong option count for question type, mismatched dimension_key, stale corpus_version, etc.) and asserts `validate_scenario(doc)` returns a non-empty list with a recognizable error string for each.

**Checkpoint**: US3 is complete. Authors and CI can detect contract regressions; near-duplicate detection works; the AUTHOR_GUIDE documents the loop.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Verification, observability, documentation, and PR hygiene.

- [ ] T028 [P] Run the full backend pytest suite (`pytest apps/assessments/`) and confirm no regression in existing tests (`test_api.py`, `test_async_flow.py`, `test_engine.py`, `test_frontend_contracts.py`, `test_role_graph.py`, `test_stage_cache.py`, `test_staged_flow.py`). Spec SC-001 baseline integrity.
- [ ] T029 [P] Re-run `python manage.py check` and confirm `apps.assessments.apps.AssessmentsConfig.ready()` exits cleanly with `SCENARIO_CORPUS_VERSION="scenario-v1"` and the seeded backend corpus.
- [ ] T030 [P] Update `Backend/CLAUDE.md` "Current Implementation Status" / "Next Module" section with a one-line entry referencing this feature track and the corpus location, so backend contributors see the corpus exists without reading the spec.
- [ ] T031 Run the quickstart top-to-bottom against a clean checkout (`specs/005-scenario-rag-corpus/quickstart.md`) and confirm every step produces the documented output. Capture any drift and update the quickstart inline.
- [ ] T032 Commit the work in two logical commits: (1) "scenario corpus: settings, schema, registry, retriever, splice, seed" (T001–T014), (2) "scenario corpus: tests, audit command, author guide, docs" (T015–T031). Open a pull request from `005-scenario-rag-corpus` into `main` with a PR body that includes a screenshot/excerpt of the `scenario_corpus_audit` output and confirmation that with the flag off, prompt content is byte-identical to pre-feature behavior. Spec SC-005 evidence.

---

## Dependencies

- Phase 1 (Setup) blocks everything that follows.
- Phase 2 (Foundational) blocks every user-story phase.
- US1 (Phase 3) is the MVP. US2 (Phase 4) extends US1's wiring with operational guarantees. US3 (Phase 5) is independent of US1/US2 in concept but in practice depends on T009 (the seed) existing because the audit reports against a real corpus.
- Phase 6 (Polish) runs last.

### Story completion order

- US1 first (P1, MVP).
- US2 second (P1, completes operational safety on top of US1).
- US3 third (P2, completes authoring loop).

### Parallel execution opportunities

- T003, T004 can run in parallel inside Phase 1.
- T007, T008 can run in parallel inside Phase 2 (different files).
- T015, T016 can run in parallel inside US1's test block (different files).
- T021, T022, T023 can run in parallel inside US2's test block (different files).
- T026, T027 can run in parallel inside US3's test block (same file but distinct functions; if multiple agents are editing, treat as serial).
- T028, T029, T030 in Phase 6 can run in parallel.

### Independent test criteria (per user story)

| Story | Independent test |
|---|---|
| US1 | Backend assessment shows retrieved scenario block in the prompt with flag on; non-backend role still produces valid assessment with no retrieved block. |
| US2 | Generation completes with flag on and missing/empty index. Bumping `SCENARIO_CORPUS_VERSION` invalidates the stage-one cache. |
| US3 | Audit rejects an invalid scenario with a precise message. Audit reports any below-floor coverage cell with a non-zero exit. |

## Suggested MVP scope

Ship Phase 1 + Phase 2 + Phase 3 (US1) + the US2 tests T021/T022/T023 + Phase 6. That is the smallest set that delivers user-visible value (US1 MVP), guarantees operational safety (US2 via tests), and keeps the merge low-risk. US3 (audit + AUTHOR_GUIDE) can ship in the very next PR alongside the first follow-up content authoring wave.
