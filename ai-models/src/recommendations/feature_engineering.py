"""
Feature vectors for job–user ranking (LightGBM).

Features (v1):
  1. skill_embedding_cosine
  2. required_skill_overlap_ratio
  3. experience_level_delta
  4. job_freshness_score
  5. location_match
"""

from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, Sequence

import numpy as np

FEATURE_NAMES = (
    "skill_embedding_cosine",
    "required_skill_overlap_ratio",
    "experience_level_delta",
    "job_freshness_score",
    "location_match",
)

_LEVEL_ORDER = {
    "entry": 0,
    "mid": 1,
    "senior": 2,
    "lead": 3,
    "executive": 4,
}

_EMBEDDER = None


def _embeddings_enabled() -> bool:
    # Explicit env override first, so eval artifacts are reproducible regardless
    # of whether sentence-transformers happens to be installed. Set
    # JOB_RANKER_SKIP_EMBEDDINGS=1 to force the deterministic, embedding-free path.
    env = os.environ.get("JOB_RANKER_SKIP_EMBEDDINGS")
    if env is not None:
        return env.strip().lower() not in {"1", "true", "yes", "on"}
    try:
        from django.conf import settings

        return not getattr(settings, "JOB_RANKER_SKIP_EMBEDDINGS", False)
    except Exception:
        return True


def _get_embedder():
    global _EMBEDDER
    if _EMBEDDER is not None:
        return _EMBEDDER
    if not _embeddings_enabled():
        _EMBEDDER = False
        return _EMBEDDER
    try:
        from sentence_transformers import SentenceTransformer

        # CPU avoids MPS temp files (fails when disk is full on macOS).
        _EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    except Exception:
        _EMBEDDER = False
    return _EMBEDDER


def embeddings_available() -> bool:
    """True when the sentence-transformers embedder is loaded and usable.

    When False, ``skill_embedding_cosine`` returns 0.0 for every pair, so the
    embedding feature is effectively disabled (relevant for interpreting eval
    metrics — the model loses its main differentiating signal).
    """
    return bool(_get_embedder())


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom <= 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def skill_embedding_cosine(user_skills: Sequence[str], job: dict[str, Any]) -> float:
    embedder = _get_embedder()
    if not embedder or not user_skills:
        return 0.0
    user_text = ", ".join(sorted({str(item).strip() for item in user_skills if str(item).strip()}))
    job_text = " ".join(
        filter(
            None,
            [
                str(job.get("title") or ""),
                str(job.get("description") or ""),
                str(job.get("requirements") or ""),
                ", ".join(job.get("required_skills") or []),
            ],
        )
    )
    if not user_text.strip() or not job_text.strip():
        return 0.0
    vectors = embedder.encode([user_text, job_text], normalize_embeddings=True)
    return _cosine(np.asarray(vectors[0]), np.asarray(vectors[1]))


def required_skill_overlap_ratio(
    user_skills: set[str],
    required_skills: set[str],
) -> float:
    if not required_skills:
        return 0.0
    user_norm = {str(s).strip().lower() for s in user_skills if str(s).strip()}
    req_norm = {str(s).strip().lower() for s in required_skills if str(s).strip()}
    if not req_norm:
        return 0.0
    return len(user_norm & req_norm) / len(req_norm)


def experience_level_delta(user_level: str, job_level: str) -> float:
    user_rank = _LEVEL_ORDER.get(str(user_level or "mid").lower(), 1)
    job_rank = _LEVEL_ORDER.get(str(job_level or "mid").lower(), 1)
    return float(abs(user_rank - job_rank))


def job_freshness_score(posted_date: date | datetime | str | None, *, today: date | None = None) -> float:
    if today is None:
        today = date.today()
    if posted_date is None:
        return 0.0
    if isinstance(posted_date, datetime):
        posted = posted_date.date()
    elif isinstance(posted_date, str):
        try:
            posted = date.fromisoformat(posted_date[:10])
        except ValueError:
            return 0.0
    else:
        posted = posted_date
    age_days = max((today - posted).days, 0)
    return float(1.0 / (1.0 + age_days / 30.0))


def location_match(job_country: str, preferred_country: str = "Egypt") -> float:
    if not job_country:
        return 0.5
    return 1.0 if str(job_country).strip().lower() == preferred_country.strip().lower() else 0.0


def build_feature_vector(
    user_skills: Sequence[str],
    job: dict[str, Any],
    *,
    user_experience_level: str = "mid",
    preferred_country: str = "Egypt",
) -> np.ndarray:
    skill_set = {str(item).strip() for item in user_skills if str(item).strip()}
    required = {str(item).strip() for item in (job.get("required_skills") or []) if str(item).strip()}
    values = [
        skill_embedding_cosine(skill_set, job),
        required_skill_overlap_ratio(skill_set, required),
        experience_level_delta(user_experience_level, str(job.get("experience_level") or "mid")),
        job_freshness_score(job.get("posted_date")),
        location_match(str(job.get("location_country") or "Egypt"), preferred_country),
    ]
    return np.asarray(values, dtype=np.float32)


def job_dict_from_model(job) -> dict[str, Any]:
    """Convert a Django Job instance (with prefetched job_skills) to a feature dict."""
    required_skills = list(
        job.job_skills.filter(is_required=True).values_list("skill__name", flat=True)
    )
    return {
        "id": str(job.id),
        "title": job.title,
        "description": job.description,
        "requirements": job.requirements,
        "experience_level": job.experience_level,
        "posted_date": job.posted_date,
        "location_country": job.location_country,
        "required_skills": required_skills,
    }
