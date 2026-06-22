# Codebase Reference Guide for Thesis Writers

**Audience:** Humans and LLMs drafting the Sha8lny graduation thesis.  
**Purpose:** Separate **authoritative evidence** from **planning noise**, **retired code**, and **stubbed features** so every thesis claim traces to something real.

**Golden rule:** If you cannot point to a committed test, eval artifact, or a doc in `docs/product/` with a matching code path, **do not defend it as implemented**.

---

## 1. Start here (read in this order)

| Order | File | Why |
|------|------|-----|
| 1 | [`THESIS_GUIDE.md`](../../THESIS_GUIDE.md) | Chapter plan + evidence index + headline numbers |
| 2 | [`docs/thesis/README.md`](README.md) | Canonical facts table (test counts, metrics) — keep chapters consistent |
| 3 | [`docs/product/CLAIMS_REGISTER.md`](../product/CLAIMS_REGISTER.md) | Claim-by-claim Done / Partial / limitation |
| 4 | [`docs/product/ACADEMIC_SUMMARY.md`](../product/ACADEMIC_SUMMARY.md) | Two-page committee summary |
| 5 | **This file** | What to cite vs ignore in the repo |

**Re-verify before submission:**

```bash
cd Backend && env -u GEMINI_API_KEY pytest -q          # expect 382 passed
cd Frontend && npm run test:run                        # expect 74 passed
cd ai-models && pytest -q                              # expect 112 passed, 5 skipped
```

---

## 2. Tier 1 — Primary evidence (safe to cite)

These are the **defensibility layer**. Prefer them over raw code when stating results.

### 2.1 Evaluation & metrics

| Artifact | Proves |
|----------|--------|
| [`docs/product/RAG_RETRIEVAL_EVAL.md`](../product/RAG_RETRIEVAL_EVAL.md) | Staged retrieval eval (Recall@5, MRR, abstention) |
| [`ai-models/eval_results/retrieval/*.json`](../../ai-models/eval_results/retrieval/) | Committed raw numbers for every table row |
| [`docs/product/EVALUATION_REPORT.md`](../product/EVALUATION_REPORT.md) | Cross-module eval summary |
| [`ai-models/models/custom/EVAL_REPORT.md`](../../ai-models/models/custom/EVAL_REPORT.md) | Job ranker LOGO NDCG/MAP + honest limits |
| [`ai-models/models/custom/job_ranker_eval.json`](../../ai-models/models/custom/job_ranker_eval.json) | Ranker eval JSON |
| [`docs/product/RAG_ARCHITECTURE.md`](../product/RAG_ARCHITECTURE.md) | RAG pipeline diagram + technique list |
| [`ai-models/src/rag/credibility.py`](../../ai-models/src/rag/credibility.py) + [`tests/test_credibility.py`](../../ai-models/tests/test_credibility.py) | Deterministic source-credibility scorer |
| [`ai-models/scripts/eval_faithfulness.py`](../../ai-models/scripts/eval_faithfulness.py) | Faithfulness protocol (**scaffold** until results committed) |

### 2.2 Methodology & data provenance

| Artifact | Proves |
|----------|--------|
| [`docs/product/DATASET_REGISTRY.md`](../product/DATASET_REGISTRY.md) | Every source: license, USE/REJECT, credibility tier |
| [`ai-models/data/CITATIONS.md`](../../ai-models/data/CITATIONS.md) | Honest scope: US-centric O\*NET, synthetic jobs, roadmap.sh license |
| [`docs/product/ROLE_GRAPH_METHODOLOGY.md`](../product/ROLE_GRAPH_METHODOLOGY.md) | Assessment taxonomy, weights, formative framing |
| [`docs/product/JOB_RANKER_METHODOLOGY.md`](../product/JOB_RANKER_METHODOLOGY.md) | Ranker features, weak-supervision framing |
| [`docs/product/ADR-002-HOSTED-DEMO-AI-RUNTIME.md`](../product/ADR-002-HOSTED-DEMO-AI-RUNTIME.md) | **As-built** LLM runtime (Gemini default, Ollama fallback) |
| [`docs/product/GRADUATION_DEMO_RUNBOOK.md`](../product/GRADUATION_DEMO_RUNBOOK.md) | Reproducible demo (online + offline) |
| [`docs/product/EXPERT_REVIEW_PACKET.md`](../product/EXPERT_REVIEW_PACKET.md) | Expert review **protocol** (blank sheet ≠ completed study) |

