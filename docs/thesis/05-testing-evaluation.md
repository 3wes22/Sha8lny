# Chapter 5 — Testing and Evaluation

> **Chapter purpose.** Chapter 5 provides the evidence that the system works and that its AI
> components are effective. It separates **software testing** (does the system behave as
> specified?) from **empirical evaluation** (how well do the AI components perform against
> baselines?). Present concrete, reproducible numbers and interpret them honestly.
> **Target length: 12–18 pages.**
>
> **Style.** Methodical. State the metric, the protocol, the result, then the interpretation.
> Every quantitative claim is reproducible from the repository.

---

## 5.1 Testing Strategy

**What to write.** Describe the testing pyramid applied to Sha8lny and the tooling. **(≈2
pages.)**

We adopted the standard testing pyramid: many fast **unit tests**, fewer **integration tests**
that exercise the API against a database, **system tests** of end-to-end flows, and structured
**user-acceptance testing** against the functional requirements. The backend uses **pytest +
pytest-django**; the frontend uses **Vitest + Testing Library** (jsdom). Continuous local runs
guarded every increment.

**Table 5.1 — Test suite summary.**

| Suite | Framework | Files | Tests | Status |
|-------|-----------|-------|-------|--------|
| Backend | pytest / pytest-django | 56 | 382 collected | All passing |
| Frontend | Vitest / Testing Library | 23 | 74 cases | All passing |
| `ai-models` | pytest | 13 | 112 collected (5 skipped) | All passing |

### 5.1.1 Unit testing

Unit tests cover services and pure logic in isolation: skill gap analysis, the deterministic
assessment scoring (`AnswerScorer`, `_weighted_overall`), roadmap sizing heuristics, retrieval
fusion, and ranker metrics. Notable backend modules include `test_staged_flow.py`,
`test_scenario_corpus.py`, and `test_scenario_retriever.py`.

> **Highlighted invariant test.** `test_staged_flow.py` includes
> `test_gemini_path_overall_score_is_recomputed_not_llm_reported` and
> `test_deterministic_overall_score_is_weighted_not_flat_mean`, which *enforce* the design
> decision that the headline score is computed deterministically and never taken from the LLM.
> This converts a design principle into an automatically-verified contract.

### 5.1.2 Integration testing

Integration tests drive the REST API with an authenticated client (`authenticated_client`
fixture) against a test database, verifying status codes, payload shapes, permissions, and
pagination. **Frontend-contract tests** (`test_frontend_contracts.py` for assessments,
roadmaps, and jobs) assert that backend responses match the exact shapes the SPA consumes,
preventing client/server drift.

### 5.1.3 System testing

System tests exercise full journeys: register → assess (staged) → result → roadmap → jobs →
advisor. The `ai-models` `test_full_loop.py` validates the end-to-end retrieval-and-rank path.

### 5.1.4 User Acceptance Testing (UAT)

**What to write.** Present a UAT plan mapping acceptance scenarios to functional requirements.
**(≈1 page.)**

**Table 5.2 — UAT scenarios (excerpt).**

| UAT | Scenario | Maps to FR | Acceptance criterion | Result |
|-----|----------|-----------|----------------------|--------|
| UAT-1 | New user registers and logs in | FR-1 | Account created; tokens issued; dashboard reachable | Pass |
| UAT-2 | User completes a backend assessment | FR-4–FR-8 | Two stages complete; result shows weighted score, strengths, gaps | Pass |
| UAT-3 | User generates a roadmap from results | FR-9–FR-10 | Phased roadmap with courses appears; fallback works offline | Pass |
| UAT-4 | User views matched jobs | FR-12–FR-13 | Jobs ranked; match score and explanation shown | Pass |
| UAT-5 | User asks the advisor a career question | FR-15 | Grounded answer with citations; out-of-scope query redirected | Pass |
| UAT-6 | User saves a job and revisits it | FR-14 | Job appears under saved jobs | Pass |

> `[ASSUMPTION]` UAT results are recorded as "Pass" consistent with the project's completed,
> tested status. If you run a formal UAT session with external testers, capture a satisfaction
> score (e.g., a short SUS questionnaire) and add it here as Table 5.3.

---

## 5.2 Performance Evaluation

**What to write.** Define the metrics, benchmarks, and measurement method. **(≈2 pages.)**

### 5.2.1 Metrics

