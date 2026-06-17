# Claims-to-Reality: Sha8lny Credibility Retrofit

**Date:** 2026-05-30  
**Status:** Draft — awaiting review  
**Timeline:** ~4 weeks to defense/submission  
**Goal:** Align thesis, demo, and codebase so every defended claim is backed by implemented behavior, real data, or an explicit limitation.

---

## 1. Context

Sha8lny has strong engineering (staged assessment, RAG advisory, modular Django backend, React frontend). The credibility gap is **epistemic**: features appear research-grade or market-grounded, but several paths use hardcoded heuristics, seeded fake jobs, or undocumented weights without traceable references.

Professors typically ask:

- *"How do you know this roadmap is accurate — what's your reference?"*
- *"Where is the Egyptian market data?"*
- *"You mention LightGBM — show the model."*
- *"How did you validate assessment scores?"*

This design closes those gaps within **one month**, without fine-tuning LLMs, daily scraping, or psychometric certification.

### Accepted scope boundaries

| Out of scope (honest limitations in thesis) | In scope (must ship) |
|---------------------------------------------|----------------------|
| LoRA/QLoRA fine-tuning of LLaMA/Mistral | Hosted **Gemini** + **Gemma/Ollama** fallback (current runtime) |
| Daily Celery scraping at scale | **One-time** ingest of 50–150 real Egyptian job listings |
| Psychometric certification (IRT, reliability studies) | **Light expert review** (3 reviewers × ~15 items) + retrieval audit |
| Full O\*NET crosswalk for all roles | **Partial crosswalk** for 2–3 primary roles (e.g. backend, frontend, data science) |
| Cloud deployment of custom fine-tuned weights | Commit **LightGBM ranker artifact** (<10 MB) + deterministic fallbacks |

---

## 2. Claims Register (single source of truth)

Every thesis sentence and UI label maps to one status. **Defended claims must be `implemented` or `partial` with documented evidence.**

| ID | Claim | Was | Target v1 | Evidence artifact |
|----|-------|-----|-----------|-------------------|
| C1 | Personalized learning roadmaps | Hardcoded if/elif phases | RAG-retrieved roadmap.sh path → normalized phases → gap reorder → Gemini copy | `metadata.generation.provenance`, UI "Sources" |
| C2 | Roadmap references / accuracy | None | Per-phase/milestone provenance (roadmap.sh URL, O\*NET element where mapped) | API field + thesis appendix |
| C3 | AI skill assessment | Staged flow + curated role graphs | Same engine + documented derivation + optional LLM rubric for open-ended | Methodology doc + expert review table |
| C4 | Role graph weights | Undocumented `curated-v2` | Partial O\*NET task mapping + job-posting sample rationale | `docs/product/ROLE_GRAPH_METHODOLOGY.md` |
| C5 | RAG career advisor | Working Chroma `career_knowledge` | Visible citations in chat UI | Screenshot + 10-query retrieval audit |
| C6 | Egyptian job market | `seed_jobs` fiction | One-time Wuzzuf (or manual CSV) ingest with real URLs | `scraped_at`, `source_url` on Job rows |
| C7 | Job–skill matching | Set overlap % | Embedding similarity + **LightGBM** rerank | `ai-models/models/custom/job_ranker.lgb` |
| C8 | "Why this job?" | `matching_skills` only | Feature contributions + missing skills | API `explanation` object |
| C9 | Course ↔ milestone matching | Model unused | Embedding match populates `RoadmapCourse` | Non-zero `match_score` on demo roadmaps |
| C10 | LLM stack | Thesis: LLaMA/Mistral fine-tunes | Thesis: **Gemini (demo) + Gemma/Ollama (fallback)** | Updated Ch. 2–4 + `AI_MODEL_ONBOARDING_REFERENCE.md` |
| C11 | Evaluation | None | Expert review + retrieval audit + job sanity check | Thesis §3.4 appendix |

**Thesis rule:** Rows not reaching Target v1 are labeled *future work* — never presented as shipped.

---

## 3. Architecture

### 3.1 Data sources (already in repo)

| Source | Location | Used today | Target use |
|--------|----------|------------|------------|
| roadmap.sh | `ai-models/data/roadmap-sh-data/` | Advisory RAG only | **Roadmap structure retrieval** |
| O\*NET 30.1 | `ai-models/data/onet_data/` | Advisory RAG only | Skill labels + milestone metadata |
| Course catalog | `seed_courses` command | Standalone | Milestone course matching |
| Scenario corpus | `Backend/apps/assessments/scenario_corpus/` | Assessment RAG | Unchanged |

