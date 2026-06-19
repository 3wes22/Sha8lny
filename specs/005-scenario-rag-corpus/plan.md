# Implementation Plan: Scenario RAG Corpus for Staged Assessment Question Generation

**Branch**: `005-scenario-rag-corpus` | **Date**: 2026-05-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-scenario-rag-corpus/spec.md`

## Summary

Augment the existing staged assessment generation flow with a role-aware, schema-aligned scenario corpus retrieved per blueprint from a local ChromaDB collection, layered **after** the existing `STAGE_QUESTION_FEW_SHOT_EXAMPLES` block in `ai_pipeline._build_stage_prompt()` and **independent of** the deterministic contract-safe fallback in `_contract_safe_stage_template()` / `BACKEND_FALLBACK_SCENARIOS`. The corpus is authored as Python modules under `Backend/apps/assessments/scenario_corpus/`, validated against the live question-contract via `apps.core.ai_validation.build_stage_validation_flags()`, and indexed into a dedicated `assessment_scenarios` collection at `SCENARIO_VECTOR_DB_PATH` by a Django management command. Retrieval is gated by a default-off feature flag (`ASSESSMENT_SCENARIO_RAG_ENABLED`), cache keys are version-bound to a new `SCENARIO_CORPUS_VERSION` mirroring the existing `CURATED_VERSION` discipline, and the v1 seed converts the existing 10 `BACKEND_FALLBACK_SCENARIOS` entries into `ScenarioDocument`s so retrieval is non-empty on day one for backend.

## Technical Context

**Language/Version**: Python 3.13 (Backend), TypeScript 5.8 / React 18.3 (Frontend - not changed by this feature)
**Primary Dependencies**: Django 5, Django REST Framework, `chromadb>=0.5,<1.0` (already in `Backend/requirements.txt`), `sentence-transformers>=2.2,<3.0` (already in `Backend/requirements.txt`), existing `apps.core.gemma_client.GemmaClient`, existing `apps.core.ai_validation.build_stage_validation_flags()`
**Storage**: Authored scenarios in version control as Python modules under `Backend/apps/assessments/scenario_corpus/`. Derived Chroma persistent collection `assessment_scenarios` at `SCENARIO_VECTOR_DB_PATH` (default `<BASE_DIR>/data/scenario_vector_db/`, separate from existing advisory `CHROMA_PERSIST_DIR`). No new Django models, no migrations.
**Testing**: pytest (Backend). New tests under `Backend/apps/assessments/tests/`: `test_scenario_corpus.py`, `test_scenario_retriever.py`. Extend `test_staged_flow.py` with one regression test that confirms flag-off behavior is byte-identical to current behavior, and one integration test for cache invalidation on `SCENARIO_CORPUS_VERSION` bump.
**Target Platform**: Existing Django backend process and Celery worker process. No new service.
**Project Type**: Web service (Django modular monolith). This feature is additive within `Backend/apps/assessments/`.
**Performance Goals**: Retrieval p95 latency under 50 ms after warmup (in-process Chroma + lazily loaded `all-MiniLM-L6-v2`). No change to the 3-LLM-calls-per-assessment ceiling. No additional Gemini/Gemma calls.
**Constraints**: Generation MUST succeed when retrieval fails (missing dir, missing collection, missing embedder, raised exception). Feature MUST default OFF. Prompt content with the feature OFF MUST be byte-identical to pre-feature behavior. Vector store MUST be rebuildable from version-controlled authored sources; it carries no source of truth.
**Scale/Scope**: Eight first-class roles (`backend`, `frontend`, `fullstack`, `data_science`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`) × 16 subskills per role = 128 subskill targets. v1 floor ≈ 768 approved scenarios (≥2 stage-1 `single_choice`, ≥2 stage-2 `single_choice`, ≥1 stage-2 `multi_select`, ≥1 stage-2 `open_ended` per subskill). v1 PR ships the wiring and a seed slice (the 10 existing `BACKEND_FALLBACK_SCENARIOS` entries re-expressed as `ScenarioDocument`s); content for full v1 floor is delivered in follow-up PRs one role at a time.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Modular Monolith Boundaries

