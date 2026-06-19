# Sha8alny (Grad-Project) — AI Model Onboarding Reference

**Purpose**: One document for other AI assistants (and contributors) to map the monorepo, trace requests, understand AI/RAG paths, and know where to extend the system.

**Repo layout** (authoritative):

```text
Grad-Project/
├── Backend/                 # Django 5 modular monolith, DRF, JWT
├── Frontend/                # React 18 + TypeScript + Vite
├── ai-models/               # Installed as editable package `rag` + ML utilities
├── docs/product/            # Product/engineering docs (this file)
└── specs/                   # Spec-kit feature tracks (e.g. 005-scenario-rag-corpus)
```

---

## 1. Architecture map

### High-level

| Layer | Technology | Role |
|-------|------------|------|
| **Client** | React + Vite + TanStack Query | SPA; calls `/api/v1/...` with JWT |
| **API** | Django REST Framework | Auth, validation, orchestration, persistence |
| **AI runtime** | `apps.core` (GemmaClient, ai_settings, ai_validation) | Hosted Gemini default + Ollama path; shared timeouts/metadata |
| **Async work** | Celery (optional) + Redis | Assessment question generation tasks when not eager |
| **Data** | PostgreSQL (prod) / SQLite (dev) | Users, assessments, roadmaps, jobs, advisory, etc. |
| **Vector / RAG** | ChromaDB + sentence-transformers | Two separate concerns (see §4) |

### Monolith boundaries

- **No microservices**: apps under `Backend/apps/*` import each other in-process.
- **Contract discipline**: API shapes + assessment payloads are guarded by serializers, `apps.core.ai_validation`, and frontend contract tests where present.
- **AI orchestration stays in Backend**: LLM calls and staged assessment logic live in Django code, not in the browser.

### Diagram (conceptual)

```text
Browser (Frontend)
    │  HTTPS + JWT
    ▼
Django URLConf  config/urls.py  →  /api/v1/{users,assessment,roadmap,jobs,advisory,...}/
    │
    ▼
DRF ViewSets / APIViews  (per app views.py)
    │
    ├──► Serializers → Models → DB
    │
    └──► Services / ai_pipeline / tasks → GemmaClient / Celery
              │
              ├──► Optional: rag.retriever (ai-models package) for advisory Chroma
              └──► apps.assessments.scenario_retriever (Backend-only) for assessment few-shot RAG
```

---

## 2. Core modules

### Backend (`Backend/apps/`)

| App | Responsibility |
|-----|----------------|
| **core** | Base models, `GemmaClient`, `ai_settings`, `ai_validation`, throttles, health, exceptions |
| **users** | Auth (JWT), profiles, skills |
| **assessments** | Assessments CRUD, staged flow, `role_graph_data`, `ai_pipeline`, scenario corpus + retriever |
| **roadmaps** | Learning paths, templates, progress |
| **jobs** | Job listings / saved jobs (product-specific) |
| **advisory** | Chat, `LLMAdvisoryService`, optional `rag` package integration |
| **progress** | User progress metrics |
| **notifications** | Notification APIs |
| **courses** | Course-related API (routing may be commented in main `urls.py`) |
| **career_tools** | Resume/portfolio hooks (scope varies) |

### Frontend (`Frontend/src/`)

| Area | Path pattern | Responsibility |
|------|----------------|-----------------|
| **Routes** | `app/AppRoutes.tsx` | React Router; protected vs public |
| **Features** | `features/*` | Domain UI: `assessment`, `auth`, `roadmap`, etc. |
| **API** | `lib/api.ts` | Typed client, token refresh, resource helpers |
| **UI primitives** | `components/ui/*` | shadcn/Radix-style components |
| **Shared layout** | `shared/*` | Shell, layout wrappers |

### ai-models (`ai-models/`)

| Area | Role |
|------|------|
| **Package `rag`** (import path) | `scope_rules`, `retriever`, `vector_store`, `embeddings` — advisory career knowledge Chroma collection `career_knowledge` |
| **Other subpackages** | Assessment / roadmap / LLM experiments (see `ai-models/CLAUDE.md` if present) |

---

## 3. Request lifecycle (typical paths)

### 3.1 Authenticated REST request (generic)

1. **Browser** sends `Authorization: Bearer <access>` to `VITE_API_BASE_URL` + `/api/v1/...`.
2. **`Frontend/src/lib/api.ts`** attaches tokens, handles 401 refresh when implemented.
3. **`Backend/config/urls.py`** routes `/api/v1/users/`, `/api/v1/assessment/`, etc.
4. **DRF** permission classes (e.g. `IsAuthenticated`) run.
5. **View** validates input via **serializer**, reads/writes **models**, returns **Response**.