Chroma collection `career_knowledge` is built via `ai-models/src/rag/build_vector_db.py`. Roadmap generation will **query the same collection** with `where={"source": "roadmap.sh"}` (pattern exists in `query_with_lmstudio.py`).

### 3.2 Component diagram

```
External: roadmap.sh corpus, O*NET, Wuzzuf listings (one-time)
                    │
                    ▼
ai-models:  Chroma career_knowledge ──► RoadmapPathRetriever (new)
            FeatureEngineering + LightGBM ranker (new)
                    │
                    ▼
Backend:    RoadmapAssembler (new, replaces _create_mvp_structure as primary)
            JobIngestService (new, one-time scrape/CSV)
            JobService.match_jobs_for_user → ranker
            Assessment open-ended rubric (extend engine)
                    │
                    ▼
Frontend:   Roadmap "Sources" panel, Job match explanation, Advisory citations
```

### 3.3 Roadmap assembly pipeline (C1, C2)

**Replaces** `_create_mvp_structure()` as the primary path when Chroma is available. Hardcoded structure remains as **deterministic fallback** (existing behavior).

1. **Resolve role key** — `resolve_role_key(target_career)` (existing).
2. **Retrieve path** — Query Chroma: role label + "learning path roadmap", filter `source=roadmap.sh`, top-k=5 chunks.
3. **Normalize to blueprint** — New `RoadmapPathNormalizer`:
   - Parse headings / ordered topics from retrieved chunks into 3 phases (merge/split heuristics documented).
   - Assign estimated hours from chunk metadata or default table (documented in methodology).
4. **Gap reorder** — Use assessment `priority_skills` / gap profile to bubble relevant milestones earlier (existing extractors in `RoadmapService`).
5. **O\*NET crosswalk (partial)** — Map milestone skill strings to nearest O\*NET skill element ID where confidence > threshold; store in `milestone.resources` or `metadata`.
6. **Gemini personalize** — Existing `RoadmapAIService.personalize_blueprint` (structure locked).
7. **Persist provenance** — `roadmap.metadata.generation.provenance`:
   ```json
   {
     "structure_source": "roadmap.sh",
     "retrieved_doc_ids": ["..."],
     "retrieved_urls": ["https://roadmap.sh/backend"],
     "onet_mappings": [{"milestone_id": "...", "onet_element_id": "..."}],
     "fallback_used": false,
     "assembler_version": "roadmap-assembler-v1"
   }
   ```

**Acceptance:** Demo user can open roadmap and see ≥1 external source link per phase.

### 3.4 Job pipeline (C6, C7, C8)

**Ingest (one-time, not scheduled):**

- New management command: `ingest_jobs_wuzzuf --limit 100` OR `ingest_jobs_csv jobs.csv`.
- Store: real `external_url`, `posted_date`, `scraped_at`, `location_country=Egypt`.
- Skill tagging: existing Gemma structured extraction with **rules fallback** (already in jobs tests).
- Keep `seed_jobs` for local dev but mark `metadata.source=fabricated`; demo uses ingested jobs only.

**Ranking:**

- New `ai-models/src/recommendations/feature_engineering.py`:
  - `skill_embedding_cosine` (SentenceTransformer, same model as RAG)
  - `required_skill_overlap_ratio` (current logic)
  - `experience_level_delta`
  - `job_freshness_days`
  - `location_match` (Egypt = 1.0)
- New `ai-models/src/recommendations/ranker.py`:
  - Train **LightGBM LambdaRank or LGBMRanker** on pseudo-labels: top quartile overlap + has title keyword match = relevant.
  - Save to `ai-models/models/custom/job_ranker.lgb` (committed, <10 MB).
  - Training script: `ai-models/scripts/train_job_ranker.py` (reproducible, documented in thesis).
- New `ai-models/src/recommendations/explainer.py`:
  - Return top-3 feature names + values (not SHAP required for v1 — weighted feature contribution is enough).

**Backend integration:**

- `JobService.match_jobs_for_user` calls ranker when model file present; falls back to overlap sort.
- API adds `explanation: { matching_skills, missing_skills, top_factors: [...] }`.

