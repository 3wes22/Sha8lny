# Quality Refinement Implementation Plan — Knowledge-Layer-First Final Stretch

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute the approved spec (`docs/superpowers/specs/2026-06-10-quality-refinement-design.md`) — refine all five AI modules to defense quality in ~30 days, root-cause-first.

**Architecture:** Week 1 rebuilds the shared knowledge layer (corpus, chunking, retrieval) with a measured eval baseline captured *before* any improvement lands. Weeks 2–3 refine the dependent modules (advisory UI, roadmap provenance, scenario corpus, courses, jobs ranker, assessment methodology). Week 4 is evaluation, academic documentation, and demo hardening — no feature work.

**Tech Stack:** Django/DRF + pytest (Backend), React/TS/Vite (Frontend), Chroma + sentence-transformers + LightGBM (ai-models). No new infrastructure; `rank-bm25` is the only new dependency.

**Rules that bind every task:**
- The full Backend suite (`cd Backend && pytest`) must stay green after every task that touches `Backend/`. Frontend tasks end with a clean `npm run build`.
- Every external data source gets its `docs/product/DATASET_REGISTRY.md` entry (URL, license, size, credibility, USE/REJECT) **before** any ingestion code runs.
- Every new retrieval/AI path keeps a deterministic fallback (demo must survive a dead `GEMINI_API_KEY` or missing Chroma volume).
- Commit at the end of every task with a descriptive message.

---

## Week 1 — Knowledge layer rebuild + eval control group

> Sequencing constraint: Tasks 1.1–1.3 establish the measured baseline of the **current** pipeline. No corpus, chunking, or retrieval change may land before 1.3 is committed.

### Task 1.1 — Retrieval eval metrics module
Files: Create `ai-models/src/rag/eval_metrics.py`; Create `ai-models/tests/test_eval_metrics.py`
Deliverable: Pure-Python implementations of `recall_at_k`, `precision_at_k`, `mrr`, each taking `(retrieved_ids: list, relevant_ids: set, k)` and returning a float; written TDD (tests first), no Chroma/network dependencies.
Acceptance: `cd ai-models && python -m pytest tests/test_eval_metrics.py -v` — all green, including edge cases (empty retrieval, no relevant docs, k > result count).
Depends on: none

### Task 1.2 — Retrieval eval question set (≥50 pairs)
Files: Create `ai-models/data/eval/retrieval_eval_set.jsonl`; Create `ai-models/tests/test_eval_set_schema.py`
Deliverable: ≥50 realistic career-advisory queries, each with `query`, `relevant_doc_ids` (or `relevant_passages` with source+section), and `source` fields, drawn from the **current** corpus (O*NET, knowledge_base, roadmap.sh) so the baseline is measurable. Schema test validates required fields and count ≥50.
Acceptance: `cd ai-models && python -m pytest tests/test_eval_set_schema.py -v` green.
Depends on: none (parallel with 1.1)

### Task 1.3 — Eval runner + BASELINE measurement (control group)
Files: Create `ai-models/scripts/run_retrieval_eval.py`; Create `ai-models/eval_results/retrieval/baseline.json` (run artifact, committed)
Deliverable: Runner that loads the eval set, calls the current `rag.retriever.retrieve_context` against the existing Chroma collection, computes Recall@5/10, Precision@5, MRR via `eval_metrics`, and writes a labeled results JSON (`{"stage": "baseline", "metrics": {...}, "timestamp": ...}`).
Acceptance: `cd ai-models && python scripts/run_retrieval_eval.py --stage baseline` completes; `eval_results/retrieval/baseline.json` contains non-null metrics; file is committed. (Env note: needs the local Chroma volume in `ai-models/data/vector_db/` and sentence-transformers. **Discovered during Task 1.1:** `ai-models/venv` is broken — pytest shim present, module missing — so this task starts by repairing/recreating the venv from `requirements.txt`. Until then the suite runs on system Python 3.13, where `tests/conftest.py` pins `OMP_NUM_THREADS=1` to avoid a pre-existing lightgbm/OpenMP segfault at interpreter shutdown.)
Depends on: Task 1.1, Task 1.2. **Blocks 1.6–1.10.**

