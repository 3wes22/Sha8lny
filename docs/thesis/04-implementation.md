# Chapter 4 — System Implementation

> **Chapter purpose.** Chapter 4 documents how the design of Chapter 3 was realised in code.
> It is written as completed work: every module is described by its *purpose, inputs, outputs,
> internal logic, and algorithms*; the database, API, security, and UI are specified concretely.
> Use real names (endpoints, models, classes) so the chapter is verifiable against the
> repository. **Target length: 18–26 pages.**
>
> **Style.** Technical and precise. Include short, illustrative code excerpts (10–25 lines)
> rather than dumping files; full listings go to Appendix A.

---

## 4.1 Development Environment

**What to write.** Specify the hardware, software, frameworks, and libraries used. **(≈2 pages.)**

### 4.1.1 Hardware

**Table 4.1 — Development and target hardware.**

| Role | Specification |
|------|---------------|
| Development workstation | Apple silicon / x86-64 laptop, 16 GB RAM, SSD |
| Local LLM fallback host (optional) | GPU-capable machine running Ollama (`gemma4:e2b`) |
| Target deployment (reference) | Linux VM, 2–4 vCPU, 8 GB RAM, plus managed PostgreSQL and Redis |

> `[ASSUMPTION]` Exact production sizing is given as a reasonable reference configuration for a
> demo deployment; adjust to your hosting.

### 4.1.2 Software, frameworks, and libraries

**Table 4.2 — Core technology stack and versions.**

| Layer | Technology | Version |
|-------|------------|---------|
| Language (backend) | Python | 3.13 |
| Web framework | Django / DRF | 5.0 / 3.14+ |
| Auth | djangorestframework-simplejwt | 5.3+ |
| API docs | drf-spectacular | 0.27+ |
| DB driver | psycopg2-binary | 2.9+ |
| Cache/queue | django-redis / celery / redis | 5.4+ / 5.3+ / 5.0+ |
| Vector DB | chromadb | 0.5.x |
| Embeddings | sentence-transformers | 2.2+ (`all-MiniLM-L6-v2`) |
| Sparse retrieval | rank-bm25 | 0.2+ |
| Ranker | lightgbm | 4.1+ |
| ML/NLP | transformers / torch | 4.35+ / 2.1+ |
| Testing (backend) | pytest / pytest-django | 7.4+ / 4.7+ |
| Language (frontend) | TypeScript | 5.8 |
| UI framework | React | 18.3 |
| Build tool | Vite | 5.4 |
| Routing | react-router-dom | 6.30 |
| Server state | @tanstack/react-query | 5.83 |
| Styling | Tailwind CSS | 3.4 |
| UI primitives | Radix UI / shadcn/ui | — |
| Testing (frontend) | Vitest / Testing Library | 1.3 / 14.2 |

### 4.1.3 Tooling and conventions

Version control with Git; code style enforced via `black`, `isort`, `flake8` (backend) and
ESLint (frontend); environment configuration via `.env` files; the `ai-models` package is
installed in editable mode (`-e ../ai-models`) so the backend imports the RAG and ranker code
directly.

---

## 4.2 Module Implementation

**What to write.** For each module, give purpose, inputs, outputs, internal logic, and the key
algorithms. **(≈8 pages — the heart of the chapter.)**

### 4.2.1 Core module

- **Purpose.** Shared infrastructure: the abstract `BaseModel`, the LLM client abstraction, AI
  throttles, validation, and AI settings.
- **Inputs / outputs.** Configuration (provider, model names, Chroma paths) in; typed LLM
  invocation contracts and validated JSON out.
- **Internal logic.** `GemmaClient` routes a request to a provider via `create_provider()`:
  `GeminiProvider` (default) or `OllamaProvider` (fallback), selecting a model by task type
  (`gemini-2.5-flash-lite` for JSON generation, `gemini-2.5-flash` for rubric validation).
  `ai_validation.py` extracts and repairs JSON, normalises stage questions, and validates
  rubrics. `ai_throttles.py` enforces `ai_burst` (3/min) and `ai_sustained` (20/hour).
- **Key facets.** Every domain model inherits `BaseModel` for UUID primary keys and soft
  deletion (`objects` returns active rows, `all_objects` returns all).