**Acceptance:** pytest proves ranker loads; demo shows jobs with real Wuzzuf URLs and non-trivial rank order vs pure overlap.

### 3.5 Course–milestone matching (C9)

- After roadmap phases/milestones created, for each milestone:
  - Build query from milestone title + skills.
  - Embed against `Course` catalog (title + skills JSON).
  - Top-3 courses → `RoadmapCourse` with `match_score` (cosine × 100), `recommendation_reason` (template: "Covers {skills}").
- Runs synchronously on roadmap generation completion (Celery task extension) or lazy on first roadmap GET.

**Acceptance:** Graduation demo roadmap has ≥2 milestones with linked courses and scores > 0.

### 3.6 Assessment credibility (C3, C4)

**Without retraining or psychometrics:**

1. **`docs/product/ROLE_GRAPH_METHODOLOGY.md`** — For backend role (minimum):
   - List dimensions and weights.
   - Map 5+ subskills to O\*NET task statements (cite element IDs).
   - Note expert review date and reviewers (can be team supervisors).

2. **Populate `taxonomy_map.py`** — At least 15 entries mapping external labels → `(role_key, subskill_key)`.

3. **Open-ended rubric (optional LLM path)** — When Gemini available:
   - Score 1–5 using rubric prompt with `expected_concepts`.
   - Store `scoring_method: "llm_rubric" | "keyword_coverage"` on response metadata.
   - Fallback unchanged for offline/demo-safe mode.

4. **Expert review (minimal)** — 3 reviewers score 15 open-ended responses (5 per reviewer overlap on 5 items):
   - Report mean absolute error vs engine.
   - Include in thesis appendix (table, not full certification).

### 3.7 Advisory citations (C5)

- `LLMAdvisoryService` already retrieves documents; expose `retrieved_documents` in API response (if not already).
- Frontend: render collapsible "Sources" under each assistant message with source label + excerpt.

### 3.8 Thesis sync (C10, C11)

Update `archive/thesis/docs-thesis/` (or active thesis path):

| Section | Change |
|---------|--------|
| Ch. 2 comparison table | LightGBM ✅, Gemini/Gemma (not LLaMA/Mistral fine-tune), scraping = batch not daily |
| Ch. 3 research design | Add expert review + retrieval audit protocols |
| Ch. 4 implementation | Match `AI_MODEL_ONBOARDING_REFERENCE.md`; cite `job_ranker.lgb`, `RoadmapAssembler` |
| Limitations | No fine-tuning, no psychometric validation, batch job ingest |

---

## 4. Four-week execution plan

### Week 1 — Foundation + roadmaps

| Day | Task | Claims |
|-----|------|--------|
| 1–2 | Claims register in repo; fix thesis comparison table draft | C10 |
| 2–3 | `RoadmapPathRetriever` + `RoadmapPathNormalizer` in Backend (or ai-models imported) | C1 |
| 4–5 | Wire into `RoadmapService` generation task; provenance metadata | C1, C2 |
| 5 | Frontend: roadmap Sources panel | C2 |

**Exit criteria:** New AI roadmap shows roadmap.sh provenance; fallback still works without Chroma.

### Week 2 — Jobs + ranker

| Day | Task | Claims |
|-----|------|--------|
| 1–2 | Job ingest command (Wuzzuf HTML parser or curated CSV export) | C6 |
| 3–4 | `feature_engineering.py`, `train_job_ranker.py`, commit model | C7 |
| 4–5 | Backend integration + explanation payload | C7, C8 |
| 5 | Frontend: job match explanation UI | C8 |

**Exit criteria:** ≥50 real jobs in DB; ranker changes order vs overlap-only; tests pass.

### Week 3 — Courses + assessment docs

| Day | Task | Claims |
|-----|------|--------|
| 1–2 | Course–milestone embedding matcher | C9 |
| 3 | Advisory citations in frontend | C5 |
| 4–5 | `ROLE_GRAPH_METHODOLOGY.md` + partial `taxonomy_map.py` | C4 |
| 5 | Open-ended LLM rubric path (if time); else document keyword method honestly | C3 |

**Exit criteria:** Demo roadmap has courses; advisory shows sources; methodology doc exists.

### Week 4 — Evaluation + thesis + hardening

