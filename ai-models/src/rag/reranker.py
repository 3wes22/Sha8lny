"""
Cross-encoder re-ranking of fused retrieval candidates (plan Task 1.9).

Bi-encoder (dense) and BM25 rankings score query and document independently;
a cross-encoder reads the (query, passage) pair jointly and is consistently
more accurate at ordering a small candidate pool (Nogueira & Cho 2019,
"Passage Re-ranking with BERT"). We re-rank the fused top candidates with
``cross-encoder/ms-marco-MiniLM-L-6-v2`` — small, local, no API cost.

Degrades gracefully: disabled via RAG_RERANK_ENABLED=0, or silently skipped
when sentence-transformers / the model is unavailable.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

Scorer = Callable[[Sequence[Tuple[str, str]]], Sequence[float]]

_scorer: Optional[Scorer] = None
_scorer_failed = False


def _enabled() -> bool:
    return os.getenv("RAG_RERANK_ENABLED", "1").strip().lower() not in ("0", "false", "no")


def _get_scorer() -> Optional[Scorer]:
    """Lazily load the cross-encoder; None when unavailable."""
    global _scorer, _scorer_failed
    if _scorer is not None or _scorer_failed:
        return _scorer
    try:
        from sentence_transformers import CrossEncoder

        model = CrossEncoder(os.getenv("RAG_RERANK_MODEL", DEFAULT_MODEL))
        _scorer = lambda pairs: model.predict(list(pairs))  # noqa: E731
    except Exception as error:
        logger.warning("Cross-encoder unavailable; re-ranking skipped: %s", error)
        _scorer_failed = True
    return _scorer


def rerank(
    query: str,
    docs: List[Dict[str, Any]],
    top_k: int,
    scorer: Optional[Scorer] = None,
) -> List[Dict[str, Any]]:
    """Re-order docs by joint (query, passage) relevance; top_k results.

    Passthrough (original order, truncated) when disabled or unavailable.
    ``scorer`` is injectable for tests.
    """
    if not docs:
        return []
    if not _enabled():
        return docs[:top_k]
    scorer = scorer or _get_scorer()
    if scorer is None:
        return docs[:top_k]

    scores = scorer([(query, doc.get("content") or "") for doc in docs])
    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)

    results = []
    for doc, score in ranked[:top_k]:
        doc = dict(doc)
        doc["rerank_score"] = float(score)
        doc["retrieval"] = "hybrid_rrf+ce"
        results.append(doc)
    return results