```python
# Illustrative: provider routing (apps/core/llm_provider.py)
def create_provider(settings):
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider(model_for_task)
    return OllamaProvider(host=settings.OLLAMA_HOST, model=settings.OLLAMA_MODEL)
```

### 4.2.2 Users module

- **Purpose.** Identity, profile, skills, and preferences.
- **Models.** `User` (email login, `auth0_id`, onboarding flags, language/timezone), `Skill`
  (self-referential taxonomy with `parent_skill`), `UserSkill` (proficiency, years, source,
  verification; unique per `(user, skill)`), `UserPreferences` (one-to-one).
- **Inputs / outputs.** Registration/login payloads in; JWT access/refresh tokens and profile
  JSON out.
- **Internal logic.** `SkillService` provides search, categories, gap analysis, and skill
  recommendations. The gap analysis compares a user's `UserSkill` set against a target role's
  required skills and returns missing/weak skills.
- **API.** `POST /users/auth/register|login|logout|refresh`, `GET/PUT/PATCH /users/me`,
  `/users/me/preferences`, skill and user-skill viewsets including
  `GET /users/user-skills/gap_analysis/`.

### 4.2.3 Assessments module (flagship)

- **Purpose.** Two-stage, role-aware competency assessment for 8 roles with deterministic
  weighted scoring.
- **Models.** `Assessment` (stage, target_career, per-stage questions/responses, gap_profile,
  roadmap_signal, `ai_processing_status`, `ai_trace_id`) and `AssessmentResult` (overall_score,
  skill_scores, strengths, areas_for_improvement, recommended_careers, roadmap_signal,
  `llm_model_used`, token counts, version).
- **Inputs.** Target role + user answers. **Outputs.** A persisted `AssessmentResult` and a
  roadmap signal.
- **Internal logic / algorithms.**
  1. **Coverage allocation.** `StageAllocator.allocate_stage_one` selects subskills from the
     role graph (`role_graph_data.py`, curated-v3 taxonomy) using coverage blueprints.
  2. **Scenario RAG few-shots.** `ScenarioRetriever.retrieve_for_blueprint()` queries the
     `assessment_scenarios` Chroma collection filtered by `role_key`, competency, type, and
     stage; it never raises (returns `[]` on failure).
  3. **Generation.** `AssessmentAIService.generate_stage_one` builds a prompt (static few-shots
     + retrieved scenarios) and requests structured JSON from Gemini; results are cached for
     7 days keyed by role + graph version + corpus version.
  4. **Gap analysis → Stage 2.** Stage 1 answers are scored, a gap profile is derived, and
     Stage 2 questions target the weakest dimensions.
  5. **Deterministic weighted scoring.** `AnswerScorer` produces per-dimension scores;
     `_weighted_overall` combines them using role-graph weights (validated to sum to 1.0),
     re-normalised over measured dimensions. **The LLM's self-reported score is discarded.**

```python
# Illustrative: deterministic roll-up (apps/assessments/ai_pipeline.py)
def _weighted_overall(dimension_scores, weights):
    measured = {d: s for d, s in dimension_scores.items() if d in weights}
    total_w = sum(weights[d] for d in measured) or 1.0
    return sum(measured[d] * weights[d] for d in measured) / total_w
```

- **Asynchrony.** Generation and evaluation run as Celery tasks (`generate_stage_one`,
  `process_stage_one_submission`, `process_final_evaluation`); the API returns `202 Accepted`
  and the client polls `GET /assessment/{id}/result/`.

**Figure 4.5 — Two-stage assessment pipeline.** *(Use the §3.5.3 DFD L2 as the figure source.)*

### 4.2.4 Roadmaps module

- **Purpose.** Generate personalised learning roadmaps and track progress.
- **Models.** `RoadmapTemplate`, `Roadmap` (links to `AssessmentResult`), `RoadmapPhase`,
  `RoadmapMilestone`, `RoadmapCourse` (with `match_score`, `recommendation_reason`).
- **Inputs.** Assessment result + target role/level + weekly hours. **Outputs.** A
  phase→milestone→course hierarchy.
