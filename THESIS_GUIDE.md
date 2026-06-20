# Sha8lny — Thesis Writing Guide & Blueprint

**Purpose.** This is a single, self-contained reference for writing the **full graduation
thesis** for the Sha8lny project. It captures (a) the **current, verified state** of the
system, (b) a **chapter-by-chapter writing plan** with the facts, tables, diagrams, and
citations you can lift directly, and (c) a clearly separated **"planned but not yet
implemented"** section so a teammate can start building the remaining work *in parallel*
while the thesis is being written.

> **How to use this file**
> - **Thesis writer:** Work top-to-bottom through Part 1 (chapter plan). Every claim is
>   tied to a file or a number in the repo (Part 4 is the evidence index) — never write a
>   claim you can't point to.
> - **Teammate starting parallel work:** Jump to **Part 3 (Future Work)**. Each item says
>   *where* in the repo it lives, *what's missing*, and *acceptance criteria*. Read the
>   "Coordination note" first so you don't collide with in-flight work.
> - **Everything here is traceable.** Numbers come from committed artifacts and the live
>   test suites; verify by re-running the commands in Part 4 before final submission.

**Document status:** Reflects the repo as of branch
`defensibility/weighted-score-and-ranker-eval`. Backend suite: **382 tests passing**.
AI-layer suite: **112 tests passing**, 5 skipped (both run on deterministic fallbacks, no API key).

---

## Part 0 — Project Cheat Sheet (memorize this)

| Field | Value |
|---|---|
| **Product name** | Sha8lny (also spelled Sha8alny) |
| **One-liner** | An AI-powered career-empowerment platform for the **Egyptian** job market. |
| **Core user journey** | Assessment → Learning Roadmap → Progress Tracking → Job Matching → AI Career Advisor |
| **Architecture** | Full-stack **modular monolith** (single deployable, module boundaries) |
| **Backend** | Django + Django REST Framework, JWT auth (+ Auth0), PostgreSQL (prod) / SQLite (dev) |
| **Frontend** | React 18 + TypeScript + Vite, shadcn/ui + Tailwind, React Query, React Router v6 |
| **AI layer** | RAG pipeline (ChromaDB + sentence-transformers + BM25 + cross-encoder) + LightGBM job ranker |
| **LLM runtime** | Hosted **Google Gemini** (default) via a single `GemmaClient` gateway; local **Gemma/Ollama** fallback; **deterministic fallback on every AI path** |
| **No-LLM-by-design** | Workflow routing, roadmap structure/ordering, course matching, scoring roll-up, progress — all deterministic |
| **Tests** | **382** backend + **74** frontend + **112** AI-layer (5 skipped), all passing on offline fallbacks |
| **Headline result** | Advisory retrieval Recall@5 improved **~5×** (0.118 → 0.609) and MRR **~5×** (0.109 → 0.544) over a measured baseline; corpus cleaned from 358,992 → ~64,000 docs |
| **Defining quality** | "Not an API wrapper" — a **measured, staged** retrieval pipeline with abstention; correctness is *measured, not asserted* |

**The thesis's central argument (your thesis statement):**
> *A career-guidance platform built on a Large Language Model becomes trustworthy not by
> better prompting but by a measured retrieval layer beneath it — license-clean data,
> hybrid search, re-ranking, citation, and honest abstention — whose contribution to
> answer quality is empirically attributable, technique by technique.*

---

## Part 1 — Chapter-by-Chapter Thesis Plan

A standard CS graduation thesis structure, mapped to this project. For each chapter:
**what to write**, **evidence/source in repo**, and **figures/tables to include**.

### Chapter 1 — Introduction
**Write:**
- **Problem.** Career resources for Egyptian students/job-seekers are fragmented (separate
  sites for assessment, courses, roadmaps, jobs). Generic AI advisors hallucinate and are
  not grounded in the Egyptian market (salaries in EGP, ITIDA/DEPI government programs).
- **Motivation.** Scale personalized guidance without human counselors; ground it in
  credible, local data.
- **Objectives** (lift from SRS §1.2): personalized assessment, roadmap generation, RAG
  advisory, job-market intelligence.
- **Scope & boundaries** (SRS §1.2): MVP = assessment + roadmap + advisory + Egypt job
  data. **Out of scope:** proprietary courses, native mobile app, direct job-application
  processing.
