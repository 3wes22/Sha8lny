# Quality Refinement: Knowledge-Layer-First Final Stretch

**Date:** 2026-06-10
**Status:** Approved in brainstorming session; awaiting written-spec review
**Timeline:** ~30 days to defense/submission
**Predecessor:** `2026-05-30-claims-to-reality-design.md` (claims C1–C11; this spec continues it, it does not replace it)

---

## 1. Context and decision record

The developer pasted a generic "graduation project master mission" (Phases 0–6: context ingestion, audit, feature architecture, dataset acquisition, RAG build, evaluation, academic docs). Exploration showed the project is ~82% complete and most mission deliverables already exist in domain-specific form:

| Mission deliverable | Existing artifact |
|---|---|
| CONTEXT_MAP.md | `CLAUDE.md`, `docs/product/ARCHITECTURE.md`, `REPOSITORY_GUIDE.md`, `SRS.md` |
| AUDIT_REPORT.md / FEATURE_PLAN.md | `2026-05-30-claims-to-reality-design.md` + `docs/product/CLAIMS_REGISTER.md` |
| RAG system | Scenario RAG corpus (assessments) + Chroma `career_knowledge` (advisory/roadmaps) |
| EVALUATION_REPORT.md | `ai-models/models/custom/EVAL_REPORT.md` (job ranker, LOGO NDCG/MAP) |

**Decisions made with the developer (2026-06-10):**

1. **Mission is intent, not script.** Keep the existing vision, stack, and features. Refine only what is feature-wise poor; rebuild only the very bad parts. No Supabase migration (stack stays Django + SQLite/Postgres + Chroma); no ground-up RAG rebuild.
2. **All five AI modules are considered weak by the developer** and are in refinement scope: advisory (worst — poor answer quality due to the knowledge base; not genuinely usable from the frontend), assessment (7/8 scenario-corpus roles are empty stubs), roadmap (provenance mid-flight), jobs (ranker trained on synthetic fixtures with its embedding feature disabled), courses (route disabled, matching unverified).
3. **~30 days remain.** Enough for deep refinement of all five modules plus the academic docs package, with Week 4 reserved for integration/evaluation/docs (no feature work).
4. **Approach: knowledge-layer-first.** The shared Chroma `career_knowledge` corpus is the root cause behind three of the five weak modules (advisory answers, roadmap structure retrieval, course matching). Fix it once in Week 1, then let dependent modules ride on it.

### Verified current state of the knowledge layer

- Chunking: fixed 500-character chunks with character overlap (`ai-models/src/rag/build_vector_db.py`) — splits mid-sentence, no structure awareness.
- Retrieval: plain dense top-k via `rag.retriever.retrieve_context`; no keyword search, no re-ranking, no enforced citations in the UI.
- Corpus: roadmap.sh (personal-use-only license — dev-only per `ai-models/data/CITATIONS.md`), O*NET 30.1 (public domain), `knowledge_base/` misc.
- Advisory plumbing is sound (fallbacks, `retrieval_failed` / `no_retrieval_context` error codes, tests) — it is kept as-is; the corpus and retrieval quality are what change.

---

## 2. Section 1 — Knowledge layer rebuild (Week 1)

### 2.1 Corpus

- **Keep:** O*NET 30.1 (public domain, strongest license available) and already-ingested real Wuzzuf job rows.
- **Keep as dev-only fallback:** roadmap.sh data (license forbids redistribution; never the defended corpus).
- **Acquire (via Tavily/Exa/Nimble connectors):** authoritative, licensable career content — government/official career guides, CC-licensed technical learning content, authoritative Egyptian-market material.
- **Rule:** every source gets a `DATASET_REGISTRY.md` entry (URL, license, size, quality indicators, credibility rationale, USE/REJECT decision) **before** ingestion. License is checked first, not retroactively.

### 2.2 Chunking

Replace fixed 500-char splitting with structure-aware chunking:

- Split on headings/paragraph boundaries; sentence-boundary overlap.
- Per-chunk metadata: `source`, `url`, `section`, `doc_type`, `quality_tier`.
- Same Chroma + SentenceTransformer stack — no storage migration.

### 2.3 Retrieval (four professor-explainable techniques)

1. **Hybrid search** — dense vectors + BM25 keyword, merged with reciprocal rank fusion (RRF).
2. **Cross-encoder re-ranking** of top candidates (local sentence-transformers cross-encoder; no API cost).
3. **Citation injection + confidence tiering** — every advisory answer carries `[source, confidence]`; surfaced in the UI (closes claim C5).
4. **Metadata filtering** by role/source so roadmap retrieval and advisory share the collection without cross-pollution.

