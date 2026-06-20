# Phase 0 Research: Scenario RAG Corpus for Staged Assessment Question Generation

## Sources Reviewed

- `/Users/mohamed3wes/Downloads/Grad-Project/specs/005-scenario-rag-corpus/spec.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/.specify/memory/constitution.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md` (referenced via 002 research)
- `/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/research.md` (decisions 2, 3, 4, 6, 7, 8 carry forward)
- `/Users/mohamed3wes/Downloads/Grad-Project/specs/004-assessment-role-expansion/spec.md` (eight-role baseline)
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/ai_pipeline.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/fallback_scenarios.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/role_graph_data.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/engine.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/core/ai_settings.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/core/ai_validation.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/ai-models/src/rag/vector_store.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/ai-models/src/rag/embeddings.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/requirements.txt`

## Decision 1: Retrieval runs inside the Backend Django process, not in ai-models

**Decision**: `Backend/apps/assessments/scenario_retriever.py` imports `chromadb` and `sentence_transformers` directly. It does **not** import from `ai-models/src/rag/*`.

**Rationale**: ADR-001 and 002 research Decision 2 require runtime to live in `Backend/apps/`. `ai-models` is support-only. Although `-e ../ai-models` is installed in `Backend/requirements.txt`, importing its RAG helpers at runtime would silently couple the assessment runtime to the ai-models package and re-create the boundary violation those decisions exist to prevent.

**Alternatives considered**:

- Re-export and use `ai_models.src.rag.vector_store.add_documents` / `search`: rejected because it pulls ai-models into the runtime call graph and uses a singleton client/collection shared with the unrelated `career_knowledge` collection.
- Extract a new shared `apps.core.rag` helper module: rejected as premature — this is the only consumer in the backend today; the right time to extract is when a second consumer materializes.

## Decision 2: Dedicated vector store directory and collection

**Decision**: New setting `SCENARIO_VECTOR_DB_PATH` (default `<BASE_DIR>/data/scenario_vector_db/`) holds a Chroma `PersistentClient`. The collection name is `assessment_scenarios`. Both are isolated from the existing `CHROMA_PERSIST_DIR` and `career_knowledge` collection used by the advisory RAG.

**Rationale**: Per the user's explicit decision in the planning conversation. Isolation prevents cross-contamination of metadata schemas, lets the advisory RAG and the assessment RAG evolve independently (different metadata keys, different embedding dimensions if either is ever swapped), and makes it trivial to wipe and rebuild one index without touching the other.

**Alternatives considered**:

- Reuse `CHROMA_PERSIST_DIR` with a new collection named `assessment_scenarios`: rejected by user. Simpler at the process level (one Chroma client) but tangles two unrelated retrieval features into one operational artifact.
- Use SQLite or a flat JSON file: rejected because semantic similarity over 384-dim embeddings is the whole point, and Chroma is already a dependency.

## Decision 3: Retrieval is gated by a feature flag

**As-built note (2026-06):** the implementation currently defaults
`ASSESSMENT_SCENARIO_RAG_ENABLED` to `true` in `Backend/apps/core/ai_settings.py`.
This remains reversible by environment override, and retrieval safely returns an
empty list when no approved matching scenario exists.

**Decision**: New setting `ASSESSMENT_SCENARIO_RAG_ENABLED` defaults to `False`. When false, `_build_stage_prompt()` produces a byte-identical prompt to today's behavior. Flag flip is the only rollout/rollback control.

**Rationale**: Spec FR-002, SC-003, and SC-005 require reversibility via a single configuration change. The original plan preferred default-off; the as-built system defaults on because empty retrieval is safe and environments can still opt out independently.

**Alternatives considered**:

- Per-role rollout flag (`ASSESSMENT_SCENARIO_RAG_ROLES`): kept on the roadmap as a follow-up but **not** added in v1, to keep the surface minimal. The global flag is sufficient because corpus content is keyed by `role_key`; a role with no approved scenarios simply gets `[]` from retrieval and falls through to the static block.
- Default-on with empty corpus: rejected because it changes prompt content the moment the feature merges, even before any content is approved.

## Decision 4: Corpus version invalidates stage-one cache, mirroring CURATED_VERSION

**Decision**: New constant `SCENARIO_CORPUS_VERSION` in `scenario_corpus/registry.py`. `AssessmentAIService._stage_one_cache_key()` is extended to include `SCENARIO_CORPUS_VERSION` so cached stage-one questions invalidate when the corpus is bumped, mirroring the `CURATED_VERSION` pattern from `role_graph_data.py` and 002 research Decision 8.

**Rationale**: When the corpus changes, the retrieved few-shot examples in the prompt change, which changes the prompt the cached stage-one questions were generated from. Without invalidation, users would keep receiving stage-one questions produced from stale examples.

**Alternatives considered**:

- Hash the corpus content and use the hash as the key suffix: more precise, but requires a corpus-content fingerprint computed at startup. The explicit `SCENARIO_CORPUS_VERSION` bump is simpler, is human-readable in cache keys, and matches the pattern operators already understand from `CURATED_VERSION`.
- Time-based TTL only: rejected because TTL keeps stale prompts alive longer than necessary after a known content change.

## Decision 5: Embedding text is a short blueprint-shaped concatenation, not the JSON document

**Decision**: The Chroma `document` text (what gets vectorized) is:

```
{competency} | {question_type} | stage {stage}
{scenario_context}
{stem}
```

The full `ScenarioDocument` JSON is stored in the Chroma `metadata.payload` so retrieval returns a drop-in few-shot block.

**Rationale**: The runtime retrieval query is built from the blueprint (`competency`, `question_type`, `stage`, `focus`). Embedding the scenario + stem aligns nearest-neighbor in 384-dim space with the actual question shape the LLM is being asked to produce. Embedding the JSON would pollute the vector with noise from `option_rationales`, IDs, and provenance fields.

**Alternatives considered**:

- Embed the full JSON: rejected; lowers retrieval precision and inflates token counts to the embedder.
- Embed only the `stem`: rejected; loses the scenario context that drives "is this on-topic for backend HTTP API design?" matching.

## Decision 6: Hard metadata filter on (role_key, question_type, stage); semantic ranking happens within the filter

**Decision**: `ScenarioRetriever.retrieve_for_blueprint()` always passes `where={"$and": [{"role_key": role_key}, {"question_type": question_type}, {"stage": stage}]}` to Chroma's `collection.query()`. Top-k similarity ranking is applied only within that subset.

**Rationale**: Cross-role bleed (a backend scenario surfacing for a frontend blueprint) would produce wrong-shaped few-shot examples and degrade output. Stage and question_type filters keep the example schema correct (e.g. `multi_select` retrieval cannot return an `open_ended` example with empty `options`).

**Alternatives considered**:

- Soft filter by boosting score for same-role results: rejected because it admits the failure mode the spec edge-cases explicitly call out.
- Filter by `subskill_key` as well: rejected. The blueprint's `subskill_key` is the dominant retrieval signal in the embedded text already, and hard-filtering on subskill would force a per-cell minimum of 1 (acceptable) but eliminate the option to surface a related-subskill example for diversity within the same dimension.

## Decision 7: One retrieved example per blueprint, capped at 5 per prompt, deduplicated by doc_id

**Decision**: `top_k=1` per blueprint × 5 blueprints per prompt = up to 5 retrieved examples. A global cap of 5 is enforced in case retrieval evolves. Deduplication by `doc_id` prevents the same scenario from filling multiple slots within one prompt.

**Rationale**: Five blueprints × 1 example each matches the prompt's actual slot count. Five additional examples on top of the existing three static `STAGE_QUESTION_FEW_SHOT_EXAMPLES` is the right token-budget shape for the 32k-token Gemini Flash Lite default model. Dedup is required because `Stage2Allocator` can re-pick a subskill across a uncertain/high-priority rotation.

**Alternatives considered**:

- `top_k=2` per blueprint for diversity: deferred to v1.1 (mentioned in plan timeline) and only when ≥3 scenarios per cell exist; with the v1 floor at ≥1–2 per cell, `top_k=2` would frequently return near-duplicates flagged by the audit.
- Inject the full retrieved JSON: rejected; we render a slimmed few-shot block (see Decision 9) to control token cost.

## Decision 8: Authored content is validated by the live question-contract validator at ingest time

**Decision**: `scenario_corpus/schema.py:validate_scenario()` calls `apps.core.ai_validation.build_stage_validation_flags()` against the scenario shaped as a question. Any returned flag fails validation. Additional corpus-only invariants (known `role_key`, known `subskill_key`, `dimension_key` matches `role_graph_data.py`) are enforced in the same function.

**Rationale**: The contract-safe path (`ai_pipeline._build_contract_safe_question()`) already raises if a fallback template fails `build_stage_validation_flags()`. Using the same validator at corpus ingest time guarantees the corpus cannot drift below the in-production validation bar.

**Alternatives considered**:

- A separate, looser corpus validator: rejected; would allow a scenario that the live system would later reject, defeating the safety guarantee.
- Validate only in the management command, not at app-ready: rejected; would let invalid content land in version control silently until the next index rebuild. App-ready validation surfaces the problem on the first `manage.py` invocation.

## Decision 9: Seed the v1 corpus by converting BACKEND_FALLBACK_SCENARIOS

**Decision**: `scenario_corpus/backend.py` ships with the 10 existing `BACKEND_FALLBACK_SCENARIOS` entries re-expressed as `ScenarioDocument`s with stable `doc_id`s of the form `backend.<subskill_key>.s<stage>.<question_type>.fallback-seed`, `review_status="approved"`, `corpus_version=SCENARIO_CORPUS_VERSION`, and `author="internal-seed-from-fallback-scenarios"`.

**Rationale**: This is the highest-quality material we already own. Reusing it (a) gives day-one retrieval hits for backend without authoring effort, (b) provides a working canonical reference for content authors who will fill the other roles, and (c) lets the smoke retrieval test pass on the first ingest. `BACKEND_FALLBACK_SCENARIOS` itself stays in place untouched — it is the deterministic safety net at the failure boundary, not a corpus.

**Alternatives considered**:

- Ship empty corpus and let retrieval return `[]` until content is authored: rejected by user. Loses immediate value on backend and makes smoke retrieval test a no-op until content lands.
- Auto-import LinkedIn / external sources: rejected; they are not scenario-shaped and would dilute the quality bar (see review in prior chat). The taxonomy map and adapter script live in v1 but produce drafts only, never auto-approved entries.

## Decision 10: Eight first-class roles, no others

**Decision**: The corpus and the audit floor enforce coverage for exactly the eight roles enumerated in `role_graph_data.py` after the 004 baseline: `backend`, `frontend`, `fullstack`, `data_science`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`. Any other `target_career` value resolves through the existing `resolve_role_key()` to one of these.

**Rationale**: This matches the approved runtime role set per Spec 004 FR-001. Scenarios for unknown roles would be unretrievable and would fail `validate_scenario()` at the `role_key` existence check.

**Alternatives considered**:

- Support additional speculative roles "ready for when they get added": rejected; FR-009 of this spec mandates rejecting scenarios whose `role_key` is not in the approved curated graph.

## Decision 11: Content authoring is delivered in follow-up PRs, role by role

**Decision**: v1 PR delivers wiring + tests + management commands + the 10-scenario backend seed. Subsequent PRs fill the v1 floor one role at a time. Each role PR must pass the `scenario_corpus_audit` coverage gate for that role before merge.

**Rationale**: Per user's explicit decision in the planning conversation. Decouples engineering rollout from content velocity. Lets the feature ship behind the flag immediately and lets the corpus grow incrementally with mechanical quality gates.

**Alternatives considered**:

- Block v1 PR until full corpus is authored: rejected; would delay the engineering work by ~6+ weeks for no engineering benefit.
- Ship empty corpus with a "do not enable" warning: rejected; the seed conversion is essentially free and gives backend immediate value.

## Decision 12: Coverage floor per role × stage × question_type cell

**Decision**: For every approved role:

- Stage 1 single_choice: ≥ 2 scenarios per subskill in the stage-1 allocation set (which is the first subskill of each dimension + the second subskill of the highest-weight dimension, deterministic per `engine.StageAllocator.allocate_stage_one`).
- Stage 2 single_choice: ≥ 2 scenarios per subskill across all 16 role subskills.
- Stage 2 multi_select: ≥ 1 scenario per subskill across all 16 role subskills.
- Stage 2 open_ended: ≥ 1 scenario per subskill across all 16 role subskills.

The `scenario_corpus_audit` command computes this matrix and exits non-zero if any cell is below floor.

**Rationale**: Stage 2 question type assignment is positional but the `open_ended` slot can swap toward `gap_profile.uncertain_areas` (`ai_pipeline._build_stage_blueprints()` lines 159–171). To guarantee a retrievable match for any allocation outcome, every stage-2 question type needs at least one scenario per subskill.

**Alternatives considered**:

- Floor only on the stage-1 allocation set: rejected; Stage 2 can land on any subskill, so partial coverage produces hard-to-debug "why did this slot not get a retrieved example" inconsistencies.
- Higher floor (≥3 per cell): kept as v1.1 stretch goal; the v1 floor is the minimum that makes retrieval guaranteed non-empty per blueprint.

## Decision 13: Near-duplicate detection at audit time, not at retrieval time

**Decision**: `scenario_corpus_audit` embeds every approved scenario and computes pairwise cosine similarity within each `(role_key, subskill_key, question_type)` cluster. Pairs above 0.92 are flagged as near-duplicates.

**Rationale**: Spec FR-011. Catching duplicates at audit time (offline) means retrieval at runtime can stay simple: nearest-neighbor with no diversity penalty. The audit is the right place to enforce diversity because the cost of recomputation is paid once per change.

**Alternatives considered**:

- MMR (maximal marginal relevance) at retrieval time: deferred to v1.1; adds runtime complexity for marginal benefit when `top_k=1`.
- No duplicate check: rejected; over time the corpus would collapse into rephrased versions of the same scenario and erode retrieval diversity.

## Decision 14: No new outbound network dependency, no new secrets

**Decision**: All Phase-1 work runs against locally installed `sentence-transformers/all-MiniLM-L6-v2` and a local Chroma persistent directory. No call to Gemini, OpenAI, Hugging Face Hub at request time, no API key required. The model is downloaded by `sentence-transformers` on first use (one-time, cached under user's hf cache).

**Rationale**: Constitution Principle IV (Responsible AI & Data Protection) — no new provider, no new credential surface, demo-safe by default. Aligns with ADR-001's local/no-cost posture.

**Alternatives considered**:

- Use a hosted embedding API: rejected; reintroduces API cost and a new credential.
- Pre-bundle the embedding model artifact in the repo: rejected; ~80MB, better handled by the sentence-transformers cache.

## Decision 15: Structured logging keys are stable and queryable

**Decision**: Retrieval emits exactly one log event per blueprint with `extra={"event": "scenario_retrieval", "role_key": ..., "subskill_key": ..., "question_type": ..., "stage": ..., "results_count": ..., "top_doc_id": ..., "top_score": ..., "corpus_version": ...}`. The single per-generation failure path emits `{"event": "scenario_retrieval_failed", "error_type": type(error).__name__}`.

**Rationale**: Constitution Principle V (Operational Visibility & Simplicity) — log keys must be stable enough to build a hit-rate dashboard without revisiting the code. The same keys are used by the smoke retrieval test to assert behavior.

**Alternatives considered**:

- Free-form log messages: rejected; harder to aggregate.
- No logging: rejected; spec FR-014 mandates structured retrieval logging.
