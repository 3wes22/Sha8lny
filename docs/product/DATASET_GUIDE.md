# Sha8lny — Dataset Guide: Shapes, Storage, and Feature Mapping

**Prepared:** 2026-06-15
**Purpose:** A precise explanation of every dataset in the project — what it
looks like (shape), where it lives, whether datasets are merged, and **which
feature uses which dataset**. Companion to `DATASET_REGISTRY.md` (licenses) and
`RAG_RETRIEVAL_EVAL.md` (retrieval quality).

---

## 1. The short answer

The project uses **five datasets in three different storage forms**, and they
are **NOT all merged into one pile.** Two key facts:

1. There are **two separate vector databases**, not one. The career-knowledge
   corpus (for the Advisor and Roadmaps) and the assessment-scenario corpus
   (for the Assessment) are **independent Chroma collections** that never mix.
2. Within the career-knowledge corpus, seven *sources* **are** merged into a
   single searchable collection — but every document keeps a `source` and
   `quality_tier` tag, so they are unified for search yet individually
   attributable for citations and filterable by quality. "Merged for retrieval,
   separable for provenance."

Two further datasets (the job-ranker postings and the O\*NET crosswalk) are
**tabular/structured data, not embedded into any vector store at all.**

---

## 2. The datasets at a glance

