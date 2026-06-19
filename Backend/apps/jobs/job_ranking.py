"""Bridge Django job matching to ai-models LightGBM ranker."""

from __future__ import annotations

from typing import Any

from apps.core.ai_bridge import ensure_ai_models_path
from apps.jobs.experience_matching import resolve_user_career_level
from apps.jobs.services import JobService
from apps.users.models import User


class JobRankingIntegration:
    """Rank jobs with LightGBM when model file exists; else overlap-only."""

    @staticmethod
    def rank_user_jobs(user: User, jobs: list, *, limit: int = 20) -> list[dict[str, Any]]:
        user_skills = sorted(JobService._user_skill_names(user))
        if not jobs:
            return []

        ensure_ai_models_path()
        from recommendations.feature_engineering import job_dict_from_model
        from recommendations.ranker import JobRanker

        job_dicts = [job_dict_from_model(job) for job in jobs]
        ranker = JobRanker()
        ranked = ranker.rank_jobs(
            user_skills,
            job_dicts,
            user_experience_level=resolve_user_career_level(user),
            limit=limit,
        )

        job_by_id = {str(job.id): job for job in jobs}
        results = []
        for item in ranked:
            job_id = str(item["job"].get("id"))
            django_job = job_by_id.get(job_id)
            if not django_job:
                continue
            explanation = item.get("explanation") or {
                "matching_skills": item.get("matching_skills", []),
                "missing_skills": item.get("missing_skills", []),
                "top_factors": [],
            }
            results.append(
                {
                    "job": django_job,
                    "match_score": item["match_score"],
                    "matching_skills": item.get("matching_skills", []),
                    "missing_skills": item.get("missing_skills", []),
                    "explanation": explanation,
                    "ranker_used": ranker.is_available,
                }
            )
        return results