### 2.3 Architecture & requirements (with banners)

| Artifact | Use for | Caveat |
|----------|---------|--------|
| [`docs/product/PROJECT_STATUS_FOR_REVIEW.md`](../product/PROJECT_STATUS_FOR_REVIEW.md) | Executive narrative, baseline→final story | — |
| [`docs/product/ARCHITECTURE.md`](../product/ARCHITECTURE.md) | Modular monolith, modules, patterns | **Top banner:** OpenAI/Anthropic/LangChain/Pinecone sections are **original plan only** |
| [`docs/product/TECH_STACK.md`](../product/TECH_STACK.md) | Stack rationale | Retired providers struck through; cite **as-built** from `docs/thesis/README.md` §3.1 |
| [`docs/product/SRS.md`](../product/SRS.md) | Requirements | Aspirational in places (microservices, Pinecone, daily scraping) — reconcile in methodology |
| [`docs/product/DATABASE_SCHEMA.md`](../product/DATABASE_SCHEMA.md) + `ERD.svg` | Schema / ERD | — |
| [`docs/product/PROFESSOR_FAQ.md`](../product/PROFESSOR_FAQ.md) | Anticipated committee questions | — |

### 2.4 Thesis chapter drafts

| Path | Role |
|------|------|
| [`docs/thesis/00-front-matter.md`](00-front-matter.md) … [`09-appendices.md`](09-appendices.md) | Draft chapter text — verify against Tier 1 before submission |
| [`docs/thesis/VISUAL-ASSETS.md`](VISUAL-ASSETS.md) | Figure/table captions checklist |

Search `docs/thesis/` for `[ASSUMPTION]` markers and resolve each against the codebase.

---

## 3. Tier 2 — Authoritative code (where behavior lives)

Use these when describing **how** something works. Pair every code citation with a **test file**.

### 3.1 Shared AI gateway

| Path | Role |
|------|------|
| `Backend/apps/core/gemma_client.py` | Single LLM gateway for all backend modules |
| `Backend/apps/core/llm_provider.py` | Gemini / Ollama provider implementations |
| `Backend/apps/core/ai_settings.py` | Env-driven AI config |
| `Backend/apps/core/gemini_keys.py` | Multi-key rotation on HTTP 429 |
| `ai-models/src/rag/runtime_settings.py` | AI-models-side settings (reads backend when available) |

### 3.2 Module map (implemented core)

| Module | Key files | Tests to cite |
|--------|-----------|---------------|
| **Users** | `apps/users/` | `apps/users/tests/` |
| **Assessments** | `ai_pipeline.py`, `engine.py`, `scenario_corpus/`, `scenario_retriever.py` | `test_engine.py`, `test_scenario_corpus.py`, `test_staged_flow.py` |
| **Roadmaps** | `services.py`, `assembler.py`, `ladder.py`, `baseline.py`, `ai_pipeline.py` | `test_ladder.py`, `test_baseline.py`, `test_full_loop.py`, `test_frontend_contracts.py` |
| **Jobs** | `apps/jobs/`, `ai-models/src/recommendations/` | `test_ranker.py`, `test_api.py` |
| **Advisory** | `llm_service.py`, `views.py` | `advisory/tests.py`, `AdvisoryPage.test.tsx` |
| **Courses** | `course_index.py`, `matching.py`, `ingest_courses.py` | `test_course_matching.py`, `test_course_api.py` |
| **Progress** | `apps/progress/services.py` | `apps/progress/tests.py` |
| **Career tools** | `apps/career_tools/` | `apps/career_tools/tests/` |
| **Notifications** | `apps/notifications/` | `apps/notifications/tests.py` (in-app only) |