- **Contributions** (this is what makes it defensible — state them explicitly):
  1. A full-stack, end-to-end career platform on a modular-monolith architecture.
  2. A **measured RAG pipeline** with a reproducible evaluation harness (the novelty).
  3. A **license-clean, Egypt-grounded knowledge corpus** with documented provenance.
  4. An **abstention mechanism** that makes the advisor decline rather than fabricate.
  5. A **weak-supervision job ranker** with leave-one-group-out evaluation against baselines.
  6. **Honest evaluation** — every limitation documented, not hidden.
- **Thesis organization** (one paragraph summarizing the remaining chapters).

**Source:** `docs/product/SRS.md` §1, `docs/product/PROJECT_STATUS_FOR_REVIEW.md` §1–2.

### Chapter 2 — Background & Literature Review
**Write the conceptual foundation and cite prior work** (see Part 5 for the reference list):
- **Large Language Models** and their failure mode for factual tasks (hallucination).
- **Retrieval-Augmented Generation (RAG)** — Lewis et al. 2020. Why grounding beats
  fine-tuning for a $0-budget, fast-moving knowledge domain.
- **Information retrieval techniques you actually used:**
  - **BM25 / probabilistic relevance** (Robertson & Zaragoza 2009) — keyword search.
  - **Dense / semantic embeddings** (Sentence-BERT, Reimers & Gurevych 2019).
  - **Reciprocal Rank Fusion** (Cormack et al., SIGIR 2009) — merging keyword + dense.
  - **Cross-encoder re-ranking** (Nogueira & Cho 2019) — joint query-passage scoring.
- **Learning-to-rank / gradient boosting** — LightGBM (Ke et al. 2017); ranking metrics
  **NDCG** (Järvelin & Kekäläinen 2002) and MAP.
- **Parameter-efficient fine-tuning** (LoRA, Hu et al. 2021; QLoRA, Dettmers et al. 2023) —
  explain why it was *evaluated and consciously deferred* in favor of hosted Gemini
  (budget/hardware; see ADR-002).
- **Career-taxonomy data sources** — O\*NET (US Dept. of Labor), BLS Occupational Outlook
  Handbook, and Egyptian government ICT sources (ITIDA/MCIT).
- **Related platforms / gap analysis** — generic chatbots, roadmap.sh (structure-only,
  personal-use license), Wuzzuf (jobs only). None combine grounded advisory + Egypt data +
  measured retrieval.

**Source:** Part 5 of this guide; `docs/product/RAG_RETRIEVAL_EVAL.md`;
`docs/product/DATASET_REGISTRY.md`; `ai-models/CLAUDE.md` (model specs & rationale).

### Chapter 3 — Requirements Analysis
**Write:** Restructure the SRS into thesis prose.
- **Functional requirements** FR-1…FR-24, grouped by service (User, Assessment, Roadmap,
  Advisory, Jobs, Analytics) — `docs/product/SRS.md` §3.1.
- **Non-functional requirements:** performance targets (non-AI ≤2s, AI ≤7s avg),
  reliability, security (JWT, HTTPS, no password storage), maintainability, portability —
  SRS §3.3–3.6.
- **User characteristics:** Students, Job Seekers, Professionals — SRS §2.3.
- **Constraints & assumptions** — SRS §2.4–2.5.

> ⚠️ **Accuracy note for the writer:** The SRS has an *aspirational* framing in places
> (it says "microservices," "Pinecone," "300+ concurrent users," "WebSockets,"
> "daily scraping"). The **implemented** system is a **modular monolith** using
> **ChromaDB** (not Pinecone), **Gemini/Gemma** (not OpenAI/Anthropic), with a
> **one-time job batch** (not daily scraping). The SRS already carries an
> "Implementation note (May 2026)" banner acknowledging this — **write the requirements
> as specified, but describe the as-built system in Ch. 4–5 and reconcile the difference
> honestly** (this is itself good thesis material: requirements evolution).

**Figures to include:** API endpoint summary table (SRS Appendix B), domain model (SRS
Appendix A).

### Chapter 4 — System Architecture & Design
**Write:**
- **Architecture philosophy:** why a **modular monolith** (rapid dev, ACID transactions
  across modules, direct Python calls instead of HTTP, single-server cost, future
  extraction path). Source: `docs/product/ARCHITECTURE.md` §"Architecture Philosophy."
- **The 10 modules** (Django apps) and responsibilities: `core`, `users`, `assessments`,
  `roadmaps`, `courses`, `jobs`, `advisory`, `progress`, `career_tools`, `notifications`.
