# RAG Retrieval Evaluation — Week-1 Knowledge-Layer Rebuild

_Measured 2026-06-10. Every number traces to a committed artifact in
`ai-models/eval_results/retrieval/`. Method: 55 realistic advisory queries with
metadata-anchored ground truth (`ai-models/data/eval/retrieval_eval_set.jsonl`),
evaluated through the production path `rag.retriever.retrieve_context`. Each
layer was measured **before** the next landed; the baseline was locked before
any change._

## Results by layer

| Stage | recall@5 | recall@10 | precision@5 | MRR | queries w/ no hit in top-10 |
|---|---|---|---|---|---|
| **baseline** (old corpus, 500-char chunks, dense + min_score) | 0.118 | 0.118 | 0.055 | 0.109 | 48 / 55 |
| **corpus_chunking** (license-clean corpus, structure-aware chunks) | 0.209 | 0.209 | 0.062 | 0.161 | 43 / 55 |
| **hybrid** (+ BM25 + RRF fusion, rank-based selection) | 0.536 | 0.673 | 0.175 | 0.396 | 17 / 55 |
| **rerank** (+ cross-encoder top-pool re-ranking) | **0.627** | **0.682** | **0.226** | **0.553** | **16 / 55** |

**Cumulative: recall@5 ×5.3, MRR ×5.1, precision@5 ×4.1 over baseline.**

## What each layer fixed (diagnosed, not assumed)

1. **Baseline failure mode.** The collection held 358,992 docs, ~85% of them
   near-identical O*NET numeric rating rows pulled in by a substring whitelist
   bug; top-hit cosine scores ran negative while `retrieve_context` filtered at
   `min_score=0.3`, so **35/55 queries returned zero documents** — the advisor
   answered ungrounded because retrieval gave it nothing.
2. **corpus_chunking.** Exact-stem O*NET whitelist (numeric rating files
   excluded from RAG per `DATASET_REGISTRY.md`); BLS OOH (8 profiles, public
   domain) and MDN (12 pages, CC-BY-SA) ingested; roadmap.sh chunked
   structure-aware with headings retained (previously stripped) and astro
   frontmatter dropped. Collection: 64,756 docs (−82%).
3. **hybrid.** Dense + BM25 fused with reciprocal rank fusion (Cormack et al.,
   SIGIR 2009). Rank-based selection replaced the absolute `min_score` cutoff —
   the single largest gain (recall@5 0.209 → 0.536), because BM25 catches
   exact-term queries (SOC codes, "CORS", section keywords) that MiniLM
   embeddings place below the old threshold.
4. **rerank.** `cross-encoder/ms-marco-MiniLM-L-6-v2` re-orders the fused pool
   jointly (Nogueira & Cho 2019). Biggest effect on first-hit rank:
   MRR 0.396 → 0.553.

## Honest limitations

- 16 queries still have no relevant hit in the top-10; failures concentrate in
  roadmap-category queries (`q030`–`q045` family) where many topic chunks from
  *other* roadmaps outrank the target roadmap's chunks, and in
  `skill_assessment.md` queries phrased abstractly (q021–q029 family). These
  are the Week-4 evaluation loop's first targets (candidates: source-diversity
  enforcement, per-source candidate quotas).
- The eval set was authored by the implementer (52→55 queries, single
  annotator); matchers are doc-level, so precision@5 under-credits multiple
  relevant chunks from one annotated source.
- Ground-truth anchoring changed twice during Week 1 (roadmap `file` →
  `category`; 3 O*NET-numeric queries re-anchored after the registry decision).
  The committed `baseline.json` was re-measured against the **old** collection
  after each change, so the table compares like with like.
- Confidence tiering (Task 1.10) is rule-based (source quality + rerank
  signal), not calibrated against human judgments.

## Reproduce

```bash
cd ai-models
../Backend/venv/bin/python scripts/run_retrieval_eval.py --stage <label>
# artifacts land in eval_results/retrieval/<label>.json
```
