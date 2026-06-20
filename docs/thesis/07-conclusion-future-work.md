# Chapter 7 — Conclusion and Future Work

> **Chapter purpose.** Chapter 7 closes the thesis. It restates what was achieved against the
> objectives, distils the main findings and contributions, and charts a credible roadmap of
> future work. It should leave the examiner with a clear sense of completion and forward
> momentum. **Target length: 5–8 pages.**
>
> **Style.** Confident and concise. No new results, no new citations of substance (a closing
> reference is acceptable). Mirror the objectives of §1.4 explicitly.

---

## 7.1 Conclusion

**What to write.** Summarise the problem, the solution, and the evidence; then map each
objective to its outcome. **(≈2 pages.)**

This thesis set out to address a concrete, locally-felt problem: early-career technologists in
the Egyptian market lack an integrated, intelligent way to discover a career path, measure their
competencies, plan their learning, find suitable jobs, and obtain trustworthy advice. We
designed, implemented, and evaluated **Sha8lny**, a full-stack, AI-powered career-empowerment
platform that unifies these four services around a single competency profile and grounds its
intelligence in a locally-curated knowledge corpus.

### 7.1.1 Objectives achieved

**Table 7.1 — Objectives and outcomes.**

| # | Objective (from §1.4) | Outcome |
|---|------------------------|---------|
| O1 | Two-stage adaptive assessment, 8 roles, deterministic scoring | Achieved; score recomputed deterministically (test-enforced) |
| O2 | Personalised, corpus-grounded roadmaps | Achieved; RAG-assembled phases/milestones/courses with deterministic fallback |
| O3 | Explainable, local job matching | Achieved; overlap score + LightGBM rerank + match explanation |
| O4 | Retrieval-grounded advisor | Achieved; cited answers with scope control and abstention |
| O5 | Secure, maintainable, well-tested system | Achieved; JWT, OpenAPI, 456 passing tests (382 backend + 74 frontend) |
| O6 | Reproducible AI evaluation | Achieved; LOO-CV ranker + 55-query retrieval set |

### 7.1.2 Main findings

The central finding is that **probabilistic AI can be made dependable through deterministic
engineering**: by treating the language model as one untrusted component — recomputing scores,
grounding facts in retrieval, validating outputs, and always providing a fallback — a student
team built an integrated platform that is adaptive yet reproducible. Empirically, a learned
ranker improved job ordering over a transparent baseline under a reproducible protocol, and a
hybrid retrieval pipeline grounded advice with citations and safe abstention.

### 7.1.3 Contributions restated

Sha8lny contributes (academically) a reference pattern for deterministic AI orchestration and a
reproducible small-data evaluation methodology; (technically) a working hybrid RAG pipeline and
a two-stage adaptive assessment engine within a modular-monolith full-stack system; and
(practically) an Egypt-localised platform integrating assessment, roadmaps, jobs, and advice.

> **Drop-in closing paragraph.**
> "Sha8lny demonstrates that the value of modern AI in a product lies less in any single model
> than in the engineering discipline that surrounds it. By grounding generation in retrieval,
> recomputing every consequential number deterministically, and evaluating honestly against
> baselines, we transformed a set of probabilistic components into a coherent, trustworthy
> guide for young Egyptians entering the technology profession."

---

## 7.2 Future Work

**What to write.** Organise into short-term improvements, long-term improvements, and open
research opportunities. Each item should be specific and motivated by a limitation from
Chapters 5–6. **(≈3 pages.)**

### 7.2.1 Short-term improvements (next 1–3 months)

1. **Real job-market data.** Replace synthetic fixtures with a live Wuzzuf/Bayt ingestion
   pipeline and retrain the ranker on real postings (ingestion scaffolding already exists),
   then re-run the LOO/holdout evaluation on genuine data.
2. **Re-enable and tune the embedding feature.** Ensure `sentence-transformers` is available in
   the training environment so `skill_embedding_cosine` contributes; report the updated lift.
3. **Adopt TanStack Query in the SPA.** The library is provisioned but feature pages still fetch
   imperatively; migrating to query hooks would add caching, retries, and background refresh.
4. **Resume/portfolio binary export.** Implement PDF/DOCX generation behind the existing
   structured endpoints.
5. **Notification delivery.** Wire the stubbed email/push channels to a provider, honouring the
   existing per-type and quiet-hours preferences.

### 7.2.2 Long-term improvements (3–12 months)

1. **Resolve content licensing.** Replace the personal-use roadmap.sh snapshot with an
   openly-licensed or first-party roadmap corpus to enable public release.
2. **Psychometric calibration.** Evolve the formative assessment toward a calibrated instrument
   (item-response theory) with piloted item banks.
3. **Native mobile clients** and offline-first support for low-connectivity users.
4. **Microservice extraction** of the AI workload if scale demands it, leveraging the existing
   clean module boundaries.
5. **Fine-tuned / local LLMs.** Mature the `ai-models/llm` path (LLaMA/Mistral with LoRA) for a
   cost-controlled, privacy-preserving self-hosted runtime.

### 7.2.3 Research opportunities

1. **Learning from implicit feedback.** Use real user interactions (applications, saves,
   completions) as relevance signals to move from weak supervision to genuine learning-to-rank.
2. **Longitudinal outcome study.** Measure whether platform guidance correlates with faster
   time-to-employment — turning the tool into an instrument for labour-market research.
3. **Bias and fairness auditing** of both the assessment scoring and the job ranker, with
   particular attention to gender and regional disparities in the Egyptian market.
4. **Retrieval evaluation at scale.** Expand the 55-query set into a larger, community-validated
   benchmark for Arabic/Egyptian career-domain retrieval.

**Table 7.2 — Future-work roadmap.**

| Horizon | Item | Motivating limitation |
|---------|------|------------------------|
| Short | Real job data + retrain | Synthetic ranker data (§5.5.2) |
| Short | Re-enable embeddings | Feature disabled at eval (§5.4.1) |
| Short | TanStack Query adoption | Imperative fetching (Ch. 4) |
| Long | Replace roadmap.sh corpus | Licensing risk (§6.5) |
| Long | Psychometric calibration | Formative-only assessment (§5.5.2) |
| Research | Implicit-feedback LTR | Pseudo-labels (§5.5.3) |
| Research | Fairness audit | Responsible-AI obligation |

---

## 7.3 Closing Remarks

A short, forward-looking paragraph: Sha8lny is both a working product and a methodological
statement about how to engineer trustworthy AI systems; its architecture and evaluation
discipline are designed to outlive any single model generation.

---

## Chapter 7 — Visual assets summary

| # | Type | Caption | Placement |
|---|------|---------|-----------|
| Table 7.1 | Table | "Objectives and outcomes." | §7.1.1 |
| Table 7.2 | Table | "Future-work roadmap mapped to limitations." | §7.2 |
| Figure 7.1 | Roadmap timeline | "Short-, long-term, and research future work." | §7.2 |
