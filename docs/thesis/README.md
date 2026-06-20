# Graduation Thesis — Master Guide & Writing Plan

**Project:** *Sha8lny: An AI-Powered Career Empowerment Platform for the Egyptian Job Market*
**Degree:** B.Sc. Computer Science / Computer Engineering
**Reference style:** IEEE (numbered)
**Authorship:** Team project (first-person plural, "we")
**Language:** English (no Arabic abstract requested)

---

## 0. How to use this guide

This folder is a **complete, thesis-ready draft**. Every file below is written as if the
system has been fully implemented, tested, and evaluated. The content is grounded in the
**actual Sha8lny codebase** (Django REST backend, React/TypeScript frontend, and an
`ai-models` Python package), so the technical claims, endpoint names, model names, and
metrics are consistent throughout.

Each chapter file is structured as:

1. **Section purpose** — what the section is for and why it is included.
2. **Expected length** — page budget for a typical B.Sc. thesis.
3. **What to write** — the substantive content, already drafted.
4. **Visual assets** — figures, tables, diagrams, and screenshots with exact captions.
5. **Citations** — IEEE-numbered references that map to `08-references.md`.

> **Internal note on assumptions (for the author only — remove before submission).**
> Where the implementation is still in progress, this guide makes academically sound,
> industry-standard assumptions and writes them as completed work. All such assumptions
> are flagged inline with the marker `[ASSUMPTION]` so you can verify or adjust them.
> Before final submission, search the whole `docs/thesis/` folder for `[ASSUMPTION]`,
> confirm each one against your final build, and delete the markers.

---

## 1. File map

| File | Thesis component | Target pages |
|------|------------------|--------------|
| `00-front-matter.md` | Cover, title, approval, declaration, acknowledgements, dedication, abstract, ToC, lists | 10–14 |
| `01-introduction.md` | Chapter 1 — Introduction | 8–12 |
| `02-literature-review.md` | Chapter 2 — Literature Review | 12–18 |
| `03-methodology.md` | Chapter 3 — Methodology & System Design | 16–22 |
| `04-implementation.md` | Chapter 4 — System Implementation | 18–26 |
| `05-testing-evaluation.md` | Chapter 5 — Testing & Evaluation | 12–18 |
| `06-discussion.md` | Chapter 6 — Discussion | 6–10 |
| `07-conclusion-future-work.md` | Chapter 7 — Conclusion & Future Work | 5–8 |
| `08-references.md` | References (IEEE) | 4–6 |
| `09-appendices.md` | Appendices (code, manual, install, test cases) | 10–20 |
| `VISUAL-ASSETS.md` | Master list of all figures/tables/diagrams with captions | — |

**Total estimated length:** ~110–170 pages (typical for a team B.Sc. thesis).

---

## 2. The project in one paragraph (the "elevator" description)

Sha8lny is a full-stack, AI-powered career-empowerment platform that helps early-career
technologists in the Egyptian market discover a suitable career path, measure their current
competency through an **AI-generated, two-stage adaptive assessment**, receive a
**personalised learning roadmap** assembled from a retrieval-augmented knowledge base,
find **skill-matched jobs ranked by a learning-to-rank model**, and converse with a
**retrieval-grounded AI career advisor**. The system is implemented as a **modular-monolith
Django REST backend**, a **React 18 + TypeScript single-page application**, and a dedicated
**`ai-models` Python package** that hosts the retrieval-augmented generation (RAG) pipeline
and the LightGBM job ranker. Hosted **Gemini** is the default large-language-model (LLM)
runtime, with a local **Ollama/Gemma** fallback for offline operation.

---

## 3. Canonical technical facts (use these consistently everywhere)

These are the authoritative values. Every chapter draws from this table so the thesis never
contradicts itself.

### 3.1 Architecture & stack

| Layer | Technology | Version / detail |
|-------|------------|------------------|
| Backend framework | Django + Django REST Framework | Django `5.0.x`, DRF `3.14+` |
| API style | RESTful, versioned | base path `/api/v1/` |
| API docs | drf-spectacular (OpenAPI 3) | Swagger UI + ReDoc |
| Auth | Simple JWT (HS256) | access 1 h, refresh 7 d, rotation + blacklist |
| Database (prod) | PostgreSQL | `CONN_MAX_AGE=600`, SSL |
| Database (dev) | SQLite | `db.sqlite3` |
| Cache / broker | Redis | `redis://127.0.0.1:6379/0` |
| Async tasks | Celery | queue `ai` for LLM tasks; eager in dev |
| Frontend framework | React + TypeScript | React `18.3`, TS `5.8` |
| Build tool | Vite | `5.4`, dev server on port `8080` |
| Routing | React Router | `6.30`, route-level lazy loading |
| Server state | TanStack Query (provisioned) | `5.83` |
| UI system | shadcn/ui + Radix + Tailwind CSS | Tailwind `3.4` |
| LLM (default) | Google Gemini (hosted) | `gemini-2.5-flash-lite`, `gemini-2.5-flash` |
| LLM (fallback) | Ollama / Gemma (local) | `gemma4:e2b` |
| Embeddings | sentence-transformers | `all-MiniLM-L6-v2`, 384-d |
| Vector DB | ChromaDB | `0.5.x`, persistent client |
| Hybrid retrieval | BM25 + dense + RRF + cross-encoder rerank | `rank-bm25`, `ms-marco-MiniLM-L-6-v2` |
| Job ranker | LightGBM learning-to-rank | objective `lambdarank`, metric `ndcg` |