- **Core patterns:**
  - `BaseModel` — UUID PKs, `created_at`/`updated_at`, **soft delete** (`is_deleted`,
    `deleted_at`), dual managers (`objects` vs `all_objects`).
  - **Service layer** (business logic out of views) and **selector layer** (query
    optimization).
  - **Cross-module ACID transactions** (`@transaction.atomic`) — the monolith's advantage.
  - **JSONField** for flexible nested data (questions, skill_scores, recommendations).
- **Data layer:** single shared PostgreSQL/SQLite DB + ChromaDB vector store (2 main
  collections: `courses`, `career_knowledge`, plus an assessment scenario collection) +
  Redis (cache/broker, configured).
- **AI inference gateway:** all LLM calls funnel through `GemmaClient`
  (`Backend/apps/core/gemma_client.py`); config in `Backend/apps/core/ai_settings.py`.
- **Background processing:** Celery queue `ai` (eager in dev).

**Figures to include (build these — they are thesis-grade):**
1. **High-level layered architecture diagram** — adapt the ASCII diagram in
   `docs/product/ARCHITECTURE.md` (Frontend → DRF API → Modules → Data/Cache → Celery →
   External). **Redraw it to match reality** (ChromaDB not Pinecone; Gemini not OpenAI).
2. **ERD** — already rendered at `docs/product/ERD.svg` / `ERD.jpg`; schema text in
   `docs/product/DATABASE_SCHEMA.md`.
3. **Module dependency / data-flow diagram** — assessment→roadmap→advisory cross-calls.

### Chapter 5 — Implementation (per module)
For each module, write: capability, key models, key endpoints, and the deterministic vs.
LLM split. Model definitions: `Backend/apps/<module>/models.py` (sizes for scale sense:
jobs 766 LOC, roadmaps 761, courses 535, progress 518, users 509, assessments 422).

- **Users / Auth** — JWT + Auth0, custom `User` (email as `USERNAME_FIELD`, `auth0_id`,
  age validation), skills CRUD, demo seeder. *Strongest, well-tested.*
