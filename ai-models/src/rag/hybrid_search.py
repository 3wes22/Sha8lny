"""
Hybrid retrieval support: BM25 keyword search + reciprocal rank fusion
(plan Task 1.8).

Dense embeddings miss exact-term queries (SOC codes, tool names, acronyms
like CORS); BM25 misses paraphrases. Fusing both with RRF is a standard,
robust combination (Cormack et al., SIGIR 2009: reciprocal rank fusion
outperforms individual rankers and learned fusion on TREC runs).

Degrades gracefully: if ``rank_bm25`` is not importable or the index has no
documents, ``HybridIndex.available`` is False and ``search`` returns [] —
callers fall back to dense-only retrieval, mirroring the advisory module's
existing fault-tolerance.
"""

from __future__ import annotations

import re
from typing import Dict, List, Sequence, Tuple

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - exercised via monkeypatch in tests
    BM25Okapi = None

_TOKEN = re.compile(r"[a-z0-9][a-z0-9.+#-]*")

RRF_K = 60  # standard constant from Cormack et al. 2009


def _tokenize(text: str) -> List[str]:
    return _TOKEN.findall(text.lower())


class HybridIndex:
    """BM25 index over chunk texts, keyed by chunk id."""

    def __init__(self, docs: Sequence[Dict]):
        self._ids = [doc["id"] for doc in docs]
        corpus = [_tokenize(doc.get("content") or "") for doc in docs]
        if BM25Okapi is None or not corpus:
            self._bm25 = None
        else:
            self._bm25 = BM25Okapi(corpus)

    @property
    def available(self) -> bool:
        return self._bm25 is not None

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """Top-k (chunk_id, bm25_score) for the query; [] when unavailable."""
        tokens = _tokenize(query)
        if not self.available or not tokens:
            return []
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(zip(self._ids, scores), key=lambda pair: pair[1], reverse=True)
        return [(doc_id, float(score)) for doc_id, score in ranked[:top_k] if score > 0]


def rrf_fuse(rankings: Sequence[Sequence[str]], k: int = RRF_K) -> List[Tuple[str, float]]:
    """Fuse ranked id lists with reciprocal rank fusion.

    score(d) = sum over rankings containing d of 1 / (k + rank_d), rank 1-based.
    Returns ids sorted by fused score, descending.
    """
    scores: Dict[str, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