### Task 1.4 — DATASET_REGISTRY.md for all existing sources
Files: Create `docs/product/DATASET_REGISTRY.md`
Deliverable: Registry with one entry per **already-ingested** source — O*NET 30.1 (public domain), roadmap.sh (personal-use-only → Decision: dev-only fallback, never the defended corpus), Wuzzuf jobs CSV, scenario-corpus references from `backend.py`, seeded course catalog. Each entry: Source URL, License, Size, Quality indicators, Relevance, Credibility rationale, Decision (USE/REJECT/PARTIAL).
Acceptance: File exists; every source named in `ai-models/data/CITATIONS.md` and `ai-models/data/` subdirs has an entry with License and Decision filled — verify by cross-reading the two files.
Depends on: none

### Task 1.5 — Corpus acquisition research (license-first, no code)
Files: Modify `docs/product/DATASET_REGISTRY.md` (append candidate entries)
Deliverable: ≥4 APPROVED (Decision: USE) license-clean sources for the career-guidance corpus, researched via Tavily/Exa/Nimble — targets: government/official career guides (e.g., O*NET ancillary products, public-domain occupational outlooks), CC-licensed technical learning content, authoritative Egyptian-market material. Rejected candidates stay in the registry with their rejection reason (license, quality).
Acceptance: Registry diff shows new entries, each with explicit License and Decision **before any ingestion code exists** (requirement 4); `git diff` for this task touches only the registry.
Depends on: Task 1.4

### Task 1.6 — Structure-aware chunker
Files: Create `ai-models/src/rag/chunking.py`; Create `ai-models/tests/test_chunking.py`; Modify `ai-models/src/rag/build_vector_db.py` (replace `chunk_text` usage)
Deliverable: Chunker that splits on headings/paragraph boundaries with sentence-boundary overlap, emitting `(text, metadata)` pairs with `source`, `url`, `section`, `doc_type`, `quality_tier`. `build_vector_db.py` calls it instead of the fixed 500-char `chunk_text`.
Acceptance: `cd ai-models && python -m pytest tests/test_chunking.py -v` green, including a fixture-doc test asserting no chunk starts/ends mid-sentence and headings map to `section` metadata.
Depends on: Task 1.3 (baseline locked)

### Task 1.7 — Ingest approved sources, rebuild collection, re-measure
Files: Create `ai-models/scripts/fetch_corpus_sources.py` (download/parse approved sources into `ai-models/data/knowledge_base/<source_slug>/`); Modify `ai-models/src/rag/build_vector_db.py` (register new sources with metadata); Create `ai-models/eval_results/retrieval/corpus_chunking.json`
Deliverable: `career_knowledge` rebuilt from license-clean sources + new chunker (roadmap.sh chunks tagged `quality_tier: dev_fallback`); eval re-run recorded as stage `corpus_chunking`.
Acceptance: Build script prints a collection document count > the pre-rebuild count from licensed sources alone; `python scripts/run_retrieval_eval.py --stage corpus_chunking` writes committed results; eval-set doc-id mappings updated if chunk ids changed (schema test still green).
Depends on: Task 1.5, Task 1.6

### Task 1.8 — Hybrid retrieval (BM25 + dense, RRF)
Files: Create `ai-models/src/rag/hybrid_search.py`; Create `ai-models/tests/test_hybrid_search.py`; Modify `ai-models/src/rag/retriever.py` (`retrieve_context` gains hybrid path); Modify `ai-models/requirements.txt` (add `rank-bm25`)
Deliverable: BM25 index over chunk texts + reciprocal rank fusion with dense results; if `rank_bm25` is unimportable or the index is missing, retrieval degrades to dense-only (mirrors existing advisory fault-tolerance).
Acceptance: `cd ai-models && python -m pytest tests/test_hybrid_search.py -v` green, including the dense-only fallback test; `python scripts/run_retrieval_eval.py --stage hybrid` committed with metrics ≥ `corpus_chunking` stage (if not, diagnose before proceeding).
Depends on: Task 1.7

