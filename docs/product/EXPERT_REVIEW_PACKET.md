# Expert Review Packet — Open-Ended Assessment Items

**Purpose:** Validate Sha8lny's open-ended scoring against independent human
experts. Reviewers grade 15 open-ended items **blind** (the engine's scores are
withheld); we then compare human scores to the engine's `keyword_coverage` /
`llm_rubric` scores and report inter-rater agreement.

> **Developer action item:** Recruiting 3 reviewers and running the session is
> the developer's task. This packet is self-contained so reviewers need **no
> repo access**. Hand each reviewer this document + their rows of
> [`expert_review_scoring_sheet.csv`](expert_review_scoring_sheet.csv).

Related: [`ROLE_GRAPH_METHODOLOGY.md`](ROLE_GRAPH_METHODOLOGY.md),
[`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md) (C3, C11).

---

## Reviewer instructions

1. You will grade a subset of 15 short technical questions. For each, read the
   **question** and the **candidate answer**, then assign a **score from 1 to 5**.
2. Grade only the rows assigned to your reviewer id (`R1`, `R2`, or `R3`) in the
   scoring sheet. Items `OE01`–`OE05` are graded by **all three** reviewers
   (calibration / inter-rater block).
3. Do **not** confer with other reviewers before submitting. Add a one-line
   justification in the `notes` column.
4. You are grading **answer quality**, not writing style or length.

## Scoring rubric (1–5)

| Score | Meaning |
|---|---|
| 5 | Correct and complete — covers all key concepts; no misconceptions. |
| 4 | Mostly correct — covers the main concepts with a minor gap. |
| 3 | Partially correct — one key concept present; notable gaps. |
| 2 | Weak — tangential; misses the core idea. |
| 1 | Incorrect / off-topic, or reveals a clear misconception. |

## Items

> Candidate answers are sample responses to be graded. (In a live session the
> developer substitutes real candidate answers; the structure stays identical.)
> The engine's score for each item is intentionally **not shown**.

| ID | Role | Competency | Question (open-ended) |
|---|---|---|---|
| OE01 | backend | Service Decomposition | When splitting a monolith into services, how do you decide where the boundaries go, and why? |
| OE02 | backend | Relational Modeling | How would you model a many-to-many relationship, and what problems does that avoid? |
| OE03 | backend | HTTP API Design | How would you make a "create order" endpoint safe to retry, and what status codes would you return? |
| OE04 | frontend | useEffect Patterns | Why might a React effect read a stale value, and how do you fix it? |
| OE05 | frontend | Component Composition | When would you compose with `children` / render props instead of adding props or inheritance? |
| OE06 | data_science | Batch vs Streaming | For a fraud-scoring pipeline, what are the tradeoffs between batch and streaming, and which fits? |
| OE07 | data_science | Star Schema | When is a star schema preferable to a fully normalized model, and what do you trade away? |
| OE08 | machine_learning_engineer | Training/Serving Skew | How does training/serving skew arise, and how do you prevent it? |
| OE09 | machine_learning_engineer | Bias-Variance Tradeoff | How would you diagnose overfitting, and what would you change to address it? |
| OE10 | devops | Dockerfile Best Practices | How would you reduce a large production Docker image and speed up rebuilds? |
| OE11 | devops | IAM Least Privilege | How would you apply least privilege to a service that only reads one storage bucket? |
| OE12 | android | Optimistic Updates | How would you implement an optimistic "like", and what happens if the server call fails? |
| OE13 | fullstack | select_related / prefetch_related | How would you detect and fix N+1 queries in a Django list view? |
| OE14 | ui_ux_designer | Usability Testing | How would you run a session to find where users struggle in checkout? |
| OE15 | ui_ux_designer | Information Architecture | How would you validate that your navigation grouping matches users' expectations? |

## Expected-concept keys (for the organizer, not the reviewers)

These mirror each item's `expected_concepts`; reviewers grade holistically, not
by keyword.

- **OE01** bounded contexts / cohesion · coupling · business capability
- **OE02** join table · foreign keys · avoids update anomalies
- **OE03** idempotency · 201 Created · retry safety
- **OE04** closure captures binding · dependency array · recreate/cleanup
- **OE05** children / render prop · composition over inheritance · reuse
- **OE06** latency vs throughput · event-time · bounded vs unbounded
- **OE07** fewer joins · denormalization · query speed vs redundancy
- **OE08** feature parity · shared transformation · serve-time availability
- **OE09** train/val gap · regularization/data · capacity
- **OE10** multi-stage build · layer caching · slim base image
- **OE11** scoped permissions · read-only · minimal blast radius
- **OE12** update locally · reconcile on response · rollback on failure
- **OE13** select_related/prefetch_related · join vs batched query · query count
- **OE14** realistic tasks · observation · think-aloud
- **OE15** card sort · mental model · findability

## Assignment design (3 reviewers, 5-item overlap)

- **Overlap block (OE01–OE05):** graded by **R1, R2, R3** → 5 items × 3 = 15
  ratings, used to compute inter-rater agreement (e.g., Krippendorff's α / mean
  pairwise absolute difference).
- **Remaining (OE06–OE15):** each graded by **exactly 2** reviewers on a
  rotating R1R2 / R2R3 / R1R3 schedule.
- **Per-reviewer load:** R1 = 12, R2 = 12, R3 = 11 items.

The machine-readable assignment is one row per `(reviewer, item)` in
[`expert_review_scoring_sheet.csv`](expert_review_scoring_sheet.csv)
(`reviewer_id, item_id, role, subskill, score_1to5, notes`).

## Analysis (after collection)

1. **Engine vs. human:** mean absolute difference between the engine score and the
   mean human score per item (target: within ±1 on the 1–5 scale).
2. **Inter-rater agreement** on the overlap block (sanity-check that humans agree
   before judging the engine).
3. Record results in [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) §assessment.