- **Assessments** — staged AI question generation for **8 roles**; role-graph taxonomy
  (curated-v3); **weighted, deterministic** overall scoring (per-dimension
  `assessment_weight`/`weight` roll-up — the LLM's self-reported score is **not trusted**);
  coverage enforcement; default-on scenario RAG few-shot augmentation that safely
  returns no retrieved examples when no approved scenario matches. Positioned as a
  **formative** assessment, *not* a psychometrically validated instrument.
  Files: `apps/assessments/ai_pipeline.py`, `engine.py`, `scenario_corpus/`.
- **Roadmaps** — AI generation from assessment with a **deterministic, assessment-aware
  fallback** (structure retrieved from roadmap.sh, used as *dev-only fallback*, never cited
  as a source). Per-phase provenance (`structure_source`, `retrieved_urls`,
  `onet_mappings`, honest `fallback_used`). **O\*NET crosswalk = backend-role-only PoC**
  (10 keyword mappings in `apps/roadmaps/onet_mapper.py`). Course embedding matching.
- **Jobs** — search, skill matching, **LightGBM ranker** (weak-supervision demonstrator)
  with LOGO eval, Wuzzuf/CSV ingest, experience-level resolution, "Why this job?"
  explainability (`top_factors`). Files: `apps/jobs/`, `ai-models/src/recommendations/`.
- **Advisory** — Gemini chat grounded in user context + career-knowledge RAG, with
  **per-message citations and confidence tiers** and a distinct **no-context** state.
- **Progress / Notifications / Career Tools / Courses** — partial (see Part 3).

**Frontend (Ch. 5 sub-section):** feature-first structure; thin lazy-loaded route
entrypoints; typed API client with token refresh (`Frontend/src/lib/api.ts`); "career
atlas" design system. Implemented pages: login, register, dashboard, profile, settings,
assessment (select → session → results), roadmap, jobs (search/detail/saved), advisory,
notifications. (See route list in `Frontend/src/features/*/routes/`.)

### Chapter 6 — The AI / RAG Pipeline (the novelty chapter — give it the most space)
This is the chapter that answers *"how is this more than calling an API?"* and *"how do
you know it's correct?"* Structure it as the project itself was built: **measurement first.**

**6.1 The problem, measured (the control group).**
Before any change, the team measured the existing advisor:
- Collection held **358,992 documents**, ~85% near-identical O\*NET numeric rows (a bug).
- **44 / 55** realistic questions returned **zero** documents.
- **Recall@5 = 0.118, MRR = 0.109.**
Source: `docs/product/PROJECT_STATUS_FOR_REVIEW.md` §2; `ai-models/eval_results/retrieval/baseline.json`.

**6.2 The rebuilt pipeline (each technique with an academic basis):**
1. **License-clean corpus** — O\*NET 30.1, BLS OOH, MDN, ITIDA/MCIT (Egypt gov), Stack
   Overflow Survey 2025, curated KB. roadmap.sh is **dev-fallback only** (personal-use
   license). Provenance + license recorded *before* ingestion in `DATASET_REGISTRY.md`.
2. **Validation layer** (`ai-models/src/rag/corpus_validation.py`) — enforces provenance
   header, min length, heading structure; rejects raw HTML / control chars; de-dupes.
   *(It caught its own first regression — rejected 12 MDN files on a header mismatch.)*
3. **Structure-aware chunking** — split on headings, not fixed 500 chars.
4. **Hybrid search** — dense (semantic) + **BM25** keyword, merged via **Reciprocal Rank
   Fusion** (Cormack et al. 2009). `ai-models/src/rag/hybrid_search.py`.
5. **Cross-encoder re-ranking** — `cross-encoder/ms-marco-MiniLM-L-6-v2` re-reads top-20
   jointly with the query (Nogueira & Cho 2019). `ai-models/src/rag/reranker.py`.
6. **Citations + confidence tiering** — every passage returns source, URL, and HIGH/
   MEDIUM/LOW confidence.
7. **Source-diversity selection** — caps passages per section.
8. **Abstention floor** — if best evidence is too weak, return **nothing**; the advisor
   says it can't answer rather than fabricating.

**6.3 Embedding & model choices:** `all-MiniLM-L6-v2` (384-dim, 22M params, CPU,
~3000 sentences/s) — justify the choice for a $0/CPU constraint.

**Figure:** the full pipeline diagram (ingestion → validation → chunking → embedding →
hybrid retrieval → RRF → rerank → diversity → abstention → citation → generation). The
plan calls this `RAG_ARCHITECTURE.md` with a Mermaid diagram — build it if not present.

### Chapter 7 — Evaluation & Results
**This is where the thesis earns its grade. Use the committed numbers verbatim.**

**7.1 Retrieval evaluation (staged, attributable).** Reproducible via
`ai-models/scripts/run_retrieval_eval.py` over a **55-question** ground-truth set; every
stage's JSON is committed under `ai-models/eval_results/retrieval/`.

| Stage | Recall@5 | Recall@10 | Precision@5 | MRR | No-answer |
|---|---|---|---|---|---|
| Baseline (original system) | 0.118 | 0.118 | 0.055 | 0.109 | 44 / 55 |
| + Clean corpus & chunking | 0.209 | 0.209 | 0.062 | 0.161 | 43 / 55 |
| + Hybrid search (BM25+dense) | 0.536 | 0.673 | 0.175 | 0.396 | 17 / 55 |
| + Cross-encoder re-ranking | 0.627 | 0.682 | 0.226 | 0.553 | 16 / 55 |
| + Egypt sources, validation, diversity | 0.609 | 0.664 | 0.218 | 0.544 | 17 / 55 |
| + Abstention floor | 0.609 | 0.664 | 0.218 | 0.544 | 17 / 55 |

**Headline:** Recall@5 **~5×**, MRR **~5×** vs. baseline. The last two rows are honest
trade-offs: diversity costs a little recall for less redundancy; abstention is **zero-cost**
to legitimate questions while preventing fabrication on off-topic ones.

**7.2 Adversarial stress test** (18 queries, `scripts/stress_test_retrieval.py`):
excellent on Egyptian gov programs and exact-term lookups; correctly refuses off-topic
("headache medication," "visa"); good on paraphrase; **fails on Arabic/code-switched** (a
documented limitation). Latency ~0.7s median after index warm-up.

**7.3 Job ranker evaluation** (`ai-models/models/custom/EVAL_REPORT.md`):
leave-one-group-out CV, 60 jobs, 8 synthetic profiles, **weak-supervision pseudo-labels**.

| Metric | LightGBM | Overlap baseline | Random baseline |
|---|---|---|---|
| NDCG@5 | 0.5895 | 0.5603 | 0.1597 |
| NDCG@10 | 0.5755 | 0.5601 | 0.2118 |
| MAP | 0.3750 | 0.3750 | 0.1589 |

LightGBM NDCG@5 lift over overlap baseline: **+0.0292**. **Be honest:** the
`skill_embedding_cosine` feature was disabled in this run (sentence-transformers
unavailable in the training env), so the lift is a **lower bound**, and labels are
heuristic, not human.

**7.4 Software testing.** **382 backend** + **74 frontend** + **112 AI-layer** automated tests, all passing
on deterministic fallbacks (no network/API key). Describe the test strategy: unit +
API/integration + frontend-contract tests + a full-loop test.

**7.5 What this demonstrates academically** (lift `PROJECT_STATUS_FOR_REVIEW.md` §7):
not an API wrapper; correctness measured not asserted; data credible & traceable; the
system knows what it doesn't know.

### Chapter 8 — Limitations & Future Work
Pull directly from **Part 3** of this guide and from
`docs/product/CLAIMS_REGISTER.md` "Limitations." Honest limitations are a strength — list
them: Arabic unsupported, single-annotator eval set, synthetic ranker labels, no
psychometric validation, O\*NET depth limited to Backend Developer, one-time job batch, no
fine-tuning.

### Chapter 9 — Conclusion
Restate the thesis statement and the six contributions; summarize the measured results;
end with the strongest forward item (Arabic/multilingual support for the Egyptian market).

### References & Appendices
- **References:** Part 5 below.
- **Appendix A:** API endpoint catalog (SRS Appendix B).
- **Appendix B:** Full retrieval eval tables + stress transcripts (`RAG_RETRIEVAL_EVAL.md`).
- **Appendix C:** Dataset registry with licenses (`DATASET_REGISTRY.md`).
- **Appendix D:** Claims register (`CLAIMS_REGISTER.md`).
- **Appendix E:** ERD (`ERD.svg`), database schema (`DATABASE_SCHEMA.md`).
- **Appendix F:** Demo runbook (`GRADUATION_DEMO_RUNBOOK.md`).

---

## Part 2 — Reference Material to Lift Directly

### 2.1 Technology stack (as-built)
| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, shadcn/ui + TailwindCSS, React Router v6, React Query |
| Backend | Django + Django REST Framework (modular monolith), SimpleJWT, Auth0 |
| Database | PostgreSQL (prod) / SQLite (dev); JSONField for flexible data |
| Vector store | ChromaDB (local, persistent) — collections: `courses`, `career_knowledge`, scenario corpus |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (384-dim) |
| Keyword search | `rank-bm25` |
| Re-ranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Job ranker | LightGBM (gradient-boosted ranker) |
| LLM | Google Gemini (default) via `GemmaClient`; Gemma/Ollama fallback |
| Async | Celery + Redis (queue `ai`) |
| Testing | pytest / pytest-django (backend), Vitest (frontend) |

> **Citing the stack honestly:** `docs/product/TECH_STACK.md` and
> `docs/product/ARCHITECTURE.md` still contain the *original* OpenAI/Anthropic/LangChain/
> Pinecone/microservices plan, each with a dated banner saying "never implemented." Cite
> the **as-built** column above; mention the pivot (ADR-001 → ADR-002) as design evolution.

### 2.2 Knowledge corpus sources & licenses (for the data-credibility section)
| Source | Provides | License basis | Tier |
|---|---|---|---|
| O\*NET 30.1 | Occupation tasks & titles | CC BY 4.0 | Official |
| BLS Occupational Outlook Handbook | Job descriptions & outlook | US public domain | Official |
| MDN Web Docs | Web/technical concepts | CC-BY-SA, attributed | Established |
| ITIDA / MCIT (Egypt gov) | Egyptian ICT market, salaries, free training (DEPI, DEBI, Train to Hire, ITIDA Gigs) | Official, excerpt-and-cite | Official |
| Stack Overflow Developer Survey 2025 | Tech adoption trends | ODbL, attributed | Established |
| Curated knowledge base | Egypt-specific career prose | Internal | Curated |
| roadmap.sh | Learning-path structure | Personal-use only | **Dev-fallback only — never cited** |

Full detail: `docs/product/DATASET_REGISTRY.md`. Each Egypt fact carries an inline citation.

### 2.3 The 8 assessment roles
Backend Developer, Frontend, Full-stack, Data Science, Machine Learning Engineer, DevOps,
Android, UI/UX Designer. Scenario-corpus authoring lives under
`Backend/apps/assessments/scenario_corpus/<role>.py`; taxonomy in `role_graph_taxonomy.py`
(curated-v3). Rebuild index: `manage.py rebuild_scenario_index`; audit:
`manage.py scenario_corpus_audit`.

### 2.4 Key commands (put in the appendix / reproducibility section)
```bash
# Backend tests (offline, deterministic)        → 382 passing
cd Backend && env -u GEMINI_API_KEY ./venv/bin/python -m pytest -q

# Frontend tests                                 → 74 passing
cd Frontend && npm run test:run

# AI-layer tests                                 → 112 passing, 5 skipped
cd ai-models && ../Backend/venv/bin/python -m pytest -q

# Retrieval evaluation (produces Ch.7 table)
cd ai-models && ../Backend/venv/bin/python scripts/run_retrieval_eval.py --stage <stage>

# Adversarial stress test
cd ai-models && ../Backend/venv/bin/python scripts/stress_test_retrieval.py

# Seed the graduation demo
cd Backend && python manage.py seed_graduation_demo --reset
```

---

## Part 3 — Planned-but-Not-Yet-Implemented (Parallel Work for the Teammate)

> **Coordination note — READ FIRST.** The main developer is actively working the
> "defensibility / quality-refinement" track (RAG eval, weighted scoring, ranker eval).
> Before claiming an item below, **check `docs/product/CLAIMS_REGISTER.md` and run the
> tests** — some Week-3/Week-4 items may already be in progress. The items are grouped by
> **collision risk** so you can pick safe, independent tracks first. The full task-level
> spec for the in-flight work is `IMPLEMENTATION_PLAN.md` (Weeks 1–4).

### 3.A — Safe independent tracks (start here, low collision risk)

**A1. Arabic & code-switched query support** *(highest-value gap — flagship future work)*
- **Why:** This is an Egyptian platform; the corpus and embedding model are English-only.
  Arabic / code-switched queries currently **fail** (documented in stress test).
- **What to build:** swap to a **multilingual embedding model** (e.g.
  `paraphrase-multilingual-MiniLM-L12-v2` or a comparable HF model); add Arabic career
  content to the corpus with provenance entries; add Arabic queries to the eval set.
- **Where:** `ai-models/src/rag/embeddings.py`, `build_vector_db.py`,
  `data/knowledge_base/`, `data/eval/retrieval_eval_set.jsonl`.
- **Acceptance:** Arabic queries in the eval set retrieve relevant docs; re-run
  `run_retrieval_eval.py` and record an Arabic-stage row; existing English metrics don't
  regress.

**A2. Deployment / DevOps** *(entirely separate from app code — ideal parallel track)*
- **What:** Dockerfile + docker-compose (Django + Postgres + Redis + Chroma volume);
  GitHub Actions CI running both test suites; Gunicorn + Nginx config; environment/secrets
  handling; deploy target (Hostinger VPS / Render / Railway per TECH_STACK §Hosting).
- **Where:** repo root (`Dockerfile`, `docker-compose.yml`, `.github/workflows/`),
  `Backend/config/settings/production.py`.
- **Acceptance:** `docker compose up` brings up the stack; CI is green on push; a
  documented one-command deploy.

**A3. Notifications delivery**
- **State:** models, API, and signals exist; **email/push sending is stubbed.**
- **What:** implement an email backend (SendGrid free tier or Django SMTP per TECH_STACK)
  wired to the existing signals; mark notifications sent.
- **Where:** `Backend/apps/notifications/` (models/API/signals present).
- **Acceptance:** triggering a notification sends a real email in dev; tests cover the
  send path with a mocked backend.

**A4. Career Tools PDF/DOCX export (v2)**
- **State:** CRUD works; generate/ATS endpoints return **structured JSON, not a file.**
- **What:** ReportLab (PDF) / python-docx (DOCX) export for resume/portfolio.
- **Where:** `Backend/apps/career_tools/`.
- **Acceptance:** export endpoint returns a downloadable file; test asserts a non-empty
  PDF/DOCX byte stream.

**A5. Frontend React error boundaries**
- **State:** none; flagged as a known gap.
- **What:** add route-level error boundaries with friendly fallback UI.
- **Where:** `Frontend/src/app/` (an error-boundary provider already referenced).
- **Acceptance:** a thrown render error shows the fallback, not a white screen; a test
  covers it.

### 3.B — Coordinate before starting (overlaps the active defensibility track)

**B1. Real Egyptian job data + ranker retrain** *(Week-3 plan — may be in progress)*
- **What:** ingest ≥100 real Wuzzuf/Bayt postings (license/ToS logged first); **enable the
  `skill_embedding_cosine` feature** (currently disabled — root cause was
  sentence-transformers missing in the training env); retrain the LightGBM model; re-run
  LOGO eval and update `EVAL_REPORT.md` with a before/after table.
- **Where:** `Backend/apps/jobs/ingest/`, `ai-models/src/recommendations/`,
  `ai-models/scripts/train_job_ranker.py`, `manage.py export_jobs_for_ranker --real-only`.
- **Acceptance:** ≥100 real postings with `external_url`/`scraped_at`; non-zero embedding
  feature across pairs; updated eval report.

**B2. Human-labeled gold set for the ranker** *(stretch)*
- **What:** ~50 job–profile pairs labeled by hand; `eval_ranker_gold.py` computes NDCG@5
  vs. human labels (replaces weak-supervision-only evaluation).
- **Where:** `ai-models/data/eval/job_gold_set_template.csv`, `scripts/eval_ranker_gold.py`.
- **Acceptance:** the script prints NDCG against a committed sample fixture. *(Labeling is
  a human task.)*

**B3. LLM rubric scoring for open-ended assessment answers**
- **What:** when Gemini is available, score open-ended answers 1–5 against a rubric with
  `expected_concepts`; record `scoring_method` (`llm_rubric` | `keyword_coverage`); keyword
  fallback stays automatic on API failure.
- **Where:** `Backend/apps/assessments/engine.py`, `services.py`.
- **Acceptance:** tests for both paths + fallback-on-exception (mocked Gemini).

**B4. Multi-rater expert review of the assessment** *(human-coordination task)*
- **What:** recruit 3 reviewers, run the review session, ingest results — turns the
  single-annotator eval into a credible multi-rater one. A self-contained packet
  (`EXPERT_REVIEW_PACKET.md` + scoring CSV) is the enabler.
- **Acceptance:** completed scoring sheets; inter-rater agreement reported in the thesis.

**B5. Course ↔ milestone matching populated on demo roadmaps**
- **What:** invoke the existing embedding matcher after roadmap generation so demo
  roadmaps get `RoadmapCourse` rows with `match_score > 0` on ≥2 milestones.
- **Where:** `Backend/apps/roadmaps/services.py` / `tasks.py`.
- **Acceptance:** a test generates a roadmap and asserts populated `RoadmapCourse` rows.

**B6. O\*NET crosswalk depth beyond Backend Developer**
- **What:** extend `apps/roadmaps/onet_mapper.py` (currently 10 keyword mappings, backend
  role only) to Frontend and Data Science with cited O\*NET element IDs; document in
  `ROLE_GRAPH_METHODOLOGY.md`.
- **Acceptance:** ≥3 roles return O\*NET links; methodology doc cites concrete element IDs.

**B7. Faithfulness + credibility evaluation (Week-4 academic package)**
- **What:** LLM-as-judge faithfulness scorer (does each advisory answer follow from its
  retrieved passages?) + deterministic credibility scorer (fraction of cited sources that
  are official/established). Then a full evaluation loop against thresholds
  (faithfulness > 85%, Precision@5 > 70%, credibility > 80%).
- **Where:** `ai-models/scripts/eval_faithfulness.py`, `ai-models/src/rag/credibility.py`.
- **Acceptance:** deterministic credibility tests green; faithfulness runs on a sample with
  a mocked judge; thresholds met or an honest written miss.

### 3.C — Explicit non-goals / hard limitations (state, don't build)
These are **deliberate** limitations to *document in Ch. 8*, not gaps to fill before
submission:
- **No LLM fine-tuning** — hardware/cost; hosted Gemini + local Gemma fallback (ADR-002).
- **No daily job scraping** — a one-time batch snapshot with `scraped_at`.
- **No psychometric validation** of assessment scores — it is **formative**, not a
  validated instrument.
- **Single-annotator** retrieval eval set (55 questions) — directionally strong, not a
  multi-rater gold standard (B4 would upgrade this).
- **Real-time WebSockets / 300+ concurrency** — Channels configured but not used; targets
  are aspirational SRS numbers, not measured.
- **roadmap.sh content** is personal-use-licensed → dev-only fallback, never redistributed
  or cited (see `ai-models/data/CITATIONS.md`).

---

## Part 4 — Evidence Index (file → what it proves)

| Evidence file | Use it for |
|---|---|
| `docs/product/PROJECT_STATUS_FOR_REVIEW.md` | Ch.1, Ch.6, Ch.7 — the measured story, baseline→final, "what this demonstrates" |
| `docs/product/SRS.md` | Ch.3 — functional/non-functional requirements, API catalog, glossary |
| `docs/product/ARCHITECTURE.md` | Ch.4 — modular monolith, module breakdown, patterns, diagrams (redraw to as-built) |
| `docs/product/TECH_STACK.md` | Ch.2/Ch.4 — stack + decision rationale (cite as-built column) |
| `docs/product/DATABASE_SCHEMA.md` + `ERD.svg`/`ERD.jpg` | Ch.4 — ERD, schema |
| `docs/product/RAG_RETRIEVAL_EVAL.md` | Ch.6/Ch.7 + Appendix — full eval tables, stress findings |
| `ai-models/eval_results/retrieval/*.json` | Ch.7 — raw, committed metric artifacts (every number traces here) |
| `ai-models/models/custom/EVAL_REPORT.md` | Ch.7 — job ranker LOGO results & honest limitations |
| `docs/product/DATASET_REGISTRY.md` | Ch.2/Ch.6 — every source's license & USE/REJECT decision |
| `docs/product/CLAIMS_REGISTER.md` | Ch.8 + status tracking — claim-by-claim done/limitation |
| `docs/product/JOB_RANKER_METHODOLOGY.md` | Ch.6 — ranker features & method |
| `docs/product/GRADUATION_DEMO_RUNBOOK.md` | Appendix — reproducible demo (online + offline) |
| `ai-models/CLAUDE.md` | Ch.2/Ch.5 — model specs, rationale, $0-budget constraints |
| `IMPLEMENTATION_PLAN.md` | Part 3 — task-level spec for in-flight & remaining work |
| `Backend/apps/*/models.py` | Ch.5 — exact data models per module |
| `Frontend/src/features/*/routes/` | Ch.5 — implemented UI pages |

**Reproducibility rule for the writer:** every figure/number in Ch.7 must trace to a
committed artifact above. Re-run the Part 2.4 commands before final submission and confirm
the numbers still match (382 / 74 / 112 tests; the retrieval table).

---

## Part 5 — Suggested Reference List (BibTeX-ready topics)

Core method papers (cite these where the technique is introduced in Ch.2/Ch.6):
1. **Lewis et al. (2020)** — *Retrieval-Augmented Generation for Knowledge-Intensive NLP
   Tasks.* NeurIPS. (RAG foundation.)
2. **Cormack, Clarke & Büttcher (2009)** — *Reciprocal Rank Fusion Outperforms Condorcet
   and Individual Rank Learning Methods.* SIGIR. (Hybrid fusion.)
3. **Nogueira & Cho (2019)** — *Passage Re-ranking with BERT.* arXiv:1901.04085.
   (Cross-encoder re-ranking.)
4. **Reimers & Gurevych (2019)** — *Sentence-BERT: Sentence Embeddings using Siamese
   BERT-Networks.* EMNLP. (Dense embeddings.)
5. **Robertson & Zaragoza (2009)** — *The Probabilistic Relevance Framework: BM25 and
   Beyond.* Foundations and Trends in IR. (Keyword search.)
6. **Ke et al. (2017)** — *LightGBM: A Highly Efficient Gradient Boosting Decision Tree.*
   NeurIPS. (Job ranker.)
7. **Järvelin & Kekäläinen (2002)** — *Cumulated Gain-based Evaluation of IR Techniques.*
   ACM TOIS. (NDCG metric.)
8. **Hu et al. (2021)** — *LoRA: Low-Rank Adaptation of Large Language Models.*
   arXiv:2106.09685. (Cite as evaluated-and-deferred fine-tuning approach.)
9. **Dettmers et al. (2023)** — *QLoRA: Efficient Finetuning of Quantized LLMs.*
   arXiv:2305.14314.

Data sources (cite as datasets, not papers):
- **O\*NET 30.1**, US Department of Labor (CC BY 4.0).
- **Occupational Outlook Handbook**, US Bureau of Labor Statistics (public domain).
- **ITIDA / MCIT** (Arab Republic of Egypt) — ICT market & training programs.
- **Stack Overflow Developer Survey 2025** (ODbL).
- **MDN Web Docs**, Mozilla (CC-BY-SA).

---

## Quick-start for whoever picks this up
1. **Writing the thesis?** Start at Part 1, keep Part 4 open in a split pane.
2. **Building in parallel?** Start at Part 3.A, read the Coordination note, pick A1 or A2.
3. **Need a number?** It's in Part 0, Part 2, or Part 7 of the source docs — never invent
   one; trace it to a committed artifact.
</content>
</invoke>
