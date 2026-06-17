"""
Structure-aware markdown chunker (plan Task 1.6).

Replaces the fixed 500-character ``chunk_text`` used for roadmap.sh content,
which stripped headings and split mid-sentence. This chunker:

- splits on H2/H3 boundaries and records heading titles as ``section`` /
  ``subsection`` metadata — the same keys the retrieval eval set matches on;
- packs long sections into chunks of at most ``max_chars``, cutting only at
  sentence boundaries, with a one-sentence overlap between consecutive chunks;
- merges caller-provided base metadata (source, file, quality_tier, ...) into
  every chunk.

Returned chunks are ``{"content": str, "metadata": dict}`` — the builder adds
ids and embeds the content.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_HEADING = re.compile(r"^(#{1,3})\s+(.*)$")

DEFAULT_MAX_CHARS = 900
DEFAULT_MIN_CHARS = 50


def chunk_markdown(
    text: str,
    base_metadata: Dict[str, str],
    max_chars: int = DEFAULT_MAX_CHARS,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> List[Dict]:
    """Chunk markdown text into structure-tagged passages."""
    if not text or not text.strip():
        return []

    blocks = _split_into_blocks(text)
    chunks: List[Dict] = []

    for block in blocks:
        body = block["body"].strip()
        if len(body) < min_chars:
            continue

        prefix = _heading_prefix(block)
        budget = max(max_chars - len(prefix), 80)

        for piece in _pack_sentences(body, budget):
            metadata = dict(base_metadata)
            metadata["section"] = block["section"]
            if block["subsection"]:
                metadata["subsection"] = block["subsection"]
            chunks.append({"content": f"{prefix}{piece}", "metadata": metadata})

    return chunks


def _split_into_blocks(text: str) -> List[Dict]:
    """Group lines into blocks keyed by their governing H2/H3 headings."""
    doc_title: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    blocks: List[Dict] = []
    current: List[str] = []

    def flush():
        if current:
            blocks.append({
                "section": section or doc_title or "Document",
                "subsection": subsection,
                "body": "\n".join(current),
                "is_preamble": section is None,
            })
            current.clear()

    for line in text.splitlines():
        match = _HEADING.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            if level == 1:
                if doc_title is None:
                    doc_title = title
                    continue
                # subsequent H1s behave like section breaks
                flush()
                section, subsection = title, None
            elif level == 2:
                flush()
                section, subsection = title, None
            else:
                flush()
                subsection = title
        else:
            current.append(line)
    flush()
    return blocks


def _heading_prefix(block: Dict) -> str:
    if block["is_preamble"]:
        return f"# {block['section']}\n"
    prefix = f"## {block['section']}\n"
    if block["subsection"]:
        prefix += f"### {block['subsection']}\n"
    return prefix


def _pack_sentences(body: str, budget: int) -> List[str]:
    """Pack sentences into pieces of <= budget chars, one-sentence overlap."""
    normalized = re.sub(r"\s*\n\s*", " ", body).strip()
    sentences = [s.strip() for s in _SENTENCE_SPLIT.split(normalized) if s.strip()]
    if not sentences:
        return []

    pieces: List[str] = []
    current: List[str] = []
    length = 0

    for sentence in sentences:
        # a single sentence longer than the budget is kept whole — cutting
        # mid-sentence is exactly what this chunker exists to avoid
        addition = len(sentence) + (1 if current else 0)
        if current and length + addition > budget:
            pieces.append(" ".join(current))
            overlap = current[-1]
            current = [overlap] if len(overlap) + len(sentence) + 1 <= budget else []
            length = len(overlap) if current else 0
            addition = len(sentence) + (1 if current else 0)
        current.append(sentence)
        length += addition

    if current:
        piece = " ".join(current)
        # drop a trailing piece that is pure overlap of the previous one
        if not (pieces and piece in pieces[-1]):
            pieces.append(piece)

    return pieces
