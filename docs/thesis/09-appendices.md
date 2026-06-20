# Appendices

> **Purpose.** Appendices hold supporting material too detailed for the main body: representative
> source-code excerpts, a user manual, an installation/deployment guide, the test-case catalogue,
> and additional results. They are referenced from the chapters (e.g., "full listing in
> Appendix A"). **Target length: 10–20 pages.** Label them A, B, C, … and list them in the Table
> of Contents.

---

## Appendix A — Source-Code Excerpts

**What to include.** 6–10 short, representative listings (15–40 lines each) that illustrate the
*most interesting* logic, not boilerplate. Caption each as "Listing A.x" and explain it in 2–3
sentences. Recommended excerpts:

- **A.1 — `BaseModel`** (UUID PK + soft delete) — the foundation every model inherits.
- **A.2 — JWT settings** (`SIMPLE_JWT`) — token lifetimes, rotation, blacklist.
- **A.3 — LLM provider routing** (`create_provider`, task→model selection).
- **A.4 — Deterministic weighted scoring** (`_weighted_overall`) — the trust-critical function.
- **A.5 — Scenario retrieval** (`ScenarioRetriever.retrieve_for_blueprint`) — fail-safe few-shot
  retrieval that returns `[]` on error.
- **A.6 — Hybrid retrieval** (`retrieve_context`: dense + BM25 + RRF + rerank + abstention).
- **A.7 — Job-ranker features** (`FEATURE_NAMES` and feature construction).
- **A.8 — Ranker training/eval** (`train_and_evaluate`: LOO-CV, NDCG/MAP).
- **A.9 — Frontend API client** (`tokenStorage`, the `401`→refresh→retry flow).
- **A.10 — Invariant test** (`test_gemini_path_overall_score_is_recomputed_not_llm_reported`).

> Present excerpts with a fixed-width font and line numbers; cite the file path under each
> listing (e.g., `Backend/apps/assessments/ai_pipeline.py`).

---

## Appendix B — User Manual

**What to include.** A task-oriented guide with screenshots for end users. Structure:

1. **Getting started** — creating an account and logging in.
2. **Taking an assessment** — choosing a role, answering Stage 1 and Stage 2, reading results.
3. **Using your roadmap** — activating it, tracking milestones, following courses.
4. **Finding jobs** — searching, reading the match explanation, saving jobs.
5. **Asking the advisor** — how to phrase questions, understanding citations and scope.
6. **Managing your profile and settings** — skills, preferences, notifications.

Each step: a one-sentence instruction + the relevant screenshot (reuse Figures 4.6–4.15).

---

## Appendix C — Installation and Deployment Guide

**What to include.** Reproducible setup instructions for evaluators.

### C.1 Prerequisites

Python 3.13, Node.js 18+, Redis, and (for production) PostgreSQL.

### C.2 Backend

```bash
cd Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # set SECRET_KEY, DB, Redis, GEMINI_API_KEY
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver       # http://localhost:8000
```

API docs: `http://localhost:8000/api/schema/swagger-ui/`.

### C.3 Frontend

```bash
cd Frontend
npm install
cp .env.example .env             # VITE_API_BASE_URL=http://localhost:8000/api/v1
npm run dev                      # http://localhost:8080
```

### C.4 AI assets (vector indexes and ranker)

```bash
cd ai-models
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m src.rag.build_vector_db          # build career_knowledge index
cd ../Backend
python manage.py rebuild_scenario_index    # assessment scenarios
python manage.py rebuild_course_index      # courses
python manage.py train_job_ranker          # train + EVAL_REPORT.md
```

### C.5 Optional local LLM fallback

Install Ollama and pull the fallback model (`gemma4:e2b`); set `AI_PROVIDER=ollama`.

### C.6 Running the test suites

```bash
cd Backend && pytest -q                      # 382 tests
cd Frontend && npm run test:run              # 74 tests
cd ../ai-models && pytest -q                 # 112 tests (5 skipped)
```

---

## Appendix D — Test-Case Catalogue

**What to include.** A structured table of representative test cases (id, area, input,
expected, result). Excerpt:

**Table D.1 — Representative test cases.**

| ID | Area | Input | Expected | Result |
|----|------|-------|----------|--------|
| TC-01 | Auth | Register valid user | 201 + JWT pair | Pass |
| TC-02 | Auth | Login wrong password | 401 | Pass |
| TC-03 | Auth | Access protected route w/o token | 401 | Pass |
| TC-04 | Assessment | Submit Stage 1 | 202; processing status set | Pass |
| TC-05 | Assessment | Overall score source | Equals deterministic weighted, not LLM value | Pass |
| TC-06 | Assessment | Scenario retrieval failure | Returns `[]`; generation still succeeds | Pass |
| TC-07 | Roadmap | Generate w/ empty retrieval | Deterministic template fallback | Pass |
| TC-08 | Jobs | Match for user | Ranked list + match explanation | Pass |
| TC-09 | Jobs | Ranker vs. overlap | LightGBM NDCG@5 ≥ overlap | Pass |
| TC-10 | Advisory | Out-of-scope query | Redirect/clarify, no fabricated answer | Pass |
| TC-11 | Advisory | In-scope query | Grounded answer with citations | Pass |
| TC-12 | Contract | Assessment response shape | Matches SPA TypeScript interface | Pass |

---

## Appendix E — Additional Results

**What to include.** Material that supports Chapter 5 but is too granular for the main text:

- **E.1** — Full per-fold NDCG/MAP table from the ranker's leave-one-group-out CV (8 folds).
- **E.2** — The complete `EVAL_REPORT.md` contents (ranker config, dataset stats, caveats).
- **E.3** — Per-query retrieval metrics for the 55-query evaluation set.
- **E.4** — Sample generated assessment questions for each of the 8 roles (to evidence
  role-awareness and quality).
- **E.5** — A sample advisor transcript showing citations, confidence tiers, and an
  out-of-scope redirect.
- **E.6** — A sample generated roadmap (phases → milestones → courses) with provenance
  (`structure_source = roadmap.sh`, `structure_license_tier = dev_only`).

---

## Appendix F — Data and Licensing Notes

**What to include.** A transparency appendix (strengthens academic integrity):

- **O*NET 30.1** — CC BY 4.0; used for the backend occupational crosswalk PoC; attribution
  provided.
- **roadmap.sh snapshot** — personal-use licence; used as a *development-only* structure source;
  flagged for replacement before public release.
- **`jobs_egypt_tech.csv`** — internal synthetic fixtures (~60 postings) used solely for the
  weak-supervision ranker demonstration; not real labelled market data.
- **Retrieval evaluation set** — 55 internally-authored labelled queries.

> This appendix makes explicit the provenance and licence status of every external dataset,
> aligning the thesis with responsible-data practice.
