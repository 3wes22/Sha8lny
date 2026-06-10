"""
Corpus validation layer (corpus v2).

Gates every fetched/authored corpus file before the builder embeds it, and
deduplicates chunks before storage. The shape contract:

- A provenance header comment carrying ``source``, ``url:``, ``license``
  and ``captured`` (written by ``fetch_corpus_sources.py`` or by hand for
  authored excerpt-and-cite files; see DATASET_REGISTRY.md).
- A substantive, heading-structured markdown body (the chunker keys
  section metadata off headings).
- No raw-HTML extraction junk, no control characters.

Chunk dedupe key is (source, category, normalized content): exact duplicates
within a source+category are storage noise, while the same roadmap topic
appearing under several role categories is legitimate coverage and is kept.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

MIN_BODY_CHARS = 500
MAX_HTML_TAGS_PER_1000 = 20

_HEADER = re.compile(r"\A<!--(.*?)-->", re.DOTALL)
_HEADING = re.compile(r"^#{1,3} \S", re.MULTILINE)
_HTML_TAG = re.compile(r"<[a-zA-Z][^>]*>")
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def validate_file_text(text: str) -> List[str]:
    """Return a list of issues; empty list means the file is ingestable."""
    issues: List[str] = []

    header_match = _HEADER.match(text)
    if not header_match:
        issues.append("missing provenance header comment")
        body = text
    else:
        header = header_match.group(1)
        for field in ("source", "url", "license"):
            if not re.search(rf"{field}\s*:", header):
                issues.append(f"provenance header missing '{field}:'")
        # the fetch date is written as "captured:" (connector captures) or
        # "fetched:" (direct fetches) — either satisfies provenance
        if not re.search(r"(captured|fetched)\s*:", header):
            issues.append("provenance header missing 'captured:'/'fetched:' date")
        body = text[header_match.end():]

    if len(body.strip()) < MIN_BODY_CHARS:
        issues.append(f"body too short (<{MIN_BODY_CHARS} chars)")

    if not _HEADING.search(body):
        issues.append("no markdown headings (chunker needs structure)")

    tag_count = len(_HTML_TAG.findall(body))
    if body and tag_count > MAX_HTML_TAGS_PER_1000 * max(len(body), 1000) / 1000:
        issues.append(f"raw HTML junk ({tag_count} tags)")

    if _CONTROL.search(text):
        issues.append("control characters present")

    return issues


def validate_file(path: Path) -> List[str]:
    try:
        return validate_file_text(path.read_text(encoding="utf-8"))
    except Exception as error:
        return [f"unreadable: {error}"]


def _normalize(content: str) -> str:
    return re.sub(r"\s+", " ", content).strip().lower()


def dedupe_chunks(chunks: List[Dict]) -> Tuple[List[Dict], int]:
    """Drop exact duplicates within (source, category); first occurrence wins."""
    seen = set()
    kept: List[Dict] = []
    dropped = 0
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        key = (metadata.get("source"), metadata.get("category"), _normalize(chunk.get("content") or ""))
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        kept.append(chunk)
    return kept, dropped