### Task 1.9 — Cross-encoder re-ranking
Files: Create `ai-models/src/rag/reranker.py`; Create `ai-models/tests/test_reranker.py`; Modify `ai-models/src/rag/retriever.py` (optional rerank stage after fusion)
Deliverable: `cross-encoder/ms-marco-MiniLM-L-6-v2` reranks the top-20 fused candidates down to top-k; controlled by a runtime setting; gracefully skipped (with logged warning) if the model can't load.
Acceptance: `cd ai-models && python -m pytest tests/test_reranker.py -v` green using an injected fake scorer (no model download in tests); `python scripts/run_retrieval_eval.py --stage rerank` committed.
Depends on: Task 1.8

### Task 1.10 — Citation payload, confidence tiering, metadata filtering
Files: Modify `ai-models/src/rag/retriever.py` (each returned doc carries `source`, `url`, `section`, `confidence_tier`; `retrieve_context` accepts a metadata `filters` dict); Create `ai-models/tests/test_retriever_contract.py`; Modify `Backend/apps/advisory/llm_service.py` `_normalize_documents` (pass the new fields through); Extend `Backend/apps/advisory/tests.py`
Deliverable: HIGH/MEDIUM/LOW confidence per doc derived from rerank score + source `quality_tier`; role/source filtering so roadmap and advisory share the collection cleanly; advisory normalization preserves the new fields end-to-end.
Acceptance: `cd ai-models && python -m pytest tests/test_retriever_contract.py -v` green; `cd Backend && pytest apps/advisory/ -v` green.
Depends on: Task 1.9

### Task 1.11 — Week-1 measured-improvement table
Files: Create `docs/product/RAG_RETRIEVAL_EVAL.md`
Deliverable: Table of all four eval stages (baseline → corpus_chunking → hybrid → rerank) with per-metric deltas, env notes, and honest commentary on any stage that didn't improve. This is thesis evidence and feeds Week 4's `EVALUATION_REPORT.md`.
Acceptance: Doc lists every committed `eval_results/retrieval/*.json` stage; numbers match the JSON artifacts exactly.
Depends on: Task 1.10

---

## Week 2 — Module refinements on the new layer

### Task 2.1 — Land in-flight roadmap/assessment working-tree changes
Files: Modify (already modified, uncommitted): `Backend/apps/roadmaps/ai_pipeline.py`, `Frontend/src/features/assessment/routes/AssessmentResultsPage.tsx`, `Frontend/src/features/roadmap/routes/RoadmapPage.tsx`
Deliverable: The developer's uncommitted changes reviewed, covered by existing tests, and committed (or split/reverted if review finds problems — surface findings before discarding anything).
Acceptance: `cd Backend && pytest apps/roadmaps/ -v` green; `cd Frontend && npm run build` clean; `git status` shows those three files clean.
Depends on: none — do first; it unblocks 2.4

### Task 2.2 — Advisory API: citations + confidence in chat response
Files: Modify `Backend/apps/advisory/llm_service.py`, `Backend/apps/advisory/serializers.py`; Extend `Backend/apps/advisory/tests.py`
Deliverable: Chat response payload exposes `retrieved_documents` as `[{source, url, section, excerpt, confidence_tier}]`; the `no_retrieval_context` error path returns an explicit machine-readable flag the frontend can render.
Acceptance: `cd Backend && pytest apps/advisory/ -v` green including a new response-contract test asserting all five fields.
Depends on: Task 1.10

