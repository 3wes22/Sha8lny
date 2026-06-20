"""Deterministic source-credibility scoring (Task 4.1).

Credibility = the fraction of cited sources whose registry ``quality_tier`` is
authoritative (official / government / peer-reviewed / established / curated).
Development-only fallback sources (e.g. roadmap.sh under a personal-use license,
tagged ``dev_fallback``) and unknown sources do not count toward credibility.

This is the *deterministic* half of the evaluation suite — pure Python, no model
or network — and complements the LLM-judge faithfulness scorer
(``scripts/eval_faithfulness.py``). Source quality tiers are documented in
``docs/product/DATASET_REGISTRY.md``.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


# Tiers that count as credible / citable in a defense.
CREDIBLE_TIERS: frozenset[str] = frozenset(
    {"official", "government", "peer_reviewed", "established", "curated"}
)
# Tiers that are explicitly present but do NOT count toward credibility.
NON_CREDIBLE_TIERS: frozenset[str] = frozenset(
    {"dev_fallback", "user_generated", "unknown"}
)


def tier_of(doc: Any) -> str:
    """Resolve a document's quality tier from a string, dict, or metadata dict."""
    if isinstance(doc, str):
        return doc.strip().lower() or "unknown"
    if isinstance(doc, dict):
        metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else doc
        return str(metadata.get("quality_tier") or "unknown").strip().lower()
    return "unknown"


def is_credible(doc: Any) -> bool:
    """True when the document's quality tier is authoritative."""
    return tier_of(doc) in CREDIBLE_TIERS


def credibility_score(docs: Iterable[Any]) -> float:
    """Fraction of cited sources that are credible (0.0–1.0); 0.0 when empty."""
    items = list(docs)
    if not items:
        return 0.0
    credible = sum(1 for doc in items if is_credible(doc))
    return credible / len(items)


def credibility_breakdown(docs: Iterable[Any]) -> dict[str, Any]:
    """Score plus per-tier counts, for the evaluation report."""
    items = list(docs)
    tier_counts = Counter(tier_of(doc) for doc in items)
    return {
        "total": len(items),
        "credible": sum(count for tier, count in tier_counts.items() if tier in CREDIBLE_TIERS),
        "score": credibility_score(items),
        "by_tier": dict(tier_counts),
    }