- **Internal logic.** `RoadmapAssembler` retrieves roadmap.sh structure chunks from the
  `career_knowledge` collection (`where={"source":"roadmap.sh"}`, top-k = 5), normalises them
  into a 3-phase blueprint (`RoadmapPathNormalizer`), reorders by assessment gaps, optionally
  applies an O*NET crosswalk (backend PoC, backend role), and matches courses via
  `CourseIndex.search`. `RoadmapAIService` rewrites only the phase *copy* with Gemini while
  preserving structure. Heuristic sizing uses `BASE_HOURS_BY_LEVEL`,
  `PHASE_WEEK_SPLIT=(0.30,0.40,0.30)`, `MIN_PLAN_WEEKS=8`. A deterministic template is used if
  retrieval returns `[]`.

### 4.2.5 Jobs module

- **Purpose.** Job search, transparent skill matching, and learned re-ranking, localised to
  Egypt.
- **Models.** `Job` (24-hour cache TTL), `JobPlatform`, `JobSkill`, `SavedJob`,
  `MarketInsight`, `SkillDemand`.
- **Inputs.** User skill profile + search filters. **Outputs.** Ranked jobs with a match score
  and explanation.
- **Internal logic / algorithms.**
  - `JobService.compute_match_score` computes a transparent skill-overlap percentage (the
    user-facing `match_score`).
  - `JobRankingIntegration.rank_user_jobs` calls the `ai-models` `JobRanker` (LightGBM
    `lambdarank`) which *re-orders* candidates using five features: `skill_embedding_cosine`,
    `required_skill_overlap_ratio`, `experience_level_delta`, `job_freshness_score`,
    `location_match`. The displayed `match_score` remains the overlap percentage for
    interpretability; only the ordering changes.
  - Ingestion utilities (`ingest/wuzzuf.py`, `ingest/persist.py`) and management commands
    (`ingest_jobs_wuzzuf`, `ingest_jobs_csv`, `train_job_ranker`) populate and train.
- **API.** `GET /jobs/search/`, `GET /jobs/match/`, saved-jobs CRUD and toggle.

### 4.2.6 Advisory module

- **Purpose.** Retrieval-grounded conversational career advice with citations and scope
  control.
- **Models.** `Conversation` (context snapshot, token totals), `Message` (role, content,
  `context_used`, `model_used`, `tokens_used`, optional `user_rating`).
- **Inputs.** A user message + conversation history. **Outputs.** A grounded assistant reply
  with structured citations (source, url, section, excerpt, confidence tier).
- **Internal logic.** `LLMAdvisoryService` classifies the message scope (`scope_rules.py`),
  retrieves context via the hybrid `rag.retriever.retrieve_context` (dense + BM25 + RRF +
  cross-encoder rerank + abstention), assembles a prompt with the user profile and last turns,
  and generates with `GemmaClient`. Out-of-scope queries are redirected; weak-evidence queries
  abstain.
- **API.** `POST /advisory/chat/`, conversation history endpoints.

### 4.2.7 Supporting modules

- **Courses.** `Course`/`CoursePlatform`/`CourseSkill`; a `courses` Chroma collection
  (`course_index.py`) powers semantic course matching during roadmap generation; search and
  recommendation endpoints.
- **Progress.** `UserProgress`, `CourseCompletion`, `MilestoneAchievement`, `TimeLog`;
  `ProgressService` computes streaks and completion stats and emits notification signals.
- **Notifications.** `Notification`, `NotificationPreference`; full in-app CRUD, mark-read,
  filtered lists, and per-type/quiet-hours preferences. Email/push delivery is stubbed
  (signals only) — documented as future work.
- **Career Tools.** `Resume`, `Portfolio`; CRUD plus `generate` and `optimize_ats` endpoints
  that return structured JSON (binary PDF/DOCX export deferred).

---

## 4.3 Database Design

**What to write.** Explain the schema, the ERD, the principal tables, and their relationships.
**(≈3 pages.)**

### 4.3.1 Schema principles

- Every table has a **UUID** primary key and soft-delete columns via `BaseModel`.
- JSON fields store semi-structured AI payloads (questions, responses, skill_scores,
  ai_insights) to avoid premature schema rigidity while keeping relational integrity for core
  entities.
- Foreign keys enforce ownership (`User`) and module links (`AssessmentResult → Roadmap`,
  `RoadmapCourse → Course`).

### 4.3.2 ERD guidance