### 3.3 RAG pipeline (`ai-models/src/rag/`)

| File | Technique |
|------|-----------|
| `corpus_validation.py` | Ingestion quality gate |
| `embeddings.py` | `all-MiniLM-L6-v2` |
| `hybrid_search.py` | BM25 + dense + RRF |
| `reranker.py` | Cross-encoder re-rank |
| `retriever.py` | Retrieval orchestration |
| `generator.py` | Gemini generation |
| `credibility.py` | Source tier scoring |

Repro scripts: `ai-models/scripts/run_retrieval_eval.py`, `stress_test_retrieval.py`.

### 3.4 Frontend (wired routes only)

Active route components live under `Frontend/src/features/*/routes/`. API contracts: `Frontend/src/lib/api.ts`.

| Route area | Page | Contract tests |
|------------|------|----------------|
| Assessment | `AssessmentPage`, `AssessmentSessionPage`, `AssessmentResultsPage` | `*.test.tsx` alongside |
| Roadmap | `RoadmapPage` + `RoadmapTrail`, `RoadmapStation`, `RoadmapSourcesPanel` | `RoadmapPage.test.tsx`, component tests |
| Jobs | `JobsPage`, `JobDetailPage`, `SavedJobsPage` | `JobsPage.test.tsx` |
| Advisory | `AdvisoryPage` + `MessageSources` | `AdvisoryPage.test.tsx` |
| Dashboard | `DashboardPage` | `DashboardPage.test.tsx` |
| Courses / Progress / Career tools | respective `*Page.tsx` | matching `*.test.tsx` |

### 3.5 Demo & operator commands

| Command | Purpose |
|---------|---------|
| `python manage.py seed_graduation_demo` | End-to-end demo account (AI roadmap + real course progress) |
| `python manage.py ingest_courses` | Load Coursera catalog from `ai-models/data/courses/` |
| `python manage.py rebuild_scenario_index` | Rebuild assessment scenario Chroma collection |
| `python manage.py scenario_corpus_audit --tier 1` | Verify 8-role scenario corpus |

---

## 4. Tier 3 — Outdated or aspirational (do NOT cite as as-built)

These files exist in the repo but describe **plans that were not built** or **superseded designs**. Cite them only when discussing **design evolution** or **deferred work**.

| Path | Problem | What to cite instead |
|------|---------|---------------------|
| **`ai-models/CLAUDE.md`** | Describes LLaMA/Mistral fine-tuning, QLoRA, Next.js frontend, separate GitHub repos, `$0 custom ML` — **not the running system** | `ADR-002`, `docs/thesis/README.md` §3.1, `gemma_client.py` |
| **`ai-models/FULL_CUSTOM_ML_GUIDE.md`** | Original 12-week custom-ML roadmap | `RAG_ARCHITECTURE.md`, `EVAL_REPORT.md` |
| **`ai-models/AI_MODELS_PLAN.md`** | Early planning doc | Same as above |
| **`docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md`** | Superseded by ADR-002 | `ADR-002-HOSTED-DEMO-AI-RUNTIME.md` |
| **`docs/product/ARCHITECTURE.md`** (sections below banner) | OpenAI, Anthropic, LangChain, Pinecone, microservices diagrams | Banner + `ARCHITECTURE.md` "Current Implementation Status" |
| **`docs/product/TECH_STACK.md`** (unmarked sections) | Original MPA/Next.js assumptions, retired providers | `docs/thesis/README.md` stack table |
| **`docs/product/SRS.md`** (unreconciled claims) | Microservices, Pinecone, 300+ concurrent users, daily scraping, WebSockets | As-built modular monolith + `CLAIMS_REGISTER` limitations |
| **`CLAUDE.md` (repo root)** | Module status can lag; check `CLAIMS_REGISTER` | `CLAIMS_REGISTER.md` + pytest counts |
| **`Backend/CLAUDE.md`** | Same — agent-oriented, may drift | Tests + product docs |

