"""
Normalize retrieved roadmap.sh chunks into a three-phase learning blueprint.

Methodology (thesis appendix):
We group retrieved content into three phases by extracting ordered topic lines from
chunk text, then assigning the first third to Foundations, the middle third to
Intermediate, and the final third to Advanced. Heading-like lines (``##`` markers,
numbered lists, bullet prefixes) are preferred as milestone titles. When retrieval
returns fewer than three distinct topics, a deterministic assessment-aware template
is used instead (see ``_fallback_phases``).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field


DEFAULT_PHASE_HOURS = [80, 120, 160]
PHASE_TITLES = ("Foundations", "Intermediate", "Advanced")


@dataclass
class NormalizedPhase:
    phase_number: int
    title: str
    milestone_titles: list[str]
    estimated_hours: int
    source_doc_ids: list[str] = field(default_factory=list)
    source_urls: list[str] = field(default_factory=list)


_TOPIC_LINE = re.compile(
    r"^(?:[-*•]\s+|\d+[\.)]\s+|#{1,3}\s+)(.+)$",
    re.MULTILINE,
)


class RoadmapPathNormalizer:
    """Parse retrieved chunks into a structured 3-phase blueprint."""

    @staticmethod
    def _extract_topics(chunks: list[dict]) -> list[str]:
        seen: set[str] = set()
        topics: list[str] = []

        for chunk in chunks:
            content = str(chunk.get("content") or "")
            for match in _TOPIC_LINE.finditer(content):
                title = match.group(1).strip()
                title = re.sub(r"\[@?[^\]]+\]\([^)]+\)", "", title).strip()
                if len(title) < 4 or len(title) > 120:
                    continue
                key = title.lower()
                if key in seen:
                    continue
                seen.add(key)
                topics.append(title)

            if not topics:
                for line in content.splitlines():
                    cleaned = line.strip().strip("#").strip()
                    if 4 <= len(cleaned) <= 80 and cleaned[0].isupper():
                        key = cleaned.lower()
                        if key not in seen:
                            seen.add(key)
                            topics.append(cleaned)

        return topics[:15]

    @staticmethod
    def _split_topics(topics: list[str]) -> tuple[list[str], list[str], list[str]]:
        if not topics:
            return [], [], []
        count = len(topics)
        first_end = max(1, math.ceil(count / 3))
        second_end = max(first_end + 1, math.ceil((2 * count) / 3))
        return (
            topics[:first_end],
            topics[first_end:second_end],
            topics[second_end:] or topics[-1:],
        )

    @staticmethod
    def _collect_sources(chunks: list[dict]) -> tuple[list[str], list[str]]:
        doc_ids: list[str] = []
        urls: list[str] = []
        seen_urls: set[str] = set()
        for chunk in chunks:
            doc_id = str(chunk.get("doc_id") or "")
            if doc_id and doc_id not in doc_ids:
                doc_ids.append(doc_id)
            url = str(chunk.get("source_url") or "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                urls.append(url)
        return doc_ids, urls

    @classmethod
    def _fallback_phases(cls, role_key: str) -> list[NormalizedPhase]:
        """Deterministic template when retrieval yields no parseable topics."""
        role_label = role_key.replace("_", " ").title()
        templates = {
            1: ["Core language fundamentals", "Version control basics", "Development environment setup"],
            2: ["Framework essentials", "Database and persistence", "API design patterns"],
            3: ["Testing and reliability", "Deployment fundamentals", f"{role_label} portfolio project"],
        }
        return [
            NormalizedPhase(
                phase_number=index,
                title=f"{PHASE_TITLES[index - 1]} — {role_label}",
                milestone_titles=templates[index],
                estimated_hours=DEFAULT_PHASE_HOURS[index - 1],
            )
            for index in range(1, 4)
        ]

    @classmethod
    def normalize(cls, chunks: list[dict], role_key: str) -> list[NormalizedPhase]:
        """
        Parse headings/ordered topics from chunks into a 3-phase structure.

        Merge heuristic: all retrieved chunks contribute topics to one ordered list;
        phase boundaries split that list into early, middle, and late segments.
        """
        if not chunks:
            return cls._fallback_phases(role_key)

        topics = cls._extract_topics(chunks)
        doc_ids, urls = cls._collect_sources(chunks)

        if len(topics) < 3:
            phases = cls._fallback_phases(role_key)
            for phase in phases:
                phase.source_doc_ids = doc_ids
                phase.source_urls = urls
            return phases

        early, middle, late = cls._split_topics(topics)
        groups = [early, middle, late]

        phases: list[NormalizedPhase] = []
        for index, group in enumerate(groups, start=1):
            milestones = group or [f"{PHASE_TITLES[index - 1]} milestone"]
            phases.append(
                NormalizedPhase(
                    phase_number=index,
                    title=f"{PHASE_TITLES[index - 1]} — {role_key.replace('_', ' ').title()}",
                    milestone_titles=milestones[:4],
                    estimated_hours=DEFAULT_PHASE_HOURS[index - 1],
                    source_doc_ids=doc_ids,
                    source_urls=urls,
                )
            )
        return phases