**Figure 4.1 — Entity-Relationship Diagram.** *What must appear:* `User` at the centre with
1-to-many edges to `UserSkill`, `Assessment`, `Roadmap`, `SavedJob`, `Conversation`,
`UserProgress`, `Resume`, `Portfolio`; `Assessment 1—1 AssessmentResult`; `Roadmap 1—*
RoadmapPhase 1—* RoadmapMilestone 1—* RoadmapCourse *—1 Course`; `Job 1—* JobSkill *—1 Skill`;
`Course *—* Skill` through `CourseSkill`; `Conversation 1—* Message`. Mark soft-delete and
UUID PKs in a legend.

### 4.3.3 Principal tables

**Table 4.3 — Selected core tables.**

| Table | Key columns | Relationships |
|-------|-------------|---------------|
| `users_user` | id (UUID), email, username, full_name, is_premium | 1—* user_skills, assessments, roadmaps |
| `users_userskill` | id, proficiency_level, years_of_experience, source | *—1 user, *—1 skill |
| `assessments_assessment` | id, target_career, stage, questions (JSON), responses (JSON), ai_processing_status | *—1 user; 1—1 result |
| `assessments_assessmentresult` | id, overall_score, skill_scores (JSON), recommended_careers (JSON) | 1—1 assessment |
| `roadmaps_roadmap` | id, target_career, completion_percentage, status | *—1 user; *—1 assessment_result; 1—* phases |
| `roadmaps_roadmapmilestone` | id, milestone_type, order, skills (JSON) | *—1 phase; 1—* roadmap_courses |
| `jobs_job` | id, title, company_name, location, salary_*, cache_expires_at | 1—* job_skills |
| `jobs_savedjob` | id, notes | *—1 user, *—1 job |
| `advisory_message` | id, role, content, context_used (JSON), tokens_used | *—1 conversation |

---

## 4.4 API Design

**What to write.** Explain the endpoint design, request/response flow, and authentication.
**(≈3 pages.)**

### 4.4.1 Conventions

- All endpoints are namespaced under **`/api/v1/`** and documented via drf-spectacular
  (`/api/schema/swagger-ui/`).
- Resources are exposed as DRF ViewSets with `PageNumberPagination` (page size 20).
- The default permission is `IsAuthenticated`; auth endpoints are public.

### 4.4.2 Representative endpoints

**Table 4.4 — Representative API endpoints.**

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | `/users/auth/register/` | Create account + issue JWT | Public |
| POST | `/users/auth/login/` | Login + issue JWT | Public |
| POST | `/users/auth/refresh/` | Rotate access token | Public (valid refresh) |
| GET/PUT/PATCH | `/users/me/` | Profile | JWT |
| POST | `/assessment/` | Create assessment (enqueues generation) | JWT |
| POST | `/assessment/{id}/submit/` | Submit answers (202) | JWT |
| GET | `/assessment/{id}/result/` | Poll result (202/200) | JWT |
| POST | `/roadmap/` | Generate AI roadmap | JWT |
| PATCH | `/roadmap/{id}/progress/` | Update progress | JWT |
| GET | `/jobs/match/` | Skill-matched + ranked jobs | JWT |
| POST | `/advisory/chat/` | Grounded chat reply | JWT |
| GET | `/notifications/` | List notifications | JWT |

### 4.4.3 Request/response flow

**Figure 4.2 — API request lifecycle.** Describe: SPA attaches `Authorization: Bearer
<access>`; DRF authenticates the JWT; the viewset delegates to a service; for AI endpoints the
service enqueues a Celery task and returns `202`; the SPA polls for the result. On `401`, the
SPA calls `/users/auth/refresh/` and retries transparently; on refresh failure it redirects to
`/login`.

### 4.4.4 Authentication

Stateless **Simple JWT (HS256)**: access tokens live 1 hour, refresh tokens 7 days, with
rotation and blacklisting after rotation. The user id is carried in the `user_id` claim.

---

## 4.5 Security Implementation

**What to write.** Cover authentication, authorization, encryption, and validation. **(≈2
pages.)**

- **Authentication.** JWT bearer tokens as above; refresh-token rotation and blacklist limit
  replay.
- **Authorization.** `IsAuthenticated` by default; object-level ownership enforced in querysets
  (users only see their own assessments, roadmaps, conversations, saved jobs). Admin-only
  content management via Django admin.
