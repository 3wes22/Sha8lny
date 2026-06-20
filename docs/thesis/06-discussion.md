# Chapter 6 — Discussion

> **Chapter purpose.** Chapter 6 steps back from raw results to interpret them. It answers the
> research questions, validates the contributions, compares the system with the literature,
> reflects on lessons learned and trade-offs, and discusses practical implications. It is the
> chapter where you demonstrate *insight*, not just output. **Target length: 6–10 pages.**
>
> **Style.** Reflective but evidence-anchored. Tie every claim back to a result in Chapter 5 or
> a design decision in Chapter 3.

---

## 6.1 Summary of Findings

**What to write.** A concise synthesis of what the evaluation established. **(≈1 page.)**

The evaluation established four findings. First, the **two-stage assessment** produces
role-aware questions across all eight roles while computing a headline score *deterministically*
— a property enforced by automated tests, not merely asserted. Second, the **learning-to-rank
job ranker** improves ordering over a transparent skill-overlap baseline (NDCG@5 0.5895 vs.
0.5603) and dwarfs random ordering, even with its strongest feature disabled. Third, the
**hybrid RAG pipeline** retrieves and grounds answers with citations and safely abstains when
evidence is weak, consistent with retrieval best practice. Fourth, the **full-stack system** is
secure, documented, and protected by 456 automated application-stack tests, demonstrating that probabilistic AI
can be embedded inside a dependable, deterministic product.

---

## 6.2 Answering the Research Questions

**What to write.** Address each RQ from §1.6 directly, citing the evidence. **(≈2 pages.)**

**RQ1 — Adaptive, trustworthy LLM assessment.**
We answer affirmatively. The LLM generates adaptive, role-aware items (grounded by scenario
RAG few-shots), but the score is recomputed deterministically from per-dimension evidence using
role-graph weights. The invariant test
`test_gemini_path_overall_score_is_recomputed_not_llm_reported` proves the LLM's self-reported
score is never used. Thus adaptivity and trustworthiness coexist: *the model proposes, the
deterministic engine disposes.*

**RQ2 — RAG effectiveness for grounding.**
We answer affirmatively with a caveat. The hybrid retriever (dense + BM25 + RRF + reranking +
abstention) grounds both roadmaps and advice, returns citations with confidence tiers, and is
evaluated on a 55-query labelled set. Effectiveness is bounded by corpus coverage and the
restrictive licence of the roadmap.sh content (dev-only), which constrains production
deployment until replaced.

**RQ3 — Learning-to-rank improvement, measured reproducibly.**
We answer affirmatively, conservatively. Under leave-one-group-out CV (seed 42), LightGBM beats
the overlap baseline on NDCG. Because this is reproducible from a committed harness and the
embedding feature was disabled at the run, the demonstrated lift is a lower bound — the claim is
*honest and verifiable* rather than inflated.

**RQ4 — Architectural patterns for a secure, maintainable, testable AI system.**
We identify and validate four: (a) the **modular monolith** for cohesive boundaries with simple
deployment; (b) a **service layer** isolating business logic from views; (c) **deterministic
orchestration with fallbacks** wrapping every AI call; and (d) **contract tests** keeping the
client and server aligned. Together these yielded a 456-test application suite (382 backend +
74 frontend) with no regressions across
feature increments.

---

## 6.3 Validation of Contributions

**What to write.** Revisit C1–C6 from §1.7 and show each was delivered. **(≈1 page.)**

**Table 6.1 — Contribution validation.**

| # | Contribution | Evidence |
|---|--------------|----------|
| C1 | Deterministic orchestration of probabilistic AI | Invariant tests; recomputed scores; fallbacks throughout |
| C2 | Reproducible evaluation methodology | LOO-CV ranker harness + 55-query retrieval set, committed and seeded |
| C3 | Hybrid RAG pipeline | `retriever.py` (dense+BM25+RRF+rerank+abstention) integrated in advisory + assessment |
| C4 | Two-stage adaptive assessment engine | `StageAllocator`/`AnswerScorer`/role graph across 8 roles |
| C5 | Modular-monolith full-stack system | Django REST + React/TS + `ai-models`; JWT; OpenAPI; 456 app-stack tests |
| C6 | Egypt-localised integrated platform | Egypt corpus/job fixtures/advisor persona; one shared competency profile |

---

## 6.4 Comparison with the Literature

**What to write.** Position the achieved system against the related work of Chapter 2.
**(≈1.5 pages.)**

Unlike opaque industrial talent matchers [19], Sha8lny privileges **explainability and
locality**, retaining a transparent overlap score as the user-facing metric. Unlike
open-domain RAG [7], our retriever adds **scope control and source-credibility tiers** suited to
a career advisor. Unlike calibrated CAT instruments [15], our assessment is **formative** but
**dynamic and role-aware**, trading psychometric calibration for adaptivity and breadth. And
unlike the global tools surveyed, Sha8lny is **integrated around one competency profile** and
**localised to Egypt** — the precise gap identified in Table 2.2. Where prior work optimised a
single component, our contribution is the *disciplined composition* of components into a
coherent, evaluable whole.

---

## 6.5 Lessons Learned

**What to write.** Honest reflections that show maturity. **(≈1 page.)**

- **Treat the LLM as untrusted.** The most valuable architectural decision was to never trust
  LLM output for scores or facts without deterministic recomputation or retrieval grounding.
- **Evaluation discipline beats demo polish.** Committing seeded, baseline-compared harnesses
  forced honest claims and caught silent regressions (e.g., the disabled embedding feature was
  *visible* precisely because the eval reported it).
- **Contracts prevent drift.** Frontend-contract tests eliminated a whole class of
  integration bugs between the SPA and the API.
- **Fallbacks are features.** Deterministic templates and graceful retrieval failure (`[]`)
  turned AI unreliability from a crash risk into a degraded-but-working path.
- **Licensing matters early.** Vendoring roadmap.sh content was expedient for development but
  is a compliance risk for release — a lesson in treating data provenance as a first-class
  concern.

---

## 6.6 Design Trade-offs Revisited

**What to write.** Reflect on the trade-offs from Table 3.3 with hindsight. **(≈1 page.)**

- **Modular monolith vs. microservices.** Simplicity and ACID transactions paid off for a
  student team; the clean module boundaries leave a credible path to later extraction.
- **Hosted Gemini vs. local-only.** Hosted generation gave reliable demos at the cost of an
  external dependency and per-call latency; the Ollama fallback preserves an offline path.
- **Determinism vs. fluency.** Discarding the LLM's score sacrificed a little narrative
  fluency for fairness and reproducibility — the correct trade for an assessment tool.
- **Explainable overlap score vs. pure learned ranking.** Showing the interpretable score
  while learning the order balances user trust against ranking quality.

---

## 6.7 Practical Implications

**What to write.** What the system means for users, employers, and educators. **(≈0.5 page.)**

For **learners**, Sha8lny compresses an unguided search into a measured, planned journey. For
**employers**, better-prepared, skill-profiled candidates reduce hiring friction. For
**educators and policymakers**, the platform's competency data could, at scale and with
consent, illuminate the very skills-mismatch it was built to address — turning a guidance tool
into a source of labour-market insight.

---

## Chapter 6 — Visual assets summary

| # | Type | Caption | Placement |
|---|------|---------|-----------|
| Table 6.1 | Table | "Validation of contributions against evidence." | §6.3 |
| Figure 6.1 | Diagram | "Sha8lny positioned against prior work on explainability, locality, and integration." | §6.4 |

**Citations used:** [7], [15], [19].
