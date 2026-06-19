#!/usr/bin/env python3
"""
Retrieval eval runner (plan Task 1.3).

Measures the *production* retrieval path (``rag.retriever.retrieve_context``
with its default similarity threshold) against the eval set, and writes a
stage-labeled results artifact. The first run ("baseline") is the control
group: every Week-1 retrieval improvement must be re-measured against it
before the next layer lands.

Usage (run with an interpreter that has chromadb + sentence-transformers —
the Backend venv qualifies):

    cd ai-models
    ../Backend/venv/bin/python scripts/run_retrieval_eval.py --stage baseline

Metrics:
- recall@k   — fraction of a query's relevance matchers hit by the top-k
- precision@5 — fraction of the top-5 docs that hit any matcher
- mrr        — mean reciprocal rank of the first hit
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

AI_MODELS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_MODELS_ROOT))          # for src.* imports
sys.path.insert(0, str(AI_MODELS_ROOT / "src"))  # mirror Backend's `rag.*` import path

from src.rag.eval_matching import first_hit_rank, hit_matcher_indexes  # noqa: E402
from src.rag.eval_metrics import precision_at_k  # noqa: E402

EVAL_SET_PATH = AI_MODELS_ROOT / "data" / "eval" / "retrieval_eval_set.jsonl"
RESULTS_DIR = AI_MODELS_ROOT / "eval_results" / "retrieval"
RETRIEVE_TOP_K = 10


def load_eval_set(path: Path) -> list[dict]:
    entries = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def evaluate(entries: list[dict]) -> dict:
    from src.rag.retriever import retrieve_context

    per_query = []
    recall5_sum = recall10_sum = precision5_sum = rr_sum = 0.0

    for entry in entries:
        docs = retrieve_context(entry["query"], top_k=RETRIEVE_TOP_K)
        matchers = entry["relevant"]

        hits_at_5 = hit_matcher_indexes(docs, matchers, k=5)
        hits_at_10 = hit_matcher_indexes(docs, matchers, k=10)
        recall_5 = len(hits_at_5) / len(matchers)
        recall_10 = len(hits_at_10) / len(matchers)

        # precision@5 / RR treat "hits any matcher" as relevant; reuse the
        # tested metric functions via positional pseudo-ids.
        pseudo_ids = [str(i) for i in range(len(docs))]
        relevant_positions = {
            str(i) for i, doc in enumerate(docs)
            if any_hit(doc, matchers)
        }
        precision_5 = precision_at_k(pseudo_ids, relevant_positions, k=5)
        rank = first_hit_rank(docs, matchers)
        rr = 1.0 / rank if rank else 0.0

        recall5_sum += recall_5
        recall10_sum += recall_10
        precision5_sum += precision_5
        rr_sum += rr

        per_query.append({
            "query_id": entry["query_id"],
            "n_retrieved": len(docs),
            "first_hit_rank": rank,
            "recall@5": round(recall_5, 4),
            "recall@10": round(recall_10, 4),
            "precision@5": round(precision_5, 4),
        })

    n = len(entries)
    return {
        "metrics": {
            "recall@5": round(recall5_sum / n, 4),
            "recall@10": round(recall10_sum / n, 4),
            "precision@5": round(precision5_sum / n, 4),
            "mrr": round(rr_sum / n, 4),
        },
        "per_query": per_query,
    }


def any_hit(doc: dict, matchers: list[dict]) -> bool:
    from src.rag.eval_matching import matcher_hits

    return any(matcher_hits(m, doc) for m in matchers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True,
                        help="Label for this run (baseline, corpus_chunking, hybrid, rerank)")
    parser.add_argument("--eval-set", type=Path, default=EVAL_SET_PATH)
    parser.add_argument("--out-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    entries = load_eval_set(args.eval_set)
    print(f"Evaluating {len(entries)} queries (stage={args.stage}, top_k={RETRIEVE_TOP_K})...")

    result = evaluate(entries)

    from src.rag import runtime_settings
    payload = {
        "stage": args.stage,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "eval_set": str(args.eval_set.relative_to(AI_MODELS_ROOT)),
        "num_queries": len(entries),
        "retriever_config": {
            "top_k": RETRIEVE_TOP_K,
            "embedding_model": runtime_settings.get_embedding_model(),
        },
        **result,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / f"{args.stage}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"\nStage: {args.stage}")
    for name, value in payload["metrics"].items():
        print(f"  {name:>12}: {value}")
    zero_hit = [q["query_id"] for q in result["per_query"] if q["first_hit_rank"] == 0]
    print(f"  queries with no hit in top-{RETRIEVE_TOP_K}: {len(zero_hit)}"
          + (f" ({', '.join(zero_hit[:10])}{'...' if len(zero_hit) > 10 else ''})" if zero_hit else ""))
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