### Task 2.3 — Advisory frontend: Sources UI + no-context state
Files: Create `Frontend/src/features/advisory/components/MessageSources.tsx`; Modify `Frontend/src/features/advisory/routes/AdvisoryPage.tsx`, `Frontend/src/features/advisory/routes/AdvisoryPage.test.tsx`, `Frontend/src/lib/api.ts` (types)
Deliverable: Collapsible "Sources" block under each assistant message (source label, excerpt, confidence badge); a distinct UI state for `no_retrieval_context` ("I don't have grounded information on that") instead of an ungrounded answer.
Acceptance: `cd Frontend && npm run build` clean; `AdvisoryPage.test.tsx` covers sources rendering and the no-context state from mocked payloads.
Depends on: Task 2.2

### Task 2.4 — Roadmap retrieval on rebuilt collection + provenance completion
Files: Modify `Backend/apps/roadmaps/path_retriever.py` (metadata filter: licensed sources first, roadmap.sh as flagged dev fallback), `Backend/apps/roadmaps/assembler.py` (complete provenance: `structure_source`, `retrieved_urls`, `onet_mappings`, honest `fallback_used`); Extend `Backend/apps/roadmaps/tests/`
Deliverable: Generated roadmaps carry complete, honest provenance metadata sourced from the rebuilt collection.
Acceptance: `cd Backend && pytest apps/roadmaps/ -v` green including a provenance contract test asserting all four fields and that `fallback_used` is true when Chroma is absent (existing fault-injection pattern).
Depends on: Task 1.7, Task 2.1

### Task 2.5 — Roadmap Sources panel per phase
Files: Modify `Frontend/src/features/roadmap/components/RoadmapSourcesPanel.tsx`, `Frontend/src/features/roadmap/routes/RoadmapPage.tsx`, `Frontend/src/features/roadmap/routes/RoadmapPage.test.tsx`
Deliverable: Each roadmap phase displays ≥1 external source link from provenance metadata; fallback-generated roadmaps show an honest "deterministic template" badge instead of fake sources.
Acceptance: `cd Frontend && npm run build` clean; `RoadmapPage.test.tsx` covers both the sourced and fallback render paths from fixtures.
Depends on: Task 2.4

