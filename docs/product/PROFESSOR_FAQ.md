# Professor FAQ

Pre-answered defense questions. **Every answer names its evidence artifact** and
none contradicts the registers ([`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md),
[`DATASET_REGISTRY.md`](DATASET_REGISTRY.md)).

---

### "What's different from just calling an LLM API?"

The contribution is the **retrieval and grounding layer around** the LLM, built
and measured stage-by-stage — not the API call. Structure-aware chunking, hybrid
BM25+dense with RRF fusion, cross-encoder re-ranking, citations + confidence
tiers, and an abstention floor together moved recall@5 from 0.118 to 0.627 (×5.2)
over a locked baseline. A bare API call has none of this, hallucinates sources,
and never abstains.
*Evidence:* [`RAG_ARCHITECTURE.md`](RAG_ARCHITECTURE.md),
[`RAG_RETRIEVAL_EVAL.md`](RAG_RETRIEVAL_EVAL.md).

### "How do you know it's accurate / not hallucinating?"

Three mechanisms. (1) The advisor answers **only** from retrieved passages and
returns each source; (2) off-topic queries hit an abstention floor and return
`no_retrieval_context` — an explicit "I don't have grounded information" state —
rather than a confident guess; (3) a deterministic credibility scorer measures
the fraction of cited sources that are authoritative, and an (operator-run)
LLM-judge measures faithfulness of answers to their passages.
*Evidence:* [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) §1, §3;
`ai-models/src/rag/credibility.py`; advisory `no_retrieval_context` contract.

### "Where did the data come from? Is it licensed?"

Every source is screened **before** ingestion with a recorded license and a
USE / REJECT / dev-only decision: BLS Occupational Outlook Handbook (public
domain), MDN (CC-BY-SA), curated Egyptian-market material, and O\*NET descriptor
*stems* (numeric rating rows excluded). roadmap.sh is **personal-use only**, so
it is used solely as a flagged development fallback (`quality_tier: dev_fallback`)
and is never part of the defended corpus or redistributed.
*Evidence:* [`DATASET_REGISTRY.md`](DATASET_REGISTRY.md); roadmap provenance
`structure_license_tier=dev_only`.

### "Is the assessment scientifically valid?"

It is positioned as a **formative** instrument, not a psychometrically validated
one — we say so explicitly. Competency dimensions, weights, and target
proficiencies are documented expert judgments with a partial O\*NET crosswalk
(Backend mapped in depth with concrete element IDs). Scoring is a deterministic
weighted roll-up — the LLM's self-reported score is never trusted — with an
optional LLM rubric for open-ended answers and a keyword fallback. A blind
3-reviewer expert-review packet is prepared to quantify engine-vs-human
agreement.
*Evidence:* [`ROLE_GRAPH_METHODOLOGY.md`](ROLE_GRAPH_METHODOLOGY.md);
[`EXPERT_REVIEW_PACKET.md`](EXPERT_REVIEW_PACKET.md);
`Backend/apps/assessments/engine.py`.

### "How is the job ranker more than a heuristic?"

It is a LightGBM learning-to-rank model evaluated by **leave-one-group-out**
NDCG/MAP against skill-overlap and random baselines (ndcg@5 0.589 vs 0.560 vs
0.160). We are transparent that it is a **weak-supervision demonstrator** on
synthetic fixtures with pseudo-labels — the lift over baselines is the honest
signal, and the embedding feature was disabled in that run (so the lift is a
lower bound). The real-postings retrain path is scaffolded.
*Evidence:* `ai-models/models/custom/EVAL_REPORT.md`, `job_ranker_eval.json`;
[`JOB_RANKER_METHODOLOGY.md`](JOB_RANKER_METHODOLOGY.md).

### "What happens if the API key dies during the demo?"

The system degrades gracefully: assessment and roadmap have deterministic,
assessment-aware fallbacks; advisory returns a grounded fallback or the
no-context state; retrieval degrades to dense-only if BM25/rerank can't load. The
demo runs end-to-end with **no `GEMINI_API_KEY` and no Chroma volume**.
*Evidence:* [`GRADUATION_DEMO_RUNBOOK.md`](GRADUATION_DEMO_RUNBOOK.md) (offline
path); deterministic fallbacks across modules.

### "What would you improve / what are the limitations?"

The honest top items: (1) **multilingual** — English-only corpus + embedder fail
Arabic/code-switched queries, the most important gap for an Egyptian platform;
(2) **precision@5 (0.22)** misses the 0.70 target — documented with root cause;
(3) **real labeled job data** to replace synthetic fixtures; (4) **psychometric
validation** and a completed expert-review session; (5) **LLM fine-tuning**
(deferred for hardware/budget). None of these are hidden — each is in the
registers and reports.
*Evidence:* [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) thresholds table;
[`CLAIMS_REGISTER.md`](CLAIMS_REGISTER.md) limitations.

### "How do I verify any of this myself?"

```bash
cd Backend && pytest                 # 333 backend tests
cd Frontend && npm run build         # clean build
cd Backend && python manage.py scenario_corpus_audit --tier 1   # 8/8 roles
cd ai-models && ../Backend/venv/bin/python -m pytest tests/test_credibility.py -q
```
Every metric in the reports names a committed JSON/`.lgb`/`.md` artifact.
