"""
Pure-Python retrieval evaluation metrics.

Control-group harness for the knowledge-layer rebuild (IMPLEMENTATION_PLAN.md
Task 1.1). Deliberately dependency-free — no Chroma, no numpy, no network —
so the eval harness can run in any environment, including CI.

Conventions:
- ``recall_at_k`` / ``precision_at_k`` follow the strict textbook definitions:
  recall divides by the number of relevant documents, precision divides by k
  (short result lists are penalized, not excused).
- Undefined cases (no relevant documents, empty retrieval) return 0.0 rather
  than raising, so a single degenerate eval row cannot abort a full run; the
  eval set schema test guards against accidentally-empty rows.
"""

from __future__ import annotations

from typing import Iterable, Sequence, Set, Tuple


def recall_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
    """Fraction of relevant documents found in the top-k results."""
    if not relevant_ids or not retrieved_ids or k <= 0:
        return 0.0
    hits = sum(1 for doc_id in retrieved_ids[:k] if doc_id in relevant_ids)
    return hits / len(relevant_ids)


def precision_at_k(retrieved_ids: Sequence[str], relevant_ids: Set[str], k: int) -> float:
    """Fraction of the top-k slots filled with relevant documents."""
    if not retrieved_ids or k <= 0:
        return 0.0
    hits = sum(1 for doc_id in retrieved_ids[:k] if doc_id in relevant_ids)
    return hits / k


def reciprocal_rank(retrieved_ids: Sequence[str], relevant_ids: Set[str]) -> float:
    """1/rank of the first relevant result, or 0.0 if none is retrieved."""
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def mrr(runs: Iterable[Tuple[Sequence[str], Set[str]]]) -> float:
    """Mean reciprocal rank over ``(retrieved_ids, relevant_ids)`` pairs."""
    ranks = [reciprocal_rank(retrieved, relevant) for retrieved, relevant in runs]
    if not ranks:
        return 0.0
    return sum(ranks) / len(ranks)
