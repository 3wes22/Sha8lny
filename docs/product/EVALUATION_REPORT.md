# Evaluation Report

Consolidated evaluation evidence for Sha8lny's AI components. **Every number
below traces to a committed artifact**; nothing is asserted without a file path.
This report is the defense-facing roll-up of the per-component evals.

| Component | Method | Headline result | Artifact |
|---|---|---|---|
| RAG retrieval | 55-query eval set, doc-level ground truth | recall@5 0.118 → **0.609** final pipeline (rerank peak **0.627**; ×5.2) | `ai-models/eval_results/retrieval/*.json` |
| Job ranker | Leave-one-group-out NDCG/MAP vs baselines | ndcg@5 **0.589** vs 0.560 overlap / 0.160 random; MAP ties overlap | `ai-models/models/custom/job_ranker_eval.json` |
| Source credibility | Deterministic tier fraction | scorer + tests green | `ai-models/src/rag/credibility.py` |
| Assessment (open-ended) | Expert review packet (blind, 3 reviewers) | packet + analysis tooling ready; human session pending | `EXPERT_REVIEW_PACKET.md`, `analyze_expert_review.py` |
| Faithfulness | LLM-judge (Gemini) | judge wired; pilot set committed; operator run on fresh key | `eval_faithfulness.py`, `faithfulness_pilot.json` |

---

## 1. RAG retrieval (primary result)

**Method.** 55 realistic career-advisory queries with metadata-anchored ground
truth (`ai-models/data/eval/retrieval_eval_set.jsonl`), each layer measured
through the production path `rag.retriever.retrieve_context` **before** the next
landed, with the baseline locked first. Full per-stage table and per-technique
diagnosis: [`RAG_RETRIEVAL_EVAL.md`](RAG_RETRIEVAL_EVAL.md).

| Stage | recall@5 | precision@5 | MRR |
|---|---|---|---|
| baseline (old corpus, 500-char chunks, dense + min_score) | 0.118 | 0.055 | 0.109 |
| + license-clean corpus & structure-aware chunks | 0.209 | 0.062 | 0.161 |
| + hybrid BM25 + RRF | 0.536 | 0.175 | 0.396 |
| + cross-encoder re-rank | **0.627** | **0.226** | **0.553** |
| + diversity & abstention floor (final) | 0.609 | 0.218 | 0.544 |

**Against thresholds.** Precision@5 target was >0.70; **measured 0.22 — a
documented miss.** Root cause (diagnosed, not assumed): doc-level matchers
under-credit multiple relevant chunks from one annotated source, and 16/55
queries — concentrated in roadmap-category bleed — still miss in the top-10. The
*relative* gains (final pipeline recall@5 ×5.2 to 0.609, MRR ×5.0 to 0.544; rerank
peak recall@5 0.627 / MRR 0.553) are the defensible story; the absolute
precision target is honest future work (per-source quotas, multilingual corpus).

## 2. Job ranker

**Method.** Leave-one-group-out cross-validation over 8 synthetic user profiles
× 60 fixture postings; relevance grades from weak-supervision labeling functions
(skill-overlap quartiles + role-title boost), **not** human labels.

| Metric | LightGBM | Overlap baseline | Random |
|---|---|---|---|
| ndcg@5 | **0.5895** | 0.5603 | 0.1597 |
| ndcg@10 | 0.5755 | 0.5601 | 0.2118 |
| map | 0.3750 | 0.3750 | 0.1589 |

The learned ranker shows a small ndcg@5 lift over overlap (+0.029) and a large
lift over random, while **MAP ties the overlap baseline**. The embedding feature
was **disabled** in this run (sentence-transformers unavailable in the training
env), so this should be defended as a weak-supervision *methodology
demonstrator*, not as a market-validated production model. The current
repository commits eval artifacts, not `job_ranker.lgb`; runtime falls back to
skill-overlap ordering when no local model file exists. The real-data upgrade
path (ingest ≥100 real Egyptian postings → retrain with embeddings → re-eval)
is documented in [`DATASET_REGISTRY.md`](DATASET_REGISTRY.md) and
`EVAL_REPORT.md`, and is an operator step (no live network in this environment).

## 3. Source credibility (deterministic)

`credibility_score` = fraction of cited sources whose registry `quality_tier` is
authoritative (official/government/peer-reviewed/established/curated);
`dev_fallback` (roadmap.sh) and unknown do not count. Pure-Python, 5 tests green
(`ai-models/tests/test_credibility.py`). This is the deterministic half of the
faithfulness/credibility pair; the LLM-judge faithfulness scorer is scaffolded
but Gemini-quota-gated and is run by the operator on a fresh key.

## 4. Assessment scoring

Open-ended answers are graded either by an **LLM rubric** (Gemini, 1–5 vs
`expected_concepts`) or, on any failure, a deterministic **keyword-coverage**
fallback; the method is recorded per response
(`Backend/apps/assessments/engine.py`, tests in `test_engine.py`). Validation
against independent experts uses the blind 3-reviewer packet
([`EXPERT_REVIEW_PACKET.md`](EXPERT_REVIEW_PACKET.md)); recruiting reviewers and
running the session is an operator step. The instrument is positioned as
**formative**, not psychometrically validated (see
[`ROLE_GRAPH_METHODOLOGY.md`](ROLE_GRAPH_METHODOLOGY.md)).

## Thresholds summary (honest)

| Target | Status |
|---|---|
| Retrieval recall@5 lift over baseline | ✅ ×5.2 |
| Precision@5 > 0.70 | ❌ 0.22 — documented miss + root cause |
| Ranker beats overlap & random baselines | 🟡 ndcg@5 beats overlap slightly and random strongly; MAP ties overlap; embedding disabled |
| Credibility scorer deterministic + tested | ✅ |
| Faithfulness > 0.85 (LLM judge) | ⏳ scaffolded, Gemini-gated (operator run) |
| Expert-review agreement | ⏳ packet ready, session is operator step |

## Reproduce

```bash
cd ai-models
../Backend/venv/bin/python scripts/run_retrieval_eval.py --stage <label>
../Backend/venv/bin/python -m pytest tests/test_credibility.py -q
../Backend/venv/bin/python scripts/generate_eval_charts.py
python scripts/analyze_expert_review.py --csv ../docs/product/expert_review_scoring_sheet.csv --engine ../docs/product/expert_review_engine_scores.json
cd ../Backend && env -u GEMINI_API_KEY python manage.py score_expert_review_reference
```