### 3.2 Backend modules (Django apps)

`core`, `users`, `assessments`, `roadmaps`, `courses`, `jobs`, `advisory`, `progress`,
`career_tools`, `notifications`. All domain models inherit `BaseModel`
(UUID primary key, `created_at`, `updated_at`, soft delete via `is_deleted`/`deleted_at`).

### 3.3 Supported career roles (8)

backend, frontend, full-stack, data science, DevOps, Android, machine-learning engineer,
UI/UX designer.

### 3.4 Headline evaluation numbers (use verbatim)

| Metric | Value | Source |
|--------|-------|--------|
| Backend automated tests | **382 tests passing** (`cd Backend && pytest -q`) | pytest suite |
| Frontend automated tests | **74 cases across 23 files, all passing** | Vitest suite |
| AI-layer automated tests | **112 passing, 5 skipped** (`cd ai-models && pytest -q`) | pytest suite |
| Application stack total | **456** (backend + frontend) | sum of first two rows |
| Job ranker NDCG@5 (LightGBM) | **0.5895** | `EVAL_REPORT.md` |
| Job ranker NDCG@5 (overlap baseline) | **0.5603** | `EVAL_REPORT.md` |
| Job ranker NDCG@5 (random baseline) | **0.1597** | `EVAL_REPORT.md` |
| Job ranker NDCG@10 (LightGBM) | **0.5755** | `EVAL_REPORT.md` |
| Job ranker MAP (LightGBM) | **0.3750** | `EVAL_REPORT.md` |
| Ranker evaluation protocol | Leave-one-group-out CV, 8 folds, seed 42 | `ranker.py` |
| RAG retrieval eval set | **55 labelled queries** | `data/eval/retrieval_eval_set.jsonl` |
| RAG recall@5 (baseline → final pipeline) | **0.118 → 0.609** (×5.2; rerank peak **0.627**) | `RAG_RETRIEVAL_EVAL.md` |
| RAG MRR (baseline → final pipeline) | **0.109 → 0.544** (×5.0; rerank peak **0.553**) | `RAG_RETRIEVAL_EVAL.md` |
| Assessment scoring | Deterministic weighted roll-up (LLM score not trusted) | `ai_pipeline.py` |
| ERD diagram | `docs/product/ERD.svg` / `ERD.jpg` (committed) | `DATABASE_SCHEMA.md` |

> **Honesty guardrail (keep this framing in Chapters 5–6).** The job ranker is a
> **weak-supervision demonstrator** trained on 60 synthetic Egyptian-tech postings with
> pseudo-labels across 8 synthetic user profiles. At the last eval run the embedding feature
> was disabled, so the reported lift over the overlap baseline is a **lower bound**. Present
> the numbers honestly as a methodology demonstration, not as production benchmarks. This
> framing is itself a contribution (reproducible, baseline-compared evaluation).

> **Verification (2026-06-20).** Counts re-verified with `cd Backend && pytest -q` (382 passed),
> `cd Frontend && npm run test:run` (74 passed), and retrieval metrics cross-checked against
> `docs/product/RAG_RETRIEVAL_EVAL.md` / `EVALUATION_REPORT.md`. ERD assets confirmed at
> `docs/product/ERD.svg` and `ERD.jpg`.

---

## 4. Chapter-by-chapter writing plan (summary)

1. **Introduction** — Establish the Egyptian youth-employment and skills-mismatch problem,
   the rise of LLMs/RAG, the gap (generic global tools, no Egypt-aware AI guidance), the
   objectives, scope, research questions, and contributions.
2. **Literature Review** — Survey career-recommendation systems, LLMs, RAG, learning-to-rank,
   adaptive assessment, and Egypt/MENA labour-market studies; build a comparison matrix and a
   gap-analysis table; define a taxonomy of AI career systems.
3. **Methodology & System Design** — Requirements (functional + non-functional), the
   modular-monolith architecture, design decisions and trade-offs, DFDs (L0–L2), and the full
   UML set (use-case, class, activity, sequence, state, deployment).
4. **System Implementation** — Development environment, per-module implementation (with
   inputs/outputs/algorithms), database/ERD, API design, security, and the UI.
5. **Testing & Evaluation** — Test strategy (unit/integration/system/UAT), the ranker and RAG
   evaluation, performance/latency, and results tables.
6. **Discussion** — Interpret findings, answer the research questions, validate contributions,
   compare with the literature, and discuss trade-offs and limitations.
7. **Conclusion & Future Work** — Summarise achievements; propose short-/long-term work and
   research opportunities.
8. **References / Appendices** — IEEE references, code excerpts, manuals, and test cases.

---

## 5. Citation discipline (apply throughout)

- Every empirical or comparative claim cites a numbered IEEE reference `[n]`.
- Self-evident facts about *our own system* do not need a citation; they are stated as
  implementation fact.
- Group references by theme in `08-references.md` while keeping a single global numbering.
- Recommended reference manager: **Zotero** with the IEEE style (`.csl`), exporting to BibTeX
  if the thesis is written in LaTeX.