- All runtime code lives inside `Backend/apps/assessments/`. No code moves into `ai-models/`.
- `ai-models/src/rag/*` is **not** imported at runtime. The new retriever uses `chromadb` and `sentence_transformers` directly to keep `ai-models` support-only per ADR-001 and per the existing 002 research Decision 2.
- No new Django app is created; the work fits inside the existing `apps.assessments` boundary.
- No shared abstraction is promoted. The validator already shared at `apps.core.ai_validation.build_stage_validation_flags()` is reused; no new cross-module helpers are added.
- **PASS.**

### II. Contract-First Interfaces

- No public HTTP routes change. Request and response payloads for `/api/assessments/*` are unchanged.
- The Gemma prompt-contract changes additively: a new "retrieved examples" block is appended after `STAGE_QUESTION_FEW_SHOT_EXAMPLES` and before the `Blueprints:` section in `_build_stage_prompt()`. The required JSON output schema (`_build_stage_question_response_json_schema()`) is unchanged.
- The internal corpus authoring contract is defined as a typed `ScenarioDocument` schema in `Backend/apps/assessments/scenario_corpus/schema.py`, enforced by `validate_scenario()` which delegates to the live `build_stage_validation_flags()`. This is the explicit author-side contract.
- Frontend contracts are not touched. Existing `apps/assessments/tests/test_frontend_contracts.py` is the regression net for the output payload.
- **PASS.**

### III. Testable Business Logic

- Backend pytest coverage added in this change:
  - `tests/test_scenario_corpus.py` — schema validation, uniqueness of `doc_id`, role/subskill key existence in `ROLE_GRAPHS`, dimension consistency, coverage-floor enforcement for the seed slice.
  - `tests/test_scenario_retriever.py` — empty-collection returns `[]`, Chroma exception returns `[]` and logs once, metadata filters by `role_key`/`question_type`/`stage`, dedup across blueprints, global cap of 5 examples per prompt.
  - `tests/test_staged_flow.py` (extension) — flag-off byte-identical prompt regression; flag-on with populated corpus splices retrieved block; `SCENARIO_CORPUS_VERSION` bump invalidates `_stage_one_cache_key()` cached entries.
- The existing `apps/assessments/tests/test_frontend_contracts.py` continues to assert the question payload shape — proof that the new block does not leak schema changes downstream.
- Critical path coverage (assessment scoring, roadmap signal generation) is unchanged and remains green; this feature adds no behavior in those paths.
- **PASS.**

### IV. Responsible AI & Data Protection

- **Model dependency**: re-uses the locally hosted `sentence-transformers/all-MiniLM-L6-v2` model already referenced by `apps.core.ai_settings.EMBEDDING_MODEL`. No new provider, no new outbound network call, no new API key.
- **Fallback behavior**: Retrieval failure (collection missing, embedder failed to load, Chroma raises, any other exception) is wrapped in try/except inside `ScenarioRetriever.retrieve_for_blueprint()` and returns `[]`. Generation continues with the existing static `STAGE_QUESTION_FEW_SHOT_EXAMPLES` block. The deterministic `_contract_safe_stage_template()` / `BACKEND_FALLBACK_SCENARIOS` path remains the final safety net for invalid LLM output, exactly as today.
- **User data**: corpus contains only authored educational scenarios. No learner profile data, no submitted responses, no PII is embedded, stored, or retrieved.
- **Secrets / configuration**: all new settings (`ASSESSMENT_SCENARIO_RAG_ENABLED`, `SCENARIO_VECTOR_DB_PATH`, `SCENARIO_CORPUS_VERSION`) are environment-driven via `python-decouple`, default off / safe values. Nothing is hardcoded.
- **Local / demo-safe operation**: with the flag OFF (default), behavior is byte-identical to today. With the flag ON and an empty corpus, generation still succeeds. The demo path therefore continues to work without any vector-store presence.
- **PASS.**

### V. Operational Visibility & Simplicity

