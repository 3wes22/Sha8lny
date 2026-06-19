# Assessment Scenario Corpus: LLM-Assisted Authoring Pipeline + Tiered Coverage

**Date:** 2026-06-18
**Status:** Approved in brainstorming session; awaiting written-spec review
**Predecessor:** `2026-06-10-quality-refinement-design.md` (this spec realizes its Decision 2 item for the **assessment** module: "7/8 scenario-corpus roles are empty stubs")
**Module:** `Backend/apps/assessments/` — scenario RAG corpus

---

## 1. Context and decision record

The assessment module already ships a complete scenario-RAG *mechanism* (spec `005-scenario-rag-corpus`): a schema (`scenario_corpus/schema.py`), a registry with integrity checks (`registry.py`), a runtime retriever (`scenario_retriever.py`) over a local Chroma collection `assessment_scenarios`, an ingest command (`rebuild_scenario_index`), an audit command (`scenario_corpus_audit`), and an author guide. The mechanism is sound. **The content is not there.**

### Verified current state (2026-06-18, via `manage.py scenario_corpus_audit`)

- **8 roles**, each with **~44 subskills** in the curated role graph.
- Only **`backend.py`** has content — **12 scenarios**, seeded from `BACKEND_FALLBACK_SCENARIOS`.
- The other **7 roles are literally `SCENARIOS = []`**: `frontend`, `fullstack`, `data_science`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`.
- There is **no fast seeding path** for the 7 empty roles: `fallback_scenarios.py` contains only `BACKEND_FALLBACK_SCENARIOS`. Their content must be authored or generated from scratch.
- The feature is **default-off**: `ASSESSMENT_SCENARIO_RAG_ENABLED=false`.

### The floor math (why naive "fill the corpus" is infeasible)

The audit's coverage floor (per `research.md` Decision 12), per role:

| Check | Subskills | Floor each | Per role |
|---|---|---|---|
| Stage 1 `single_choice` | ~5 (calibration set) | ≥2 | ~10 |
| Stage 2 `single_choice` | ~44 (all) | ≥2 | ~88 |
| Stage 2 `multi_select` | ~44 (all) | ≥1 | ~44 |
| Stage 2 `open_ended` | ~44 (all) | ≥1 | ~44 |

≈ **~186 reviewed scenarios per role → ~1,500 across 8 roles.** Even `backend` (the "done" role) meets **none** of its stage-2 floor (0 coverage on 42–44 subskills). Hand-authoring ~1,500 reviewed questions is infeasible in the remaining timeline, and the uniform floor over-provisions subskills the engine never adaptively targets.

### Decisions made with the developer (2026-06-18)

1. **Goal: defensible, role-aware coverage for all 8 roles**, RAG turned on, with measured improvement. (Not: a minimal "don't look broken" seed; not: a pure-method pipeline with content as a byproduct.)
2. **Authoring approach: LLM-assisted generation with a mandatory human-review gate** (Approach C). Gemini drafts → automated validation/dedup → human spot-review → promotion. The pipeline is itself a thesis artifact.
3. **Coverage target is tiered and demand-weighted**, replacing the uniform ~1,500 floor. Tier 1 (stage-1 calibration, all roles) is the committed deliverable; Tier 2 (stage-2 subskills the engine actually targets) is pipeline-driven and incremental.
4. **Generated drafts are staged in JSONL**, never written directly into the role `.py` modules. Only reviewed-and-approved scenarios are promoted into the curated `.py` files — keeping the shipped corpus human-curated, not raw model output.
5. **The audit floor is reframed** to the tiered, demand-weighted definition, with the rationale documented.
6. **Evaluation uses both** a deterministic retrieval-level eval (the spine) **and** a question-quality A/B study including an LLM-as-judge (the outcome claim).
7. **Flag rollout: flip `ASSESSMENT_SCENARIO_RAG_ENABLED` default → on** once all 8 roles pass Tier 1 and the retrieval eval is published. The deterministic `fallback_scenarios` path remains the generation safety net throughout.

---

## 2. Architecture — three-stage authoring pipeline

```
role_graph_data (subskill/dimension/competency defs)   backend.py exemplars (style anchors)
            │                                                      │
            ▼                                                      ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ manage.py generate_scenarios --role <r> --tier 1|2 [--blueprint]  │
  │   For each blueprint (role × subskill × stage × question_type)    │
  │   not yet covered, ask Gemini to draft a ScenarioDocument,         │
  │   grounded in the subskill's curated definition + role vocabulary  │
  │   + 1–2 backend exemplars as style anchors.                        │
  └─────────────────────────────────────────────────────────────────┘
            │  writes drafts →
            ▼
   scenario_corpus/_staging/<role>.jsonl   (review_status="draft"; never retrieved, never imported by registry)
            │
            ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ manage.py review_scenarios --role <r>                             │
  │   CLI loop. For each draft: run validate_scenario + audit content  │
  │   rules + near-duplicate check; show the rendered scenario;        │
  │   accept / reject / edit. Accepted drafts marked approved.         │
  └─────────────────────────────────────────────────────────────────┘
            │  approved →
            ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │ promoter (review_scenarios --promote, or a dedicated step)        │
  │   Append approved dicts as review_status="approved" literals       │
  │   into scenario_corpus/<role>.py. Idempotent on doc_id.            │
  └─────────────────────────────────────────────────────────────────┘
            │
            ▼
  manage.py rebuild_scenario_index → Chroma `assessment_scenarios` → ScenarioRetriever (RAG on)