- **Encryption / transport.** HTTPS in production; secrets via environment variables; the
  database connection uses SSL in production settings.
- **Input validation.** DRF serializers validate and coerce all inputs; AI outputs are
  re-validated and repaired (`ai_validation.py`) before persistence, preventing malformed-LLM
  data from entering the database.
- **Abuse protection.** Custom throttles cap costly AI endpoints (`ai_burst` 3/min,
  `ai_sustained` 20/hour); CORS is restricted in production.
- **Data protection.** Soft deletion preserves auditability; UUID keys avoid enumerable
  identifiers.

**Table 4.5 — Security controls mapped to threats.**

| Threat | Control |
|--------|---------|
| Credential replay | JWT rotation + blacklist |
| Unauthorised data access | Per-user querysets, `IsAuthenticated` |
| Injection / malformed input | DRF validation, ORM parameterisation |
| LLM cost abuse / DoS | AI throttles |
| Enumeration | UUID primary keys |
| Data exposure in transit | HTTPS / SSL DB |

---

## 4.6 User Interface

**What to write.** Explain design choices, the user workflow, and the principal screens; list
screenshots to capture. **(≈3 pages.)**

### 4.6.1 Design choices

The SPA uses a **"Career Atlas"** visual language built on shadcn/ui + Radix primitives and
Tailwind, with Space Grotesk/IBM Plex Sans typography and an orange/teal palette. Every route
is **lazy-loaded**; protected routes are wrapped by `ProtectedRoute` and the authenticated
`MainLayout` (primary navigation, notifications badge, user menu). State feedback
(loading/empty/error) is standardised via shared `StatePanel`/`PageShell` components.

### 4.6.2 User workflow

Landing → Register/Login → Dashboard → Assessment (pick role → session → results) → Roadmap →
Jobs/Saved → Advisor → Profile/Settings/Notifications. Authentication tokens persist in
`localStorage` and refresh transparently.

### 4.6.3 Principal screens and screenshots to capture

**Table 4.6 — Screens and recommended screenshots.**

| # | Screen | Route | Screenshot caption |
|---|--------|-------|--------------------|
| S1 | Landing | `/` | "Figure 4.6 — Landing page presenting the Sha8lny value proposition." |
| S2 | Login / Register | `/login`, `/register` | "Figure 4.7 — Authentication screens." |
| S3 | Dashboard | `/dashboard` | "Figure 4.8 — Career-atlas dashboard with progress snapshot." |
| S4 | Assessment picker | `/assessment` | "Figure 4.9 — Career-path selection across eight roles." |
| S5 | Assessment session | `/assessment/session/:id` | "Figure 4.10 — Adaptive question card with progress rail." |
| S6 | Assessment results | `/assessment/results/:id` | "Figure 4.11 — Competency result with strengths and gaps." |
| S7 | Roadmap | `/roadmap` | "Figure 4.12 — Personalised roadmap with AI source panel." |
| S8 | Jobs | `/jobs` | "Figure 4.13 — Skill-matched jobs with match explanation." |
| S9 | Advisor | `/advisor` | "Figure 4.14 — Grounded advisor chat showing cited sources." |
| S10 | Profile/Settings | `/profile`, `/settings` | "Figure 4.15 — Profile, skills, and preferences." |

---

## 4.7 Summary

Conclude: "All modules of §3 are implemented, JWT-secured, documented via OpenAPI, and
exercised by an automated test suite (Chapter 5)."

---

## Chapter 4 — Visual assets summary

| # | Type | Caption | Placement |
|---|------|---------|-----------|
| Figure 4.1 | ERD | "Entity-Relationship Diagram of the Sha8lny database." | §4.3.2 |
| Figure 4.2 | Sequence/flow | "API request lifecycle with JWT and async AI." | §4.4.3 |
| Figure 4.5 | Pipeline | "Two-stage assessment pipeline." | §4.2.3 |
| Figures 4.6–4.15 | Screenshots | UI screens (see Table 4.6). | §4.6.3 |
| Tables 4.1–4.6 | Tables | Hardware, stack, tables, endpoints, security, screens. | throughout |

**Citations used:** [4], [5], [7], [9], [12], [14], [17], [21].
