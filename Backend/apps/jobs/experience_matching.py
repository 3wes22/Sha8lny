"""Career-level resolution and job filtering for personalized recommendations."""

from __future__ import annotations

from apps.jobs.models import Job
from apps.users.models import User, UserSkill

# Job.experience_level values
LEVEL_RANK: dict[str, int] = {
    "entry": 0,
    "mid": 1,
    "senior": 2,
    "lead": 3,
    "executive": 4,
}

ROADMAP_TEMPLATE_LEVEL_MAP: dict[str, str] = {
    "entry_level": "entry",
    "mid_level": "mid",
    "senior_level": "senior",
    "lead_level": "lead",
}

PROFICIENCY_LEVEL_MAP: dict[str, str] = {
    "beginner": "entry",
    "intermediate": "mid",
    "advanced": "senior",
    "expert": "senior",
}


def normalize_experience_level(raw: str | None, *, default: str = "mid") -> str:
    """Map assorted labels to Job.experience_level choices."""
    if not raw:
        return default
    lowered = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    if lowered in LEVEL_RANK:
        return lowered
    if lowered in ROADMAP_TEMPLATE_LEVEL_MAP:
        return ROADMAP_TEMPLATE_LEVEL_MAP[lowered]
    if lowered in ("junior", "graduate", "intern", "internship", "fresh", "fresher"):
        return "entry"
    if lowered in ("middle", "intermediate", "midlevel"):
        return "mid"
    if lowered in ("sr", "principal", "staff"):
        return "senior"
    if lowered in ("manager", "head", "director"):
        return "lead"
    if "entry" in lowered:
        return "entry"
    if "senior" in lowered:
        return "senior"
    if "lead" in lowered:
        return "lead"
    if "executive" in lowered or "director" in lowered:
        return "executive"
    if "mid" in lowered:
        return "mid"
    return default


def level_from_text(text: str | None) -> str | None:
    """Infer a job level from free text (title, roadmap fields)."""
    if not text:
        return None
    lowered = str(text).lower()
    if any(token in lowered for token in ("intern", "graduate", "entry level", "entry-level", "junior")):
        return "entry"
    if any(token in lowered for token in ("principal", "staff engineer", "senior ")):
        return "senior"
    if any(token in lowered for token in ("team lead", "tech lead", "engineering manager", " head of ")):
        return "lead"
    if "senior" in lowered or " sr " in f" {lowered} ":
        return "senior"
    if "lead" in lowered:
        return "lead"
    if "executive" in lowered or "director" in lowered:
        return "executive"
    if "mid" in lowered:
        return "mid"
    return None


def level_rank(level: str) -> int:
    return LEVEL_RANK.get(normalize_experience_level(level), 1)


def effective_job_level(job: Job) -> str:
    """Combine stored job level with senior/entry signals in the title."""
    stored = normalize_experience_level(job.experience_level or "mid")
    title_level = level_from_text(job.title)
    if not title_level:
        return stored
    if level_rank(title_level) > level_rank(stored):
        return title_level
    return stored


def resolve_user_career_level(user: User) -> str:
    """
    Infer the user's current career band for job filtering.

    Priority: active roadmap (template + text) → assessment score → skill proficiency → mid.
    """
    try:
        from apps.roadmaps.models import Roadmap

        roadmap = (
            Roadmap.objects.filter(
                user=user,
                is_deleted=False,
                status__in=[Roadmap.ACTIVE, Roadmap.IN_PROGRESS],
            )
            .select_related("template")
            .order_by("-updated_at")
            .first()
        )
        if roadmap:
            if roadmap.template and roadmap.template.career_level:
                mapped = ROADMAP_TEMPLATE_LEVEL_MAP.get(roadmap.template.career_level)
                if mapped:
                    return mapped
            for field in (roadmap.current_level, roadmap.target_level, roadmap.title):
                parsed = level_from_text(field)
                if parsed:
                    return parsed
    except Exception:
        pass

    try:
        from apps.assessments.models import AssessmentResult

        latest = (
            AssessmentResult.objects.filter(
                assessment__user=user,
                is_deleted=False,
            )
            .order_by("-created_at")
            .first()
        )
        if latest and latest.overall_score is not None:
            score = float(latest.overall_score)
            if score < 45:
                return "entry"
            if score < 72:
                return "mid"
            return "senior"
    except Exception:
        pass

    proficiencies = list(
        UserSkill.objects.filter(user=user, is_deleted=False).values_list(
            "proficiency_level", flat=True
        )
    )
    if proficiencies:
        ranks = [
            level_rank(PROFICIENCY_LEVEL_MAP.get(str(item), "mid"))
            for item in proficiencies
            if item
        ]
        if ranks:
            # Conservative: use median-ish band (floor of average rank)
            avg = sum(ranks) / len(ranks)
            if avg < 0.75:
                return "entry"
            if avg < 1.75:
                return "mid"
            if avg < 2.75:
                return "senior"
            return "lead"

    return "mid"


def max_job_rank_for_user(user_level: str, *, allow_stretch: bool = False) -> int:
    """Highest job rank to include; optional +1 band for reach roles."""
    stretch = 1 if allow_stretch else 0
    return level_rank(user_level) + stretch


def job_matches_user_level(
    job: Job,
    user_level: str,
    *,
    allow_stretch: bool = False,
) -> bool:
    """True when the job is at or below the user's allowed career band."""
    job_level = effective_job_level(job)
    return level_rank(job_level) <= max_job_rank_for_user(user_level, allow_stretch=allow_stretch)


def experience_fit_label(job: Job, user_level: str) -> str:
    """aligned | stretch | above_level (should be filtered out)."""
    job_level = effective_job_level(job)
    user_rank = level_rank(user_level)
    job_rank = level_rank(job_level)
    if job_rank <= user_rank:
        return "aligned"
    if job_rank == user_rank + 1:
        return "stretch"
    return "above_level"


def filter_jobs_for_user_level(
    jobs: list[Job],
    user_level: str,
    *,
    allow_stretch: bool = False,
) -> list[Job]:
    return [
        job
        for job in jobs
        if job_matches_user_level(job, user_level, allow_stretch=allow_stretch)
    ]