### 3.2 Create assessment (staged skills)

1. `POST /api/v1/assessment/` → `AssessmentViewSet.create` (`apps/assessments/views.py`).
2. Serializer persists `Assessment` with staged flags / metadata.
3. If staged: **`generate_stage_one_task`** (Celery) or **`run_generate_stage_one`** when `CELERY_TASK_ALWAYS_EAGER` — see `dispatch_assessment_task` in the same viewset.
4. Task path uses **`AssessmentAIService`** (`ai_pipeline.py`): role graph load, prompt build, LLM structured call, sanitize/repair, cache, fallbacks.
5. Client polls or refetches assessment until questions appear (frontend feature code under `features/assessment`).

### 3.3 Advisory chat

1. Advisory routes under `/api/v1/advisory/` → views delegate to **`LLMAdvisoryService`** (`apps/advisory/llm_service.py`).
2. **`get_rag_runtime()`** tries `import_module("rag.scope_rules")` and `rag.retriever` (the **ai-models** package).
3. If runtime exists: **classify** message → optional **retrieve_context** → build prompt → **GemmaClient** completion.
4. If runtime missing: fallback response path (no vector retrieval).

### 3.4 Scenario corpus RAG (assessments only)

1. When **`ASSESSMENT_SCENARIO_RAG_ENABLED`** is true, **`AssessmentAIService._build_stage_prompt`** appends **`_build_retrieved_examples_block`** after static few-shot text.
2. **`ScenarioRetriever`** (`apps/assessments/scenario_retriever.py`) queries Chroma collection **`assessment_scenarios`** at **`SCENARIO_VECTOR_DB_PATH`** (separate from advisory `CHROMA_PERSIST_DIR`).
3. Failures return `[]` — generation never hard-fails on retrieval.

---

## 4. Embeddings, retrieval, reranking

### Two RAG stacks (do not conflate)

| Concern | Location | Collection / model | Notes |
|---------|----------|-------------------|--------|
| **Career advisory knowledge** | `ai-models/src/rag/` → imported as **`rag`** | Chroma **`career_knowledge`**; persist dir from `rag.runtime_settings` / `CHROMA_PERSIST_DIR` | `retrieve_context()` → `vector_store.search()` |
| **Assessment scenario few-shots** | `Backend/apps/assessments/scenario_retriever.py` | Chroma **`assessment_scenarios`** at `SCENARIO_VECTOR_DB_PATH` | Only augments question-generation prompts |

### Embeddings

- **Advisory path**: `ai-models/src/rag/embeddings.py` — `embed_text()` used at index and query time for `career_knowledge`.
- **Assessment scenario path**: `sentence_transformers.SentenceTransformer(EMBEDDING_MODEL)` in Backend retriever and `rebuild_scenario_index` management command; default model name in `apps.core.ai_settings.EMBEDDING_MODEL`.

### Retrieval

- **Advisory**: Cosine-style similarity via Chroma `collection.query`; scores derived from distance (`1 - distance` pattern in `vector_store.search`).
- **Assessment scenarios**: Query embedding built from **`ScenarioRetriever.build_embedding_text`** (competency, question_type, stage, scenario_context, stem); **hard metadata filter** `$and` on `role_key`, `question_type`, `stage`; top-k within that slice.

### Reranking

- **There is no separate reranker model** in-repo today. “Ranking” is:
  - Chroma’s nearest-neighbor order for a single embedding query, plus
  - **Optional** score threshold in `rag.retriever.retrieve_context` (`min_score`), and
  - **LLMAdvisoryService** truncating/normalizing documents (`MAX_RETRIEVED_DOCS`, char caps) — not cross-encoder reranking.
- **Assessment scenario audit** can flag **near-duplicate** pairs by pairwise cosine similarity over embedding texts — still not production reranking.

### Legacy / placeholder

- **`RAGContextService.retrieve_relevant_documents`** in `apps/advisory/services.py` is still largely **placeholder** (TODO vector DB); real advisory RAG is the **`rag`** package path used by `LLMAdvisoryService`.

---

## 5. Extension points