```

### Components

- **`generate_scenarios` (new management command).**
  - Inputs: `--role`, `--tier {1,2}`, optional `--blueprint role.subskill.stage.type`, `--limit`, `--dry-run`.
  - Computes the set of *uncovered* blueprints for the tier (re-uses the audit's bucketing against the role graph and `StageAllocator`).
  - For each, calls the existing Gemini runtime (per ADR-002) with a structured prompt: the subskill's `competency`/`dimension_key` (pulled from `ROLE_GRAPHS`), the role's engineering vocabulary, the `AUTHOR_GUIDE` quality bar and banned-phrase list, the required `answer_key` shape for the question type, and 1–2 `backend.py` exemplars as style anchors.
  - Parses the response into a `ScenarioDocument`, sets `review_status="draft"`, `corpus_version=SCENARIO_CORPUS_VERSION`, generates a conforming `doc_id`.
  - Runs `validate_scenario` immediately; only schema-valid drafts are written to `_staging/<role>.jsonl`. Invalid drafts are logged and skipped (optionally one retry with the validation error fed back).
  - **Never** touches the role `.py` modules or Chroma.

- **`review_scenarios` (new management command).**
  - Loads `_staging/<role>.jsonl`. For each draft: re-validates, runs the audit content rules and the embedding near-duplicate check against already-approved scenarios in the same `(role, subskill, question_type)` cluster, renders the scenario for the human, and prompts accept / reject / skip / edit.
  - `--promote`: append accepted (`approved`) drafts into `scenario_corpus/<role>.py` as Python dict literals, idempotent on `doc_id`; remove promoted entries from staging.
  - Non-interactive `--list` / `--stats` modes for inspection.

- **Promoter.** Writes well-formed, `black`-compatible dict literals into the role module's `SCENARIOS` list. After writing, the module must import cleanly and `assert_corpus_integrity()` must pass.

### Unchanged

`schema.py`, `registry.py`, `scenario_retriever.py`, `rebuild_scenario_index`, and the `ai_pipeline._build_stage_prompt` wiring are **not modified by this work** (except `registry.SCENARIO_CORPUS_VERSION` bumps and the audit-floor reframe in §4). The retriever already layers retrieved scenarios after the static few-shot block; filling the corpus is sufficient to activate that path.

---

## 3. Coverage target — tiered & demand-weighted

Replaces the uniform ~186/role floor.

- **Tier 1 (committed): stage-1 calibration set, all 8 roles.**
  ~5 subskills/role × ≥2 `single_choice` ≈ **~80 scenarios total** (`backend` already partially covered). This is the path *every* test-taker hits first and what the retriever queries at assessment start — the highest-leverage content. **RAG flips on once Tier 1 passes audit for all 8 roles.**

- **Tier 2 (pipeline-driven, demand-weighted): the subskills stage 2 actually targets adaptively** — not all 44.
  A plan task extracts the stage-2 target set from the engine's allocation logic (`engine.py`), expected to be ~10–12 subskills/role. For those: `single_choice`×2 + `multi_select`×1 + `open_ended`×1. **Fill `backend` + 1–2 showcase roles fully** via the pipeline; stage the remaining roles' Tier-2 drafts as reviewable `_staging` content (demonstrating the pipeline scales) without blocking the milestone.

- **Audit-floor reframe.** `scenario_corpus_audit` is updated so its coverage matrix reflects the tiered definition: Tier 1 gates green for all roles; Tier 2 reports against the demand-weighted subskill set, not all 44. The change and its rationale are documented in the audit command docstring and `AUTHOR_GUIDE.md`. A passing audit becomes an honest, achievable signal.

---

## 4. Defensibility / circularity answer

The expected defense challenge: *"LLM-generated few-shots feeding an LLM generator — isn't that circular?"* Answered structurally:

1. **The shipped corpus is human-curated, schema-validated, dedup-checked content.** Raw model output is the *draft* in `_staging`; the *artifact* is what survives the review gate and lands in the `.py` modules. The contribution is the validation + curation layer.
2. **Generation is grounded**, not free: constrained by the curated `role_graph` taxonomy (real subskill/dimension/competency definitions) and role-specific engineering vocabulary — closer to constrained exemplar-drafting than open generation.
3. **It is an additive stylistic layer.** The deterministic `fallback_scenarios` path remains the generation safety net, so the corpus is never a single point of failure.
4. **The benefit is measured** (see §5), so "this helps" is evidenced, not asserted.

---

## 5. Evaluation

### 5.1 Retrieval-level eval — the spine (deterministic, no Gemini quota, CI-gateable)

A runnable script walks every Tier-1 blueprint (role × subskill × stage × type) and measures:

| Metric | Before (empty corpus) | After Tier 1 (target) |
|---|---|---|
| **Retrieval coverage** — % blueprints returning ≥1 scenario | ~0% for 7 roles; partial backend | 100% of stage-1 blueprints |
| **Subskill-match precision** — % retrieved whose `subskill_key` exactly matches the request (vs. broad-`where` fallback firing) | n/a | ≥0.9 |
| **Role-match** — guard (role is a hard `where` filter) | — | 100% (sanity) |

Output: per-role before/after table in **`docs/product/SCENARIO_RAG_EVAL.md`**, mirroring `docs/product/RAG_RETRIEVAL_EVAL.md`. This is the reproducible, defense-safe evidence and is safe to gate in CI.

### 5.2 Question-quality A/B — the outcome claim (sampled, documented, quota-bounded)

Hold a fixed set of blueprints (~3–5 per role, ~30 total); generate questions **RAG-off vs RAG-on**, same Gemini model. Score both ways:

- **Rubric checks (always, deterministic, free):** `scenario_context` concrete and not a banned phrase; option-length parallelism (length variance); role-vocabulary terms present; decision-not-definition heuristic. Report per-dimension deltas.
- **LLM-as-judge (included):** a separate Gemini call performs **blind pairwise A/B preference** (RAG-on vs RAG-off, order randomized) plus 1–5 rubric scores. Report win-rate and mean score deltas.

Sample size stays modest given quota; documented explicitly as a small study, not a benchmark. **Run deliberately, cache all outputs, never in CI.** Results live in `SCENARIO_RAG_EVAL.md`.

---

## 6. Rollout — phased, each phase shippable

- **Phase 0 — Pipeline scaffolding.** `generate_scenarios`, `review_scenarios` (+ promoter). Unit-tested with Gemini mocked. The reusable method; no content yet.
- **Phase 1 — Tier 1 floor + content, all 8 roles.** First, teach `scenario_corpus_audit` the **Tier-1 floor** (stage-1 calibration set), so a green audit means an honest, achievable signal. Then generate → review → promote stage-1 calibration scenarios for the 7 empty roles (+ top up `backend`). Audit passes Tier 1 for all roles. `rebuild_scenario_index`.
- **Phase 2 — Turn RAG on + retrieval eval.** Flip `ASSESSMENT_SCENARIO_RAG_ENABLED` default → `true`; bump `SCENARIO_CORPUS_VERSION` (invalidates stage-1 cached questions); publish the §5.1 before/after table.
- **Phase 3 — Question-quality A/B study.** Run §5.2 (rubric + LLM-judge); document results.
- **Phase 4 — Tier 2 demand-weighted.** Extract the stage-2 target subskill set from `engine.py`; extend the audit's tiered floor with the **Tier-2 demand-weighted** matrix (§3); fill `backend` + showcase role(s); stage remaining roles' Tier-2 drafts.
- **Phase 5 — Docs.** `AUTHOR_GUIDE.md` pipeline workflow; `SCENARIO_RAG_EVAL.md`; update `Backend/CLAUDE.md`, root `CLAUDE.md` module-status line, and the academic/dataset-registry docs.

---

## 7. Testing

- **Per-command unit tests (Gemini mocked):**
  - `generate_scenarios` writes only schema-valid `ScenarioDocument`s to `_staging/<role>.jsonl`; malformed model output is skipped/retried, never staged.
  - `review_scenarios` validators reject schema-invalid, banned-phrase, and near-duplicate drafts; accept-path marks `approved`.
  - Promoter emits syntactically valid Python; the target module imports and passes `assert_corpus_integrity()`.
- **Corpus/retriever tests:** extend `test_scenario_corpus.py` / `test_scenario_retriever.py` with Tier-1 coverage assertions and a "promoted modules import & validate" test.
- **Retrieval eval:** runnable script with a checked-in expected-coverage snapshot, asserted in a test.
- **No network in the suite:** all Gemini calls mocked; quota-consuming steps (generation, LLM-judge) are operator-run, never in CI.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Gemini quota exhaustion (generation + LLM-judge) | Operator-run, cached, never in CI; CI gates only on deterministic audit + retrieval coverage. |
| LLM produces paraphrase-spam (8 near-identical scenarios) | Mandatory near-duplicate check (cosine > 0.92) in `review_scenarios`, reusing the audit's logic. |
| Quality drift from generated content | Mandatory human review gate; only `approved` content is promoted and retrieved; `backend` seeds remain the quality bar. |
| Stale stage-1 cache after content change | Bump `SCENARIO_CORPUS_VERSION` (already wired into the stage-one cache key). |
| Generation circularity challenge at defense | §4 structural answer + measured §5 evidence. |
| Corpus becomes a failure point | Additive layer only; deterministic `fallback_scenarios` stays the generation safety net. |

---

## 9. Out of scope

- Modifying the retriever, schema, registry, ingest command, or `ai_pipeline` prompt wiring (beyond `SCENARIO_CORPUS_VERSION` bumps and the audit-floor reframe).
- Full uniform 44-subskill stage-2 coverage for all 8 roles (explicitly replaced by the tiered target).
- Frontend changes (assessment UI already consumes generated questions unchanged).
- The deterministic `fallback_scenarios` content (unrelated safety net).

---

## 10. File-level change inventory (for the implementation plan)

**New**
- `Backend/apps/assessments/management/commands/generate_scenarios.py`
- `Backend/apps/assessments/management/commands/review_scenarios.py`
- `Backend/apps/assessments/scenario_corpus/_staging/` (gitignored or committed-as-empty; drafts transient)
- `Backend/apps/assessments/tests/test_generate_scenarios.py`
- `Backend/apps/assessments/tests/test_review_scenarios.py`
- Retrieval-eval script (e.g. `Backend/apps/assessments/scenario_corpus/eval/retrieval_eval.py`) + test
- `docs/product/SCENARIO_RAG_EVAL.md`

**Modified (content)**
- `scenario_corpus/{frontend,fullstack,data_science,devops,android,machine_learning_engineer,ui_ux_designer}.py` — Tier-1 (and showcase Tier-2) approved scenarios
- `scenario_corpus/backend.py` — Tier-1 top-up + Tier-2 fill

**Modified (config/floor/flag)**
- `scenario_corpus/registry.py` — `SCENARIO_CORPUS_VERSION` bump(s)
- `apps/core/ai_settings.py` — `ASSESSMENT_SCENARIO_RAG_ENABLED` default → `true` (Phase 2)
- `management/commands/scenario_corpus_audit.py` — Tier-1 floor (Phase 1), Tier-2 demand-weighted matrix (Phase 4)
- `scenario_corpus/AUTHOR_GUIDE.md` — pipeline workflow + reframed floor
- `Backend/CLAUDE.md`, root `CLAUDE.md` — status updates