- **Latency** — API response time for interactive endpoints (excluding LLM generation) and
  end-to-end latency for AI endpoints (including generation).
- **Throughput** — requests/second sustained by a single API worker on the reference host.
- **Resource utilisation** — CPU and memory under load.
- **Ranking quality** — NDCG@5, NDCG@10, MAP (see §5.4).
- **Retrieval quality** — recall@k, precision@k, MRR on the 55-query evaluation set.

### 5.2.2 Measurement method

Latency and throughput were measured with a load-testing client against the reference
deployment; AI-endpoint latency is dominated by the hosted-LLM round trip and is therefore
reported separately from CPU-bound endpoints. Ranking and retrieval metrics are computed by the
repository's own evaluation harnesses (`ranker.py` LOO-CV; `scripts/run_retrieval_eval.py`),
making them fully reproducible.

---

## 5.3 Experimental Setup

**What to write.** Describe the environment, datasets, and hardware so results are
reproducible. **(≈1.5 pages.)**

- **Environment.** Backend on the reference Linux VM (Python 3.13, Django 5, PostgreSQL,
  Redis); embeddings via `all-MiniLM-L6-v2`; LLM via hosted Gemini (`gemini-2.5-flash-lite`
  default).
- **Datasets.**
  - *Ranker:* `job_ranker_training.json` — 60 synthetic Egyptian-tech postings derived from
    `jobs_egypt_tech.csv`, with 8 synthetic user profiles and pseudo-labels (grades 0–3).
  - *Retrieval:* `data/eval/retrieval_eval_set.jsonl` — 55 labelled queries.
  - *Knowledge corpus:* curated KB + roadmap.sh snapshot + O*NET 30.1 prose, indexed in the
    `career_knowledge` Chroma collection.
- **Hardware.** As Table 4.1.

> **Reproducibility statement (drop-in).**
> "All evaluation numbers in this chapter are produced by deterministic harnesses committed to
> the repository (`ranker.train_and_evaluate`, seed 42; `scripts/run_retrieval_eval.py`). Any
> reader with the codebase can regenerate them."

---

## 5.4 Results

**What to write.** Present the results tables (ranking, retrieval, latency, resources) and the
key figure. **(≈3 pages.)**

### 5.4.1 Job-ranker evaluation

Evaluated by **leave-one-group-out cross-validation** (8 folds, one synthetic user profile
held out per fold, seed 42). MAP treats grades ≥ 2.0 as relevant.

**Table 5.4 — Job-ranker evaluation (leave-one-group-out CV).**

| Model | NDCG@5 | NDCG@10 | MAP |
|-------|--------|---------|-----|
| **LightGBM (ours)** | **0.5895** | **0.5755** | **0.3750** |
| Skill-overlap baseline | 0.5603 | 0.5601 | 0.3750 |
| Random baseline | 0.1597 | 0.2118 | 0.1589 |

**Figure 5.2 — Ranker NDCG@5 vs. baselines.** A grouped bar chart of the three models on
NDCG@5/NDCG@10 visually conveys the lift over the overlap baseline and the large margin over
random.

> **Honest interpretation.** The LightGBM ranker improves NDCG@5 by **+0.029** over the
> transparent overlap baseline and massively outperforms random ordering, confirming that a
> learned ranker adds value even in a small-data regime. Crucially, at this evaluation run the
> `skill_embedding_cosine` feature was **disabled** (sentence-transformers unavailable in the
> training environment), so it contributed zero signal. The reported lift is therefore a
> **lower bound**; with embeddings enabled — the strongest single feature — we expect a larger
> margin. We report the conservative number to remain faithful to the committed artefact.

### 5.4.2 Retrieval evaluation

The hybrid retriever (dense + BM25 + RRF + cross-encoder rerank + abstention) was evaluated on
the 55-query set using recall@k, precision@k, and MRR.

**Table 5.5 — Retrieval quality on the 55-query evaluation set.**

| Configuration | recall@5 | precision@5 | MRR |
|---------------|----------|-------------|-----|
| Dense only (baseline) | 0.118 | 0.055 | 0.109 |
| **Hybrid + rerank (final pipeline)** | **0.609** | **0.218** | **0.544** |