| # | Dataset | Form | Storage | Feature(s) it powers |
|---|---|---|---|---|
| 1 | **Career-knowledge corpus** (7 sources) | Text → embeddings | Chroma collection `career_knowledge` | **AI Advisor**, **Roadmap** structure retrieval |
| 2 | **Assessment-scenario corpus** | Text → embeddings | Chroma collection `assessment_scenarios` (separate) | **Assessment** question generation |
| 3 | **Job postings** | Tabular (JSON/DB rows) | `job_ranker_training.json` + Postgres `Job` table | **Jobs** ranking & matching |
| 4 | **O\*NET database** | Tab-separated tables | Raw files in `onet_data/` | **Roadmap** O\*NET crosswalk (+ partially fed into #1) |
| 5 | **roadmap.sh content** | Markdown | Files in `roadmap-sh-data/` | **Roadmap** structure (+ fed into #1 as dev-fallback) |

The rest of this document takes each in turn.

---

## 3. Dataset #1 — The Career-Knowledge Corpus (the RAG corpus)

This is the dataset we rebuilt this cycle. It powers the **AI Advisor** and the
**Roadmap** source-retrieval.

### 3.1 What it's made of (seven sources, merged into one collection)

Stored as markdown files under `ai-models/data/knowledge_base/`, then embedded
into the **single Chroma collection `career_knowledge`** (~64,300 documents):

| Source tag | What it contains | Files | Quality tier |
|---|---|---|---|
| `egypt_official` | Egyptian ICT market facts, salaries, government training programs (ITIDA/MCIT) | 2 | official |
| `bls_ooh` | US Bureau of Labor occupation profiles (what jobs do, outlook) | 8 | official |
| `mdn` | Web/technical concept docs (HTTP, JavaScript, security…) | 12 | established |
| `tech_trends` | Stack Overflow 2025 survey technology trends | 1 | established |
| `knowledge_base` | Curated Egypt-specific career prose | 4 | curated |
| `onet` | Occupation tasks/titles (a *prose subset* of O\*NET — see §6) | — | official |
| `roadmap.sh` | Learning-path topic content | many | **dev_fallback** (never cited) |

These are **merged into one collection** so a single user question searches all
credible career knowledge at once. They are **not blended into anonymity**: each
document carries metadata that keeps it attributable.

### 3.2 The shape of one document (the metadata schema)

After processing, every entry in `career_knowledge` is a record like:

```jsonc
{
  "id": "egy_3f8a1c2b_4",                       // unique chunk id
  "content": "## Free and subsidized programs an Egyptian job seeker can join\n...",
  "embedding": [0.0123, -0.0456, ...],          // 384-dim vector (all-MiniLM-L6-v2)
  "metadata": {
    "source": "egypt_official",                 // which dataset this came from
    "quality_tier": "official",                 // official | established | curated | dev_fallback
    "file": "talent-and-training-programs.md",  // source file
    "section": "Free and subsidized programs...",// heading (for citation + diversity)
    "subsection": "...",                         // optional sub-heading
    "category": "career_development",            // topical bucket
    "url": "https://itida.gov.eg/english/..."    // citation link (fetched sources)
  }
}
```

The pipeline that produces these documents:

```
raw markdown file
  → validation layer (provenance header, length, structure, junk checks)
  → structure-aware chunker (split on headings, keep sentences whole)
  → metadata tagging (source, quality_tier, section, url…)
  → embed with sentence-transformers (all-MiniLM-L6-v2, 384-dim)
  → store in Chroma collection `career_knowledge` (de-duplicated)
```

### 3.3 How the two features use it

**AI Advisor** (`Backend/apps/advisory/llm_service.py`): on each user message it
calls the retriever, which runs hybrid search (BM25 + vector) → fusion →
cross-encoder re-ranking → confidence tiering → abstention. The top passages
become the grounded context and the on-screen "Sources" with confidence labels.

**Roadmap** (`Backend/apps/roadmaps/path_retriever.py`): when generating a
learning roadmap it queries the **same collection** but **filtered by source**
(`source = roadmap.sh`) to retrieve learning-path structure for the target role,
which the assembler turns into phases/milestones with provenance.

---

## 4. Dataset #2 — The Assessment-Scenario Corpus (separate vector DB)

This is a **completely separate dataset and a separate Chroma collection**
(`assessment_scenarios`, at its own `SCENARIO_VECTOR_DB_PATH`). It is **not**
mixed with the career-knowledge corpus — different content, different schema,
different purpose.

- **Lives in:** `Backend/apps/assessments/scenario_corpus/<role>.py` (one file
  per role), assembled via `registry.py`.
- **Powers:** the **Assessment** feature. When generating assessment questions
  for a role, the system retrieves role-relevant *scenarios* to ground the LLM's
  question generation (so questions are realistic and role-specific, not generic).
- **Shape of one scenario** (`schema.py` → `ScenarioDocument`):

```jsonc
{
  "doc_id": "backend.decorators.s1.single_choice.fallback-seed",
  "role_key": "backend",
  "subskill_key": "decorators",
  "competency": "...", "dimension_key": "...", "difficulty": 2,
  "stem": "Which decorator pattern best preserves the wrapped callable's metadata?",
  "options": [ { "option_id": "a", "label": "..." }, ... ],
  "explanation": "...", "learning_objective": "..."
}
```

- **Current coverage (honest):** only the **`backend` role is seeded (12
  scenarios)**; the other 7 roles (`frontend`, `fullstack`, `data_science`,
  `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`) are empty
  and **fall back gracefully** to deterministic question generation. Seeding the
  remaining roles is planned work (Implementation Plan, Tasks 2.6–2.8).

**Why it's separate:** assessment scenarios are structured multiple-choice items
with role/subskill keys and answer options — a different shape and a different
retrieval intent than free-text career knowledge. Merging them would pollute
both retrievals.

---

## 5. Dataset #3 — Job Postings (tabular, not embedded for RAG)

Powers the **Jobs** feature (search, skill-matching, ranking).

- **Training fixture:** `ai-models/data/job_ranker_training.json` — a **list of
  60 job-posting objects**:

```jsonc
{
  "id": "b6283296-...",
  "title": "Backend Developer (Python/Django)",
  "description": "Instabug is hiring a Backend Developer in Egypt.",
  "requirements": "Python, Django, PostgreSQL, REST API, Docker",
  "experience_level": "entry",
  "posted_date": "2026-06-01",
  "location_country": "Egypt",
  "required_skills": ["Django", "Docker", "PostgreSQL", ...]
}
```

- **How it's used:** features are engineered from these rows (skill overlap,
  experience match, freshness, location) and a **LightGBM ranker**
  (`job_ranker.lgb`) is trained to order jobs for a user. This is a
  *machine-learning model trained on tabular data* — **not** a vector search.
  Live job rows also live in the Postgres `Job` table.
- **Honest note:** these 60 postings are **synthetic fixtures** (real company
  names, templated descriptions). Replacing them with real labeled Egyptian
  postings is documented future work. See `models/custom/EVAL_REPORT.md`.

This dataset is **not merged** with either vector corpus — it is structured data
for a supervised ranking model.

---

## 6. Dataset #4 — O\*NET (used two different ways)

The US Department of Labor's O\*NET 30.1 database (`ai-models/data/onet_data/`,
tab-separated tables). It is used in **two distinct ways** — this is the one
dataset that genuinely spans two storage forms:

1. **A prose subset feeds the RAG corpus** (Dataset #1): only the
   human-readable files (`Occupation Data`, `Task Statements`,
   `Technology Skills`) are embedded into `career_knowledge` (tag `source=onet`).
   The bulk *numeric rating* tables are **deliberately excluded** — they were the
   358k-row flood that broke the original system.
2. **A keyword crosswalk for Roadmaps** (`Backend/apps/roadmaps/onet_mapper.py`):
   a *direct lookup* (no embeddings) that maps roadmap milestone keywords to
   O\*NET element IDs, giving roadmap milestones an official reference. Currently
   a proof-of-concept depth for the **backend** role only.

So: O\*NET is **partly merged** (its prose) into the RAG corpus, and **partly
used standalone** (its codes) by the roadmap crosswalk.

---

## 7. Dataset #5 — roadmap.sh content (used two ways, license-restricted)

The developer-roadmap markdown content (`ai-models/data/roadmap-sh-data/`).

1. **Embedded into the RAG corpus** as `source=roadmap.sh`, tagged
   `quality_tier=dev_fallback` — meaning it is searchable internally but is
   **never surfaced as a cited source** to users, because its license forbids
   redistribution.
2. **Read for roadmap structure** by `path_normalizer.py` / `assembler.py` to
   shape learning-path phases.

**License caution (documented):** roadmap.sh content is personal-use-only. It is
treated as development-only scaffolding and must be replaced with an openly
licensed alternative before any public release (see `data/CITATIONS.md`).

---

## 8. Did we merge the datasets? — precise answer

| Question | Answer |
|---|---|
| Are all datasets in one place? | **No.** Two separate vector DBs + tabular data + raw O\*NET tables. |
| Is the career-knowledge corpus merged? | **Yes — 7 sources in one Chroma collection,** but each doc keeps `source` + `quality_tier` so it stays attributable and filterable. |
| Is the assessment corpus merged with it? | **No — entirely separate collection.** |
| Are job postings merged into a vector DB? | **No — tabular data for a LightGBM model.** |
| Is O\*NET merged? | **Partly** — its prose subset is in the RAG corpus; its codes are used standalone by the roadmap crosswalk. |

---

## 9. Feature → Dataset map (the direct answer)

| Feature | Primary dataset(s) | Storage / mechanism |
|---|---|---|
| **AI Career Advisor** | Career-knowledge corpus (all 7 sources) | `career_knowledge` Chroma collection; hybrid retrieval + rerank + citations |
| **Learning Roadmap** | roadmap.sh (structure) + O\*NET crosswalk (references) | `career_knowledge` filtered by `source=roadmap.sh`; `onet_mapper` direct lookup |
| **Skills Assessment** | Assessment-scenario corpus | `assessment_scenarios` Chroma collection (separate); backend role seeded |
| **Jobs (match & rank)** | Job postings | `job_ranker_training.json` → LightGBM `job_ranker.lgb`; Postgres `Job` rows |
| **Progress / Dashboard** | (derived from user activity — no external dataset) | Application DB |

---

## 10. Where to verify each claim

- Corpus composition & metadata: `ai-models/src/rag/build_vector_db.py`,
  live count via `scripts/run_retrieval_eval.py`.
- Source licenses & decisions: `docs/product/DATASET_REGISTRY.md`.
- Validation layer: `ai-models/src/rag/corpus_validation.py` +
  `scripts/validate_corpus.py`.
- Assessment corpus: `Backend/apps/assessments/scenario_corpus/` +
  `scenario_retriever.py`.
- Job ranker: `ai-models/data/job_ranker_training.json`,
  `models/custom/EVAL_REPORT.md`.
- O\*NET crosswalk: `Backend/apps/roadmaps/onet_mapper.py`.