---

## 5. Tier 4 — Planning artifacts (intent, not proof)

Use for **background** or **future work**. Do **not** treat task checkboxes as completed features.

| Path | Contents |
|------|----------|
| `IMPLEMENTATION_PLAN.md` | Week 1–4 quality-refinement task list (mostly done; use `CLAIMS_REGISTER` for status) |
| `docs/superpowers/plans/*.md` | Implementation plans (roadmap ladder, etc.) |
| `docs/superpowers/specs/*.md` | Design specs — verify against merged code |
| `specs/005-scenario-rag-corpus/` | Feature spec for scenario RAG |
| `.claude/plans/` | Agent session plans |

**Rule:** A spec saying "we will build X" is not evidence that X exists. Find the test or eval artifact.

---

## 6. Tier 5 — Dead code, archive, and local garbage

### 6.1 Do not cite

| Path | Why |
|------|-----|
| **`archive/`** | Old thesis drafts (`archive/thesis/`), presentation scripts, **unvetted** dataset CSVs — not defended corpus |
| **`archive/datasets/potential-datasets/`** | Exploratory CSVs; not ingested or license-screened |
| **`.playwright-mcp/`** | Ephemeral browser snapshots (local tooling) |
| **`.claude/settings.local.json`** | Local agent permissions |
| **Retired frontend components** (already deleted) | `CareerAtlasHero`, `ProgressSnapshot`, `RoadmapAtlas`, `RoadmapNodeCard`, `RoadmapRail`, `RoadmapProgressView` — replaced by dashboard v2 + `RoadmapTrail` |
| **`roadmap-*.png` (repo root, untracked)** | Manual screenshots — not evidence unless committed with caption in `VISUAL-ASSETS.md` |
| **Untracked `ai-models/eval_results/faithfulness/*.json`** | Ad-hoc runs — not canonical until committed + referenced in `EVALUATION_REPORT.md` |

### 6.2 Dev-only / never defend as production corpus

| Path | Rule |
|------|------|
| `ai-models/data/roadmap-sh-data/` | **Personal-use license** — structure fallback only; **never cited as a source** in the advisor or thesis corpus section |
| `Backend/apps/jobs/ingest/fixtures/jobs_egypt_tech.csv` | **Synthetic** Egypt-tech fixtures for ranker demo — not real market data |
| Legacy demo courses (`demo.sha8alny.local`) | Purged by `ingest_courses --purge-demo`; do not describe as current |

### 6.3 Git branches (historical)

Branches like `001-frontend-visual-rebuild`, `002-ai-rag-experiment`, `005-scenario-rag-corpus` are **merged history**, not separate products. Describe the **current `main` / defensibility branch** only.

---

## 7. Partial & stub features (cite honestly as limitations)

| Feature | What works | What does **not** | Evidence |
|---------|------------|-------------------|----------|
| **Job ranker** | Eval artifacts, overlap fallback at runtime, explainability API | `job_ranker.lgb` **not committed** — LightGBM only when operator trains locally | `CLAIMS_REGISTER` C7, `EVAL_REPORT.md` |
| **Job corpus** | Synthetic fixture ingest + search | Real Wuzzuf/Bayt batch documented but **operator step** | `CLAIMS_REGISTER` C6, `DATASET_REGISTRY.md` |
| **O\*NET crosswalk** | Backend role, ~10 keyword mappings | Other 7 roles return **no** O\*NET links | `onet_mapper.py`, `ROLE_GRAPH_METHODOLOGY.md` |
| **Assessment** | Weighted deterministic scoring, optional LLM rubric, 8-role scenarios | **Not psychometrically validated**; expert review packet prepared, not completed | `CLAIMS_REGISTER` C3, `EXPERT_REVIEW_PACKET.md` |
| **Faithfulness eval** | Script + injectable judge | Full Gemini judge run **pending** committed results | `eval_faithfulness.py`, C11 |
| **Notifications** | Models, API, in-app list, preferences, signals | **Email/push delivery not implemented** | `notifications/services.py` (signal only), Ch.8 limitation |
| **Career tools export** | CRUD, ATS score, AI improve, structured JSON document | **PDF/DOCX returns placeholder bytes** — v2 | `career_tools/services.py` (`PDF placeholder`) |
| **Password reset** | Frontend route stub | **No backend endpoint** | `ForgotPasswordPage.tsx` |
| **Celery / Channels** | Configured | AI often runs **in-request** in dev; WebSockets unused | `ARCHITECTURE.md`, demo runbook |
| **Arabic queries** | — | **Fails** — English embedder + corpus | stress test in `RAG_RETRIEVAL_EVAL.md` |