| Day | Task | Claims |
|-----|------|--------|
| 1–2 | Expert review session + retrieval audit (10 queries) | C11 |
| 2–3 | Thesis chapter updates + screenshots from live demo | C10, C11 |
| 4 | Integration test: assessment → roadmap → jobs full loop | all |
| 5 | Buffer: bug fixes, demo seed script (`seed_graduation_demo` uses real jobs) | — |

**Exit criteria:** Thesis and demo tell identical story; `pytest` green; graduation demo script documented in README.

---

## 5. File touch list (implementation reference)

### New files

| Path | Purpose |
|------|---------|
| `Backend/apps/roadmaps/path_retriever.py` | Chroma query for roadmap.sh |
| `Backend/apps/roadmaps/path_normalizer.py` | Chunks → phase blueprint |
| `Backend/apps/roadmaps/assembler.py` | Orchestrates C1 pipeline |
| `Backend/apps/jobs/ingest/wuzzuf.py` | One-time ingest |
| `Backend/apps/jobs/management/commands/ingest_jobs_wuzzuf.py` | CLI |
| `ai-models/src/recommendations/feature_engineering.py` | Ranker features |
| `ai-models/src/recommendations/ranker.py` | LightGBM inference |
| `ai-models/src/recommendations/explainer.py` | Match explanation |
| `ai-models/scripts/train_job_ranker.py` | Training |
| `ai-models/models/custom/job_ranker.lgb` | Trained artifact |
| `docs/product/ROLE_GRAPH_METHODOLOGY.md` | C4 evidence |
| `docs/product/CLAIMS_REGISTER.md` | Living register from §2 |

### Modified files

| Path | Change |
|------|--------|
| `Backend/apps/roadmaps/services.py` | Call assembler; deprecate primary reliance on `_create_mvp_structure` |
| `Backend/apps/jobs/services.py` | Ranker integration |
| `Backend/apps/assessments/engine.py` | Optional LLM rubric branch |
| `Backend/apps/advisory/llm_service.py` | Ensure citations in response |
| `Frontend/src/features/roadmap/` | Sources panel |
| `Frontend/src/features/jobs/` | Explanation UI |
| `Frontend/src/features/advisory/` | Citations UI |
| `archive/thesis/docs-thesis/Chapter_2*.md` | Align claims |

---

## 6. Testing strategy

| Layer | Tests |
|-------|-------|
| Roadmap assembler | Unit: normalizer with fixture chunks; integration: roadmap POST returns provenance |
| Job ranker | Unit: feature vector shape; model loads; order differs from overlap-only on fixture |
| Ingest | Unit: parser on saved HTML fixture (commit 2–3 pages, no live network in CI) |
| Contracts | Extend `test_frontend_contracts.py` for new API fields |
| Full loop | Existing `test_full_loop.py` updated for provenance + courses |

---

## 7. Risk register

| Risk | Mitigation |
|------|------------|
| Wuzzuf blocks scraping | Manual CSV export of 50 jobs; thesis cites "batch collection" |
| Chroma not built in demo env | Document `build_vector_db` in demo setup; fallback to hardcoded + flag `fallback_used: true` |
| 4 weeks too tight | Drop LLM rubric (C3 partial); keep keyword + expert review |
| LightGBM overfits pseudo-labels | Document as learning-to-rank v1; show ablation vs overlap in appendix |
| O\*NET mapping incomplete | Scope to 1 role in depth vs 3 roles shallow — pick 1 role (backend) |

---

## 8. Success criteria (defense-ready)

1. Professor can click a roadmap milestone and see an external reference (roadmap.sh or O\*NET).
2. Job list includes real URLs from Egyptian market; match explanation cites skills and ranker factors.
3. LightGBM model file exists in repo; training script is reproducible.
4. Advisory chat shows retrieved sources.
5. Thesis comparison table matches live demo behavior.
6. Limitations section explicitly excludes fine-tuning, daily scrape, psychometrics.
7. Appendix contains expert review summary and retrieval audit table.

---

## 9. Self-review (spec quality check)

- [x] No TBD placeholders in scope or acceptance criteria
- [x] Architecture matches file layout and existing patterns (GemmaClient, Chroma, Celery tasks)
- [x] Scope fits ~4 weeks with explicit descopes
- [x] No contradiction: Gemini/Gemma accepted; fine-tuning out of scope
- [x] Claims register covers original professor questions (roadmap reference, jobs, ranker, validation)

---

## 10. Next step

After approval: invoke **writing-plans** skill to produce task-level `plan.md` with ordered PR-sized chunks for implementation.