### Task 2.6 — Scenario corpus batch A: frontend + fullstack
Files: Modify `Backend/apps/assessments/scenario_corpus/frontend.py`, `Backend/apps/assessments/scenario_corpus/fullstack.py`; Modify `docs/product/DATASET_REGISTRY.md` (entries for any external content referenced)
Deliverable: `SCENARIOS` populated for both roles per `AUTHOR_GUIDE.md` (matching `backend.py`'s coverage pattern, `review_status="approved"`), content researched via connectors and license-logged.
Acceptance: `cd Backend && python manage.py scenario_corpus_audit` passes for `frontend` and `fullstack` with no warnings; `python manage.py rebuild_scenario_index` succeeds; `pytest apps/assessments/ -v` green.
Depends on: none (independent of Week-1 collection; registry rule applies)

### Task 2.7 — Scenario corpus batch B: data_science + machine_learning_engineer + devops
Files: Modify `Backend/apps/assessments/scenario_corpus/data_science.py`, `machine_learning_engineer.py`, `devops.py`; Modify `docs/product/DATASET_REGISTRY.md`
Deliverable: Same as 2.6 for three more roles.
Acceptance: Same commands as 2.6, passing for all three roles.
Depends on: Task 2.6 (reuse its authoring workflow and any shared source approvals)

### Task 2.8 — Scenario corpus batch C: android + ui_ux_designer
Files: Modify `Backend/apps/assessments/scenario_corpus/android.py`, `ui_ux_designer.py`; Modify `docs/product/DATASET_REGISTRY.md`
Deliverable: Final two roles seeded; all 8 roles now retrieve role-specific scenarios — no silent fallback to generic questions.
Acceptance: `python manage.py scenario_corpus_audit` passes for **all 8 roles**; `pytest apps/assessments/ -v` green.
Depends on: Task 2.7

### Task 2.9 — Course↔milestone matching populated (C9)
Files: Modify `Backend/apps/roadmaps/services.py` and/or `Backend/apps/roadmaps/tasks.py` (invoke the existing embedding matcher after roadmap generation); Extend `Backend/apps/roadmaps/tests/`; Modify `CLAUDE.md` (correct the stale "courses URL route disabled" note — route is wired at `Backend/config/urls.py:66`)
Deliverable: Demo roadmaps get `RoadmapCourse` rows with `match_score > 0` and a templated `recommendation_reason` ("Covers {skills}") on ≥2 milestones.
Acceptance: `cd Backend && pytest apps/roadmaps/ apps/courses/ -v` green including a new test that generates a fixture roadmap and asserts populated `RoadmapCourse` rows.
Depends on: Task 2.4

---

## Week 3 — Jobs real-data upgrade + assessment credibility

### Task 3.1 — Registry entry for job-posting acquisition (license/ToS first)
Files: Modify `docs/product/DATASET_REGISTRY.md`
Deliverable: Entry for the chosen collection path — Nimble-assisted Wuzzuf collection if ToS permits, otherwise curated CSV export (the predecessor spec's blessed fallback) — with ToS notes and the decision recorded.
Acceptance: Entry exists with License/ToS and Decision filled; no ingestion code in this task's diff (requirement 4).
Depends on: Task 1.4

### Task 3.2 — Ingest ≥100 real Egyptian postings
Files: Modify `Backend/apps/jobs/ingest/wuzzuf.py` and/or `Backend/apps/jobs/ingest/csv_loader.py` (extend only as needed); Add data file under `ai-models/data/raw/`; Extend `Backend/apps/jobs/tests/`
Deliverable: ≥100 Job rows with real `external_url`, `posted_date`, `scraped_at`, `platform_metadata.source`; fabricated seed jobs remain dev-only.
Acceptance: Ingest parser tests green on committed fixtures (no live network in CI); `cd Backend && python manage.py shell -c "from apps.jobs.models import Job; print(Job.objects.filter(platform_metadata__source='wuzzuf').count())"` reports ≥100.
Depends on: Task 3.1

### Task 3.3 — Enable skill_embedding_cosine + retrain ranker on real data
Files: Modify `ai-models/src/recommendations/feature_engineering.py` (only if the embedding path needs fixes — root cause was sentence-transformers unavailable in the training env, so primarily an environment fix); Regenerate `ai-models/data/job_ranker_training.json` (via `manage.py export_jobs_for_ranker --real-only`) and `ai-models/models/custom/job_ranker.lgb` (via `ai-models/scripts/train_job_ranker.py`)
Deliverable: Retrained model where `skill_embedding_cosine` is non-zero across training pairs.
Acceptance: `cd ai-models && python -m pytest tests/test_model_loading.py -v` green; a spot-check script/assertion shows non-zero embedding-feature values in the regenerated training export; new model file committed.
Depends on: Task 3.2

### Task 3.4 — Re-run LOGO eval + regenerate EVAL_REPORT.md
Files: Regenerate `ai-models/models/custom/job_ranker_eval.json`; Modify `ai-models/models/custom/EVAL_REPORT.md`
Deliverable: Updated report with a before/after table — old run (synthetic fixtures, embedding disabled) vs. new run (real postings, embedding enabled) — and updated limitations.
Acceptance: `cd ai-models && python -m pytest tests/test_ranker_eval.py -v` green; report contains both result sets with the same metric definitions.
Depends on: Task 3.3

### Task 3.5 — ROLE_GRAPH_METHODOLOGY.md + taxonomy_map
Files: Create `docs/product/ROLE_GRAPH_METHODOLOGY.md`; Modify `Backend/apps/assessments/scenario_corpus/taxonomy_map.py` (≥15 entries); Extend `Backend/apps/assessments/tests/`
Deliverable: Dimensions and weights documented per role (from `role_graph_taxonomy.py` curated-v3, which overrides the legacy graphs in `role_graph_data.py`); O*NET task-statement crosswalk — Backend Developer in depth, Frontend and Data Science where mappings are clean, element IDs cited; taxonomy map populated with an integrity test (every entry resolves to a real `(role_key, subskill_key)`).
Acceptance: `cd Backend && pytest apps/assessments/ -v` green including the new taxonomy integrity test; doc cites concrete O*NET element IDs.
Depends on: none

### Task 3.6 — LLM rubric scoring path for open-ended answers
Files: Modify `Backend/apps/assessments/engine.py` (rubric branch), `Backend/apps/assessments/services.py` (wiring as needed); Extend `Backend/apps/assessments/tests/`
Deliverable: When Gemini is available, open-ended answers score 1–5 against a rubric prompt with `expected_concepts`; `scoring_method` (`"llm_rubric"` | `"keyword_coverage"`) recorded on response metadata; keyword fallback unchanged and automatic on API failure.
Acceptance: `cd Backend && pytest apps/assessments/ -v` green with tests for both paths plus fallback-on-exception (mocked Gemini, existing test patterns from `tests.py`).
Depends on: none

### Task 3.7 — Expert review packet (developer action item enabler)
Files: Create `docs/product/EXPERT_REVIEW_PACKET.md`; Create `docs/product/expert_review_scoring_sheet.csv`
Deliverable: Self-contained packet — 15 open-ended items with engine scores hidden, reviewer instructions, scoring rubric, and a CSV scoring sheet for 3 reviewers (5-item overlap design) — so the developer can run the review without repo access for reviewers. Flag clearly: **recruiting reviewers and running the session is the developer's task.**
Acceptance: Packet contains all 15 items, instructions, and the overlap assignment table; CSV opens with one row per (reviewer, item).
Depends on: Task 3.6 (items must reflect the final scoring paths)

### Task 3.8 — STRETCH: human gold set for the ranker
Files: Create `ai-models/data/eval/job_gold_set_template.csv`; Create `ai-models/scripts/eval_ranker_gold.py`
Deliverable: Labeling template (~50 job–profile pairs sampled from real postings) and a script computing NDCG@5 against human labels. Labeling (~1 hour) is the developer's task.
Acceptance: `python scripts/eval_ranker_gold.py --sample` runs against a 5-row committed sample fixture and prints metrics.
Depends on: Task 3.4

---

## Week 4 — Evaluation, academic package, hardening (no feature work)

### Task 4.1 — Faithfulness + credibility scorers
Files: Create `ai-models/scripts/eval_faithfulness.py`; Create `ai-models/src/rag/credibility.py`; Create `ai-models/tests/test_credibility.py`
Deliverable: LLM-as-judge faithfulness scorer (Gemini judges whether each advisory answer is supported by its retrieved passages; responses cached to disk to respect quota) and a deterministic credibility scorer (fraction of cited sources that are official/peer-reviewed/established, from registry `quality_tier`).
Acceptance: `cd ai-models && python -m pytest tests/test_credibility.py -v` green (deterministic part); faithfulness script runs on a 3-item sample with a mocked judge in tests.
Depends on: Task 1.11

### Task 4.2 — Full evaluation loop: run, diagnose, fix, re-run
Files: Run artifacts in `ai-models/eval_results/` (committed); fixes limited to retrieval configuration, corpus gaps, or prompt adjustments — **no new features**
Deliverable: Final metrics vs. thresholds (faithfulness > 85%, Precision@5 > 70%, credibility > 80%); for any shortfall, a documented root-cause analysis (retrieval vs. generation vs. data gap) and the targeted fix applied and re-measured — or an honest documented miss.
Acceptance: Final-stage eval artifacts committed; each threshold either met or accompanied by written failure analysis.
Depends on: Task 4.1, Weeks 1–3 complete

### Task 4.3 — EVALUATION_REPORT.md
Files: Create `docs/product/EVALUATION_REPORT.md`
Deliverable: Methodology (eval-set construction, metric definitions), baseline vs. final tables, per-technique contribution (from `RAG_RETRIEVAL_EVAL.md` + ranker before/after), honest limitations and failure cases, future-work section.
Acceptance: Every number traces to a committed artifact in `ai-models/eval_results/` or `ai-models/models/custom/`; no unsourced claims.
Depends on: Task 4.2

### Task 4.4 — RAG_ARCHITECTURE.md
Files: Create `docs/product/RAG_ARCHITECTURE.md`
Deliverable: Chunking strategy and rationale; embedding model choice; the four implemented techniques (hybrid+RRF, cross-encoder rerank, citations+confidence, metadata filtering) each with a one-paragraph academic basis (papers found via Exa, cited); Mermaid diagram of the full pipeline; pointer to evaluation methodology.
Acceptance: All four techniques described match the shipped code (file paths referenced); diagram covers ingestion → chunking → embedding → hybrid retrieval → rerank → citation → generation.
Depends on: Task 1.11

### Task 4.5 — ACADEMIC_SUMMARY.md + PROFESSOR_FAQ.md
Files: Create `docs/product/ACADEMIC_SUMMARY.md`; Create `docs/product/PROFESSOR_FAQ.md`
Deliverable: 2-page executive summary (problem, solution novelty, architecture in plain language, key results, data credibility) and pre-answered professor questions ("what's different from calling an API", "how do you know it's accurate", "where did the data come from", "what would you improve") — every answer grounded in a named artifact (EVALUATION_REPORT, DATASET_REGISTRY, EVAL_REPORT, CLAIMS_REGISTER).
Acceptance: Each FAQ answer names its evidence artifact; no claim contradicts the registers.
Depends on: Task 4.3, Task 4.4

### Task 4.6 — Claims/docs sync
Files: Modify `docs/product/CLAIMS_REGISTER.md` (flip statuses with evidence links), `CLAUDE.md` (current state), `docs/product/DATASET_REGISTRY.md` (finalize)
Deliverable: Every claim C1–C11 is Done-with-evidence or an explicit limitation; CLAUDE.md module table reflects reality (including the corrected courses note from 2.9).
Acceptance: Cross-read: no claim marked Done without a verifiable artifact path; no stale status against shipped code.
Depends on: Task 4.2

### Task 4.7 — Full-loop integration test update
Files: Extend the existing full-loop test in `Backend/apps/*/tests/` (locate `test_full_loop` at task start — predecessor spec places it; extend, don't duplicate)
Deliverable: One test covering assessment → roadmap (with provenance) → courses (populated) → jobs (ranked, explained) → advisory (cited), all on deterministic fallbacks (no network).
Acceptance: `cd Backend && pytest -v` — full suite green including the extended loop test.
Depends on: Task 4.2

### Task 4.8 — Demo hardening + rehearsal checklist
Files: Modify `docs/product/GRADUATION_DEMO_RUNBOOK.md`
Deliverable: Verified offline run (dead `GEMINI_API_KEY`, no Chroma volume) recorded step-by-step; fresh-API-key rehearsal checklist; quota-budget note (full test runs exhaust quota — rehearse on a fresh key, never run the suite right before the demo).
Acceptance: Both runbook paths (online, offline) executed once end-to-end locally and their observed outputs recorded in the runbook.
Depends on: Task 4.7

---

## Self-review record

- **Spec coverage:** §2 corpus/chunking/retrieval/harness → 1.1–1.11; §3.1 advisory → 2.2–2.3; §3.2 roadmap → 2.1, 2.4–2.5; §3.3 scenarios → 2.6–2.8; §3.4 courses → 2.9; §4.1 jobs → 3.1–3.4, 3.8; §4.2 assessment credibility → 3.5–3.7; §5 evaluation/academic/hardening → 4.1–4.8. No spec section without a task.
- **Known unknown, flagged not hidden:** exact location of the existing full-loop test (4.7) is resolved at task start; everything else uses verified paths.
- **Control-group rule honored:** 1.3 blocks 1.6–1.10. **Registry-first rule honored:** 1.5 → 1.7, 3.1 → 3.2, registry touches inside 2.6–2.8.