- **Structured logging**: `ScenarioRetriever.retrieve_for_blueprint()` emits one `logger.info("scenario_retrieval", extra={...})` per blueprint with `role_key`, `subskill_key`, `question_type`, `stage`, `results_count`, `top_doc_id`, `top_score`, `corpus_version`. Failure path emits `logger.warning("scenario_retrieval_failed", extra={...})` once per generation.
- **Failure modes**: any exception from Chroma, the embedder, or filesystem access is caught and downgraded to a warning + empty result. No exception propagates into `_build_stage_prompt()`.
- **Simplicity**: no new microservice; no new Django app; no new model; no migration; no new outbound dependency. The change is two new modules and one tightly scoped splice into an existing function. Two management commands provide the human/CI surface (`rebuild_scenario_index`, `scenario_corpus_audit`).
- **Recovery**: rebuilding the index is idempotent (`./manage.py rebuild_scenario_index`). The kill switch is `ASSESSMENT_SCENARIO_RAG_ENABLED=False`. No data migration, no cache surgery required for rollback.
- **PASS.**

All five principles pass. No `Complexity Tracking` entries required.

## Project Structure

### Documentation (this feature)

```text
specs/005-scenario-rag-corpus/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── scenario_document.schema.json
│   └── retriever_interface.md
├── checklists/
│   └── requirements.md
└── tasks.md            # generated later by /speckit.tasks
```

### Source Code (repository root)

```text
Backend/
├── apps/
│   └── assessments/
│       ├── ai_pipeline.py                 # MODIFIED: splice retrieval block + version-bound cache key
│       ├── fallback_scenarios.py          # UNCHANGED (deterministic fallback safety net)
│       ├── role_graph_data.py             # UNCHANGED
│       ├── scenario_corpus/               # NEW package
│       │   ├── __init__.py
│       │   ├── AUTHOR_GUIDE.md
│       │   ├── schema.py                  # ScenarioDocument TypedDict + validate_scenario()
│       │   ├── registry.py                # SCENARIO_CORPUS_VERSION, iter_all_scenarios(), assert_corpus_integrity()
│       │   ├── taxonomy_map.py            # external taxonomy → (role_key, subskill_key)
│       │   ├── backend.py                 # NEW: seeded from BACKEND_FALLBACK_SCENARIOS conversion
│       │   ├── frontend.py                # NEW (empty list ready for content PR)
│       │   ├── fullstack.py               # NEW (empty list)
│       │   ├── data_science.py            # NEW (empty list)
│       │   ├── devops.py                  # NEW (empty list)
│       │   ├── android.py                 # NEW (empty list)
│       │   ├── machine_learning_engineer.py  # NEW (empty list)
│       │   └── ui_ux_designer.py          # NEW (empty list)
│       ├── scenario_retriever.py          # NEW: ScenarioRetriever class
│       ├── apps.py                        # MODIFIED: invoke assert_corpus_integrity() at app ready
│       ├── management/
│       │   ├── __init__.py                # NEW if absent
│       │   └── commands/
│       │       ├── __init__.py            # NEW if absent
│       │       ├── rebuild_scenario_index.py  # NEW
│       │       └── scenario_corpus_audit.py   # NEW
│       └── tests/
│           ├── test_scenario_corpus.py    # NEW
│           ├── test_scenario_retriever.py # NEW
│           └── test_staged_flow.py        # MODIFIED: flag-off byte-equality + flag-on integration
├── apps/core/
│   └── ai_settings.py                     # MODIFIED: add SCENARIO_VECTOR_DB_PATH, ASSESSMENT_SCENARIO_RAG_ENABLED, SCENARIO_RAG_TOP_K, SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT
└── config/settings/
    └── base.py                            # UNCHANGED (settings live in apps/core/ai_settings.py)

data/
└── scenario_vector_db/                    # NEW gitignored dir; created at first index build
```

**Structure Decision**: web-service (Django modular monolith). All new code is contained within `Backend/apps/assessments/` to preserve modular ownership per Constitution Principle I. No frontend changes. `ai-models/` is not modified; runtime stays in `Backend/` per ADR-001 and prior research Decision 2.

## Complexity Tracking

> Constitution Check passes with no violations. Section left empty intentionally.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| (none) | (none) | (none) |
