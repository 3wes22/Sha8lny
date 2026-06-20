"""Deterministic skill/role/level course matcher.

Graceful fallback for roadmap course-matching when the embedding vector store
(chromadb) is unavailable: ranks the real course catalog against a milestone by
curated-skill overlap, role tag, level alignment, and quality. Fully offline,
deterministic, and reproducible — which also makes it easy to evaluate and to
defend ("transparent skill/role/level ranking").
"""

from __future__ import annotations

import math
import re
from typing import Any

_LEVEL_RANK = {"beginner": 0, "intermediate": 1, "advanced": 2}

# Generic words that carry no role/skill signal — excluded from token overlap.
_STOPWORDS = {
    "the", "and", "for", "with", "your", "you", "this", "that", "from", "into",
    "course", "courses", "specialization", "professional", "certificate",
    "introduction", "intro", "fundamentals", "basics", "basic", "beginner",
    "beginners", "intermediate", "advanced", "learn", "learning", "build",
    "building", "guide", "complete", "essential", "essentials", "mastering",
    "master", "practical", "hands", "using", "getting", "started", "skills",
    "development", "developer", "programming", "applied", "project", "projects",
    "understanding", "introduction", "part", "level", "online", "google",
    "microsoft", "meta", "ibm", "aws",
}


def _tokens(text: Any) -> set[str]:
    return {
        tok
        for tok in re.split(r"[^a-z0-9+#.]+", str(text or "").lower())
        if len(tok) >= 3 and tok not in _STOPWORDS
    }


def target_level_for_order(phase_order: int) -> str:
    """Map a 1-indexed ladder band position to an expected course level."""
    if phase_order <= 2:
        return "beginner"
    if phase_order == 3:
        return "intermediate"
    return "advanced"


class CourseCatalog:
    """Cached lightweight view of the published course catalog for scoring."""

    _entries: list[dict[str, Any]] | None = None
    _signature: int | None = None

    @classmethod
    def reset(cls) -> None:
        cls._entries = None
        cls._signature = None

    @classmethod
    def _load(cls) -> list[dict[str, Any]]:
        from apps.courses.models import Course

        signature = Course.objects.filter(is_deleted=False, is_published=True).count()
        if cls._entries is not None and cls._signature == signature:
            return cls._entries

        entries: list[dict[str, Any]] = []
        rows = Course.objects.filter(is_deleted=False, is_published=True).only(
            "id", "title", "level", "rating", "total_enrollments", "metadata"
        )
        for course in rows:
            metadata = course.metadata if isinstance(course.metadata, dict) else {}
            skills = metadata.get("skills") or []
            roles = metadata.get("roles") or []
            skill_tokens: set[str] = set()
            for skill in skills:
                skill_tokens |= _tokens(skill)
            entries.append(
                {
                    "course_id": str(course.id),
                    "title": course.title,
                    "title_tokens": _tokens(course.title),
                    "skill_tokens": skill_tokens,
                    "roles": set(roles),
                    "level": course.level,
                    "rating": float(course.rating) if course.rating is not None else 0.0,
                    "enrollments": int(course.total_enrollments or 0),
                }
            )
        cls._entries = entries
        cls._signature = signature
        return entries


def match_courses(
    *,
    target_career: str,
    role_key: str | None,
    milestone_title: str,
    milestone_skills: list[str],
    target_level: str | None,
    top_k: int = 2,
) -> list[dict[str, Any]]:
    """Return up to ``top_k`` ranked course matches: {course_id, title, score}.

    score is normalized to [0, 1] so it slots into the same contract the
    embedding matcher returns.
    """
    query_tokens: set[str] = _tokens(milestone_title) | _tokens(target_career)
    for skill in milestone_skills or []:
        query_tokens |= _tokens(skill)
    if not query_tokens:
        return []

    catalog = CourseCatalog._load()
    scored: list[tuple[float, dict[str, Any]]] = []
    for entry in catalog:
        skill_hits = len(query_tokens & entry["skill_tokens"])
        title_hits = len(query_tokens & entry["title_tokens"])
        role_match = bool(role_key) and role_key in entry["roles"]

        # A candidate must be on-topic: share a curated skill/title token OR be
        # tagged for this role. Otherwise it is not a real match.
        if skill_hits == 0 and title_hits == 0 and not role_match:
            continue

        # Curated-skill overlap is the strongest signal and must be able to beat a
        # role-only match (so a Docker course outranks a generic backend capstone
        # for a "Containerization with Docker" milestone).
        raw = (4.0 * skill_hits) + (1.5 * title_hits)
        if role_match:
            raw += 2.0
        if target_level and entry["level"] in _LEVEL_RANK and target_level in _LEVEL_RANK:
            distance = abs(_LEVEL_RANK[entry["level"]] - _LEVEL_RANK[target_level])
            raw += 2.0 if distance == 0 else (1.0 if distance == 1 else 0.0)

        # Quality tiebreakers (small, never dominate relevance).
        raw += 0.4 * (entry["rating"] / 5.0)
        raw += 0.2 * min(1.0, math.log10(entry["enrollments"] + 1) / 6.0)

        score = raw / (raw + 6.0)  # squashes to (0, 1), ~0.5 at raw=6
        scored.append((score, entry))

    scored.sort(key=lambda item: (item[0], item[1]["rating"], item[1]["enrollments"]), reverse=True)
    return [
        {"course_id": entry["course_id"], "title": entry["title"], "score": round(score, 4)}
        for score, entry in scored[:top_k]
    ]
