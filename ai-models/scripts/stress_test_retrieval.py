#!/usr/bin/env python3
"""
Retrieval stress test (corpus v2).

Probes the production retrieval path with inputs the 55-query eval set does
not cover: paraphrase consistency, typos, exact-term lookups, Egypt-official
coverage, off-topic adversarials, Arabic/code-switched queries, vague
queries. Reports per-query top results with rerank scores and aggregate
latency/diversity statistics.

This is qualitative evidence (transcripts) complementing the quantitative
eval (scripts/run_retrieval_eval.py). Run with the Backend venv:

    cd ai-models && ../Backend/venv/bin/python scripts/stress_test_retrieval.py
"""

from __future__ import annotations

import re
import statistics
import sys
import time
from pathlib import Path

AI_MODELS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_MODELS_ROOT))
sys.path.insert(0, str(AI_MODELS_ROOT / "src"))

CASES = {
    "paraphrase (same intent x3)": [
        "How much do junior backend developers make in Egypt?",
        "expected pay for an entry level backend dev in Cairo?",
        "junior developer salaries Egypt - what's a normal range?",
    ],
    "typos": [
        "How do I negotaite my salray with an egptian employer?",
        "what is CROS and why do browsers block requets?",
    ],
    "exact terms / codes": [
        "What occupation is O*NET code 15-1252.00?",
        "Which tasks does SOC 15-2051.00 involve?",
        "What is reciprocal rank fusion?",
    ],
    "egypt official coverage": [
        "How fast is Egypt's ICT sector growing according to official figures?",
        "What free government training programs can I join in Egypt like DEPI or DEBI?",
        "How many offshoring companies operate in Egypt and how big are digital exports?",
    ],
    "off-topic adversarial": [
        "What medication should I take for a headache?",
        "How do I apply for a Schengen tourist visa?",
        "Who is the best football team in Egypt?",
    ],
    "arabic / code-switched": [
        "ezay alaa2y shoghl backend fi masr?",
        "ازاي اتعلم البرمجة من الصفر؟",
    ],
    "vague": [
        "help me with my career",
        "what should I learn next?",
    ],
}


def main() -> int:
    from src.rag.retriever import retrieve_context

    t0 = time.time()
    retrieve_context("warmup", top_k=1)
    print(f"(index warmup: {time.time()-t0:.1f}s)\n")

    latencies = []
    diversity_violations = 0

    for category, queries in CASES.items():
        print("=" * 96)
        print(f"CATEGORY: {category}")
        for query in queries:
            t = time.time()
            docs = retrieve_context(query, top_k=5)
            took = time.time() - t
            latencies.append(took)

            # diversity invariants: no duplicate content, <=2 per (file, section)
            normalized = [re.sub(r"\s+", " ", (d.get("content") or "")).strip().lower() for d in docs]
            sections = [((d.get("metadata") or {}).get("file"), (d.get("metadata") or {}).get("section")) for d in docs]
            if len(set(normalized)) != len(normalized) or any(sections.count(s) > 2 for s in set(sections)):
                diversity_violations += 1

            top_rr = docs[0].get("rerank_score") if docs else None
            print(f"\n  Q: {query}   [{took:.2f}s, top rerank={'%.2f' % top_rr if top_rr is not None else 'n/a'}]")
            for d in docs[:3]:
                m = d.get("metadata") or {}
                loc = (m.get("section") or m.get("title") or m.get("category") or "")[:42]
                rr = d.get("rerank_score")
                print(f"     [{m.get('source','?'):>14} | {loc:<42} | {d.get('confidence_tier','-'):>6} | rr={'%.2f' % rr if rr is not None else ' n/a'}]")
        print()

    print("=" * 96)
    print(f"latency: p50={statistics.median(latencies):.2f}s  "
          f"p95={sorted(latencies)[int(0.95 * len(latencies)) - 1]:.2f}s  n={len(latencies)}")
    print(f"diversity violations (dup content or >2 per section in top-5): {diversity_violations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