Each technique gets a one-paragraph academic justification (problem it solves, why appropriate here, supporting paper/benchmark found via Exa) recorded in `RAG_ARCHITECTURE.md`.

### 2.4 Evaluation harness (built alongside, not after)

- ~50 question → relevant-passage pairs drawn from the corpus itself, with source passages recorded.
- Retrieval metrics: Recall@K, Precision@K, MRR. Generation metric: LLM-as-judge faithfulness.
- The **current** pipeline is measured first as the baseline; each new layer must show measured improvement before the next lands. The resulting table is thesis evidence.

**Exit criteria (Week 1):** rebuilt collection from license-clean sources; baseline-vs-hybrid-vs-reranked eval table exists; `DATASET_REGISTRY.md` covers every ingested source.

---

## 3. Section 2 — Module refinements on the new layer (Week 2)

### 3.1 Advisory → frontend (developer-flagged worst module)

- Wire `/advisor` in properly: collapsible "Sources" under each assistant message (source label, excerpt, confidence tier).
- Clean UI state for `no_retrieval_context` instead of an ungrounded answer.
- **Acceptance:** 10-query audit — every answer grounded and cited (claim C5 evidence).

### 3.2 Roadmap provenance (C1/C2 — in-flight)

- First: review and land the developer's uncommitted changes (`Backend/apps/roadmaps/ai_pipeline.py`, `AssessmentResultsPage.tsx`, `RoadmapPage.tsx`).
- Point roadmap structure retrieval at the rebuilt collection with the `source` metadata filter.
- Finish the provenance chain: `structure_source`, retrieved URLs, honest `fallback_used`, Sources panel per phase.
- **Acceptance:** every phase of a demo roadmap shows ≥1 external source link.

### 3.3 Assessment scenario corpus

- Seed the 7 empty role stubs (only `backend.py` has content) following the existing author guide and audit command.
- Scenario content researched via connectors; license-logged like all other sources.
- **Acceptance:** all 8 roles retrieve role-specific scenarios; corpus audit command passes; no silent fallback to generic questions.

### 3.4 Courses (C9)

- Re-enable the disabled URL route.
- Run the existing embedding matcher on the demo roadmap.
- **Acceptance:** ≥2 milestones with linked courses, `match_score > 0`, human-readable `recommendation_reason`.

### 3.5 Error-handling rule (whole section)

Every new path keeps a deterministic fallback. The demo must survive a dead `GEMINI_API_KEY` or missing Chroma volume — the known biggest demo risk.

---

## 4. Section 3 — Jobs upgrade + assessment credibility (Week 3)

### 4.1 Jobs: shrink the ranker's honest weaknesses

Per `EVAL_REPORT.md`, the three weaknesses are: embedding feature disabled, templated fixture postings, pseudo-labels. Fixes in impact order:

1. Expand real ingest to **≥100 Egyptian postings** via existing `ingest_jobs_csv` / `wuzzuf.py`; Nimble for collection if scraping cooperates, curated CSV export if not (risk register already blesses this fallback).
2. Re-enable `skill_embedding_cosine` in the training environment; retrain with `--real-only`.
3. Re-run leave-one-group-out evaluation; regenerate `EVAL_REPORT.md` with a before/after table.
4. **Stretch:** small human-labeled gold set (~50 job–profile pairs, ~1 hour of developer time) to report one metric against human judgment.

### 4.2 Assessment credibility (C3/C4)