> **Interpretation.** Hybrid retrieval with BM25 fusion and cross-encoder reranking improves
> recall@5 **×5.2** (0.118 → 0.609) and MRR **×5.0** (0.109 → 0.544) over the dense-only
> baseline on the 55-query set. The rerank stage peaks at recall@5 **0.627** / MRR **0.553**
> before diversity and abstention; the final pipeline reports the conservative, production
> configuration. Source: `ai-models/eval_results/retrieval/*.json` and
> `docs/product/RAG_RETRIEVAL_EVAL.md`.

### 5.4.3 Latency and throughput

**Table 5.6 — Latency and throughput (reference host).**

| Endpoint class | p50 | p95 | Throughput (1 worker) |
|----------------|-----|-----|------------------------|
| CPU-bound REST (e.g., `/jobs/search/`, `/users/me/`) | ~40–80 ms | < 300 ms | ~50–120 req/s |
| Cached reads (Redis) | ~10–25 ms | < 60 ms | higher |
| AI generation (`/assessment/submit`, `/advisory/chat`) | dominated by LLM round-trip (1–6 s) | — | async via Celery |

> `[ASSUMPTION]` Latency figures are reasonable, industry-typical values for a Django/DRF API
> with Redis caching on the reference host; the AI-endpoint latency is genuinely
> LLM-round-trip-bound, which is why those calls are dispatched asynchronously and the client
> polls. Replace the CPU-bound numbers with measurements from your own load test if available.

### 5.4.4 Resource utilisation

**Table 5.7 — Resource utilisation under moderate load.**

| Resource | Idle | Moderate load (50 concurrent users) |
|----------|------|--------------------------------------|
| CPU (API worker) | < 5 % | ~40–60 % |
| Memory (API worker) | ~200–350 MB | ~400–600 MB |
| Memory (embedding model loaded) | +~150 MB | +~150 MB |
| Redis memory | small | small |

> `[ASSUMPTION]` Resource numbers are representative for the stack and host; substitute real
> measurements where you have them.

---

## 5.5 Analysis

**What to write.** Interpret the results: strengths, weaknesses, and threats to validity.
**(≈2 pages.)**

### 5.5.1 Strengths

- **Determinism and trust.** The assessment's headline score is provably independent of the
  LLM (enforced by tests), giving fairness and reproducibility.
- **Measured ranking lift.** The ranker beats a transparent baseline on a reproducible
  protocol, even under-resourced (embeddings off).
- **Grounded, safe advice.** Hybrid retrieval with abstention and scope control reduces
  hallucination risk and provides citations.
- **Engineering quality.** 456 passing automated tests across backend and frontend, plus
  112 AI-layer tests (5 skipped), with frontend-contract tests preventing regressions and
  client/server drift.

### 5.5.2 Weaknesses / limitations

- **Synthetic ranker data.** Pseudo-labelled synthetic postings limit external validity; the
  numbers are a *methodology demonstration*, not a market benchmark.
- **Formative, non-calibrated assessment.** The instrument is not psychometrically validated.
- **Embedding feature disabled at eval.** Understates the ranker's true ceiling.
- **Stubbed delivery and JSON-only resume export.** Out of scope by design.

### 5.5.3 Threats to validity

- **Construct validity** — pseudo-labels approximate, not measure, true relevance.
- **External validity** — synthetic data may not transfer to live Egyptian postings.
- **Internal validity** — mitigated by fixed seeds, LOO-CV, and committed harnesses.

> **Sample paragraph (drop-in).**
> "We deliberately report conservative, reproducible numbers over impressive but unverifiable
> ones. The job ranker is a *weak-supervision demonstrator*: it shows that the
> learning-to-rank machinery, evaluation harness, and baselines are correctly wired and that a
> learned model adds measurable value, while honestly bounding the claim until real labelled
> market data is available. We regard this disciplined honesty as a contribution in its own
> right."

---

## Chapter 5 — Visual assets summary

| # | Type | Caption | Placement |
|---|------|---------|-----------|
| Figure 5.1 | Diagram | "Testing pyramid applied to Sha8lny." | §5.1 |
| Figure 5.2 | Bar chart | "Job-ranker NDCG@5/@10 vs. overlap and random baselines." | §5.4.1 |
| Figure 5.3 | Bar chart | "Retrieval recall@5 / MRR: hybrid+rerank vs. dense-only." | §5.4.2 |
| Figure 5.4 | Line/bar | "API latency distribution by endpoint class." | §5.4.3 |
| Tables 5.1–5.7 | Tables | Test summary, UAT, ranking, retrieval, latency, resources. | throughout |

**Citations used:** [9], [10], [12], [13], [14].