---

## 8. Quick lookup — "I am writing about X"

| Topic | Read first | Code | Do **not** use |
|-------|------------|------|----------------|
| RAG retrieval quality | `RAG_RETRIEVAL_EVAL.md` | `ai-models/src/rag/` | `FULL_CUSTOM_ML_GUIDE.md` |
| Advisory citations | `EVALUATION_REPORT.md` §1 | `advisory/llm_service.py`, `MessageSources.tsx` | Raw prompt strings only |
| Assessment scoring | `ROLE_GRAPH_METHODOLOGY.md` | `assessments/engine.py` | LLM self-reported scores |
| Roadmap generation | `roadmap-personalization-ladder` spec (design) | `roadmaps/ladder.py`, `baseline.py`, `services.py` | roadmap.sh as "our corpus" |
| Course matching | `test_course_matching.py` | `courses/matching.py`, `course_index.py` | Hand-wavy "AI picks courses" |
| Job matching | `JOB_RANKER_METHODOLOGY.md` | `jobs/`, `recommendations/ranker.py` | `archive/datasets/*.csv` |
| Stack / architecture | `docs/thesis/README.md` §3.1 | `config/settings/`, `gemma_client.py` | SRS microservices diagram |
| Demo reproducibility | `GRADUATION_DEMO_RUNBOOK.md` | `seed_graduation_demo.py` | Fake `demo.sha8alny.local` URLs |
| Test coverage | `docs/thesis/README.md` §3.4 | `pytest`, `npm run test:run` | Invented percentages |
| Limitations | `CLAIMS_REGISTER.md` §Limitations | — | Hiding partial status |

---

## 9. Numbers you may state verbatim

From `docs/thesis/README.md` (re-verify before print):

| Metric | Value |
|--------|-------|
| Backend tests | **382** passing |
| Frontend tests | **74** passing |
| AI-layer tests | **112** passing, 5 skipped |
| RAG Recall@5 | **0.118 → 0.609** (rerank peak **0.627**) |
| RAG MRR | **0.109 → 0.544** (rerank peak **0.553**) |
| Ranker NDCG@5 (LightGBM / overlap / random) | **0.5895 / 0.5603 / 0.1597** |
| Assessment roles | **8** (Tier-1 scenario audit passes) |

---

## 10. Anti-patterns for LLM thesis writers

1. **Do not** describe LLaMA/Mistral fine-tuning or QLoRA as implemented — it was evaluated and **deferred** (ADR-002).
2. **Do not** claim Pinecone, LangChain, or OpenAI/Anthropic in the as-built system.
3. **Do not** cite `archive/thesis/` or old chapter drafts as current implementation.
4. **Do not** present `jobs_egypt_tech.csv` as real Egyptian market coverage.
5. **Do not** present roadmap.sh content as redistributable or citable career knowledge.
6. **Do not** claim PDF resume export works — structured JSON only.
7. **Do not** claim push/email notifications are delivered.
8. **Do not** invent test counts — run the commands in §1.
9. **Do not** treat `IMPLEMENTATION_PLAN.md` checkboxes as automatically done.
10. **Do** frame weak-supervision ranker and formative assessment as **methodology demonstrations**, not production benchmarks.

---

*Last aligned with branch `defensibility/week4-academic-package` (2026-06-20). When in doubt, `CLAIMS_REGISTER.md` wins.*
