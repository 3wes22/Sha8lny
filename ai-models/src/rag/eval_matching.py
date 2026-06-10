"""
Matcher semantics for the retrieval eval set (plan Task 1.3).

The eval set (``data/eval/retrieval_eval_set.jsonl``) declares relevance as
metadata matchers rather than chunk ids, because chunk ids are hash+index
based and change on every rebuild. A matcher hits a retrieved doc when every
field it specifies matches:

- ``source`` / ``file`` / ``section`` / ``subsection``: equality against
  ``doc["metadata"]``
- ``content_contains``: case-insensitive substring of ``doc["content"]``

Docs are the dicts returned by ``vector_store.search`` /
``retriever.retrieve_context`` (keys: id, content, metadata, score).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Set

_METADATA_KEYS = ("source", "file", "section", "subsection")


def matcher_hits(matcher: Dict[str, str], doc: Dict[str, Any]) -> bool:
    """True when every field the matcher specifies matches the doc."""
    metadata = doc.get("metadata") or {}
    for key in _METADATA_KEYS:
        if key in matcher and metadata.get(key) != matcher[key]:
            return False
    needle = matcher.get("content_contains")
    if needle is not None:
        content = doc.get("content") or ""
        if needle.lower() not in content.lower():
            return False
    return True


def first_hit_rank(docs: Sequence[Dict[str, Any]], matchers: List[Dict[str, str]]) -> int:
    """1-indexed rank of the first doc hit by any matcher; 0 if none."""
    for rank, doc in enumerate(docs, start=1):
        if any(matcher_hits(m, doc) for m in matchers):
            return rank
    return 0


def hit_matcher_indexes(
    docs: Sequence[Dict[str, Any]],
    matchers: List[Dict[str, str]],
    k: Optional[int] = None,
) -> Set[int]:
    """Indexes of matchers hit by at least one of the top-k docs."""
    pool = docs if k is None else docs[:k]
    hit = set()
    for index, matcher in enumerate(matchers):
        if any(matcher_hits(matcher, doc) for doc in pool):
            hit.add(index)
    return hit