- `docs/product/ROLE_GRAPH_METHODOLOGY.md`: dimensions and weights per role; O*NET task-statement crosswalk — Backend Developer in depth (per the predecessor spec's risk decision), plus Frontend and Data Science where mappings are clean (element IDs cited); ≥15 `taxonomy_map.py` entries.
- LLM-rubric scoring path for open-ended answers, `scoring_method` recorded per response (`llm_rubric` | `keyword_coverage`), keyword fallback unchanged.
- Expert review (3 reviewers × 15 items): **developer action item** — Claude prepares the review packet and scoring sheet; the developer recruits reviewers and runs it.

---

## 5. Section 4 — Evaluation, academic package, hardening (Week 4)

### 5.1 Evaluation loop

- Full harness run across the finished system: Recall@K, Precision@K, MRR; LLM-as-judge faithfulness; source-credibility score over all citations.
- Thresholds: faithfulness > 85%, Precision@5 > 70%, credibility > 80%. Failures diagnosed (retrieval vs. generation vs. data gap), fixed, re-measured.
- Output: `EVALUATION_REPORT.md` — baseline vs. final, per-technique contribution table, honest limitations.

### 5.2 Academic package

- `ACADEMIC_SUMMARY.md` — 2-page defense summary.
- `PROFESSOR_FAQ.md` — pre-answered likely questions, grounded in real artifacts.
- `RAG_ARCHITECTURE.md` — pipeline diagram + per-technique academic basis.
- `DATASET_REGISTRY.md` — living since Week 1, finalized here.
- Sync: `CLAIMS_REGISTER.md` statuses flipped with evidence links; `CLAUDE.md` updated; thesis chapters aligned (C10/C11).

### 5.3 Demo hardening

- Full-loop integration test: assessment → roadmap → courses → jobs → advisor.
- Demo rehearsal against a fresh Gemini key per `GRADUATION_DEMO_RUNBOOK.md`.
- Verified offline run on deterministic fallbacks.

---

## 6. Timeline

| Week | Focus | Exit criteria |
|---|---|---|
| 1 | Knowledge layer: corpus acquisition + registry, structure-aware chunking, hybrid + re-rank + citations, eval harness with baseline | Rebuilt collection; measured improvement table; registry complete |
| 2 | Advisory UI integration, roadmap provenance (land in-flight work), scenario corpus ×8 roles, courses route + matching | C5 audit passes; provenance links per phase; corpus audit green; ≥2 milestones with courses |
| 3 | Jobs real-data retrain + re-eval, `ROLE_GRAPH_METHODOLOGY.md`, LLM rubric path, expert-review packet | New `EVAL_REPORT.md` before/after; methodology doc exists |
| 4 | Evaluation loop, academic docs package, claims/thesis sync, demo hardening. **No feature work.** | Thresholds met or honestly documented; full suite green; rehearsed demo |

---

## 7. Testing strategy (throughout, not just Week 4)

| Layer | Tests |
|---|---|
| Regression gate | Full existing suite (274+ tests) stays green after every change — the guard for "don't break what's good" |
| Chunker / fusion / re-rank | Unit tests on committed fixtures; no live network in CI |
| Retrieval | Tests against committed fixture corpora; eval harness runnable as a management command/script |
| API contracts | New fields (citations, provenance, explanations) covered by existing frontend-contract tests |
| Full loop | Existing full-loop test updated for provenance + courses + citations |

---

## 8. Risks

| Risk | Mitigation |
|---|---|
| Connector-acquired content has unusable licenses | Registry-first rule: license checked before ingestion; O*NET-heavy corpus is the floor |
| Wuzzuf blocks collection | Curated CSV export (predecessor spec's accepted fallback) |
| Gemini quota dies during eval or demo | Deterministic fallbacks preserved on every path; fresh key for rehearsal |
| Eval thresholds not met by Week 4 | Honest documentation of shortfall + failure analysis is itself defensible; thresholds are targets, not claims |
| Scenario authoring for 7 roles takes longer than planned | Roles prioritized by demo likelihood; unseeded roles keep graceful fallback and are listed as limitations |
| Week 2 depends on Week 1 completion | Eval harness and corpus work start day 1; module work can begin against the old collection and re-point |

---

## 9. Success criteria (defense-ready)

1. Advisory chat is integrated in the frontend, grounded, and shows per-message sources with confidence — usable in the live demo.
2. All 8 assessment roles retrieve role-specific scenarios.
3. Demo roadmap phases each show an external source link; provenance metadata is honest about fallbacks.
4. Jobs ranking is trained on real postings with the embedding feature enabled, with a before/after evaluation table.
5. Courses appear on demo roadmap milestones with non-zero match scores.
6. `EVALUATION_REPORT.md`, `DATASET_REGISTRY.md`, `RAG_ARCHITECTURE.md`, `ACADEMIC_SUMMARY.md`, `PROFESSOR_FAQ.md` exist and are grounded in real artifacts.
7. Every claim in `CLAIMS_REGISTER.md` is either Done-with-evidence or an explicit limitation.
8. Full test suite green; demo rehearsed online and offline.

---

## 10. Next step

After developer review of this spec: invoke the **writing-plans** skill to produce the ordered, PR-sized implementation plan.