| Goal | Where to extend |
|------|-----------------|
| **New REST resource** | New or existing `apps/<app>/views.py`, `serializers.py`, `urls.py`; register in `Backend/config/urls.py` |
| **New React page** | `Frontend/src/app/AppRoutes.tsx` + `features/<domain>/` |
| **New assessment role / graph** | `role_graph_data.py`, `role_graph.py` aliases, staged tests, scenario corpus per-role module |
| **New scenario content** | `apps/assessments/scenario_corpus/<role>.py` + `AUTHOR_GUIDE.md`; `manage.py rebuild_scenario_index`; bump `SCENARIO_CORPUS_VERSION` when needed |
| **LLM provider / model** | `apps/core/ai_settings.py`, `apps/core/gemma_client.py`, env vars |
| **Prompt / schema for staged questions** | `apps/assessments/ai_pipeline.py` (`_build_stage_prompt`, JSON schema builders, fallbacks) |
| **Advisory scope / guardrails** | `ai-models` package: `rag/scope_rules.py` |
| **Advisory knowledge corpus** | `ai-models/src/rag/` ingest scripts + Chroma `career_knowledge` |
| **Cross-cutting AI validation** | `apps/core/ai_validation.py` |
| **Celery tasks** | Per-app `tasks.py`; assessment wiring in `apps/assessments/tasks.py` |

---

## 6. Files to master first (priority order)

### Cross-cutting (read first)

1. `Backend/config/urls.py` — API map  
2. `Backend/apps/core/ai_settings.py` — AI + vector env knobs  
3. `Backend/apps/core/gemma_client.py` — how LLM calls are made  
4. `Backend/apps/core/ai_validation.py` — structured output contracts  
5. `Frontend/src/lib/api.ts` — how the SPA talks to the API  
6. `Frontend/src/app/AppRoutes.tsx` — navigation surface  

### If you work on **assessments / staged AI**

7. `Backend/apps/assessments/ai_pipeline.py`  
8. `Backend/apps/assessments/role_graph.py` + `role_graph_data.py`  
9. `Backend/apps/assessments/engine.py` — allocation / scoring orchestration  
10. `Backend/apps/assessments/views.py` + `serializers.py`  
11. `Backend/apps/assessments/scenario_corpus/schema.py` + `registry.py`  
12. `Backend/apps/assessments/scenario_retriever.py`  
13. `specs/005-scenario-rag-corpus/` — scenario RAG spec/plan/tasks  

### If you work on **advisory / career RAG**

7. `Backend/apps/advisory/llm_service.py` (`get_rag_runtime`, `LLMAdvisoryService`)  
8. `ai-models/src/rag/retriever.py` + `vector_store.py` + `embeddings.py`  
9. `ai-models/src/rag/scope_rules.py`  

### If you work on **users / auth**

7. `Backend/apps/users/views.py` + serializers + JWT settings in `Backend/config/settings/`  

### Product / governance

- Root `CLAUDE.md`, `AGENTS.md`, `Backend/CLAUDE.md`  
- `.specify/memory/constitution.md` (spec-kit governance)  
- `docs/product/CODING_STANDARDS.md` (if present)  

---

## 7. Contributor learning roadmap

### Week 1 — Run and read

- [ ] Clone; run Backend (`migrate`, `runserver`) and Frontend (`npm install`, `npm run dev`).  
- [ ] Open Swagger: `/api/schema/swagger-ui/`.  
- [ ] Trace one **GET** and one **POST** (e.g. profile, assessment list) through `urls.py` → view → serializer.  
- [ ] Read `core/ai_settings.py` + `core/gemma_client.py` end-to-end.  

### Week 2 — Assessments vertical slice

- [ ] Read `role_graph.py` / `role_graph_data.py`; run `pytest apps/assessments/tests/test_role_graph.py`.  
- [ ] Read `ai_pipeline.py` staged paths; run `pytest apps/assessments/tests/test_stage_cache.py` (slower suite acceptable).  
- [ ] Follow `features/assessment` on Frontend from route → API hook → page.  

### Week 3 — Advisory + ai-models package

- [ ] Read `advisory/llm_service.py` and understand `get_rag_runtime()` failure modes.  
- [ ] Read `ai-models/src/rag/*`; try embedding + search in a notebook or script **if** local numpy/chromadb stack is healthy.  

### Week 4 — Extension practice

- [ ] Pick one: **small serializer change** with tests, **or** one **new scenario document** with `validate_scenario` clean, **or** a **docs-only** improvement to `specs/`.  
- [ ] Open PR; ensure `pytest` relevant apps + `npm run build` for Frontend if you touched it.  

### Ongoing

- Watch **`specs/*`** for feature contracts before large refactors.  
- Keep **scenario corpus** (`scenario_corpus/`) and **advisory Chroma** (`ai-models` / `CHROMA_PERSIST_DIR`) mentally separate.  

---

## Quick command reference

```bash
# Backend
cd Backend && source venv/bin/activate
python manage.py check
pytest apps/assessments/

# Frontend
cd Frontend && npm run build

# Scenario corpus (assessment RAG)
python manage.py rebuild_scenario_index
python manage.py scenario_corpus_audit
```

---

**Document maintenance**: When major AI or routing behavior changes, update this file in the same PR as the code change so downstream AI tools stay aligned.
