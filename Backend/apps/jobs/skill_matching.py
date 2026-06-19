"""Shared skill normalization and career-path skill inference for job matching."""

from __future__ import annotations

from apps.users.models import User

# Map assessment subskill keys / career keywords → job-posting skill names
CAREER_DEFAULT_SKILLS: dict[str, list[str]] = {
    "backend": ["Python", "Django", "PostgreSQL", "REST API"],
    "front": ["JavaScript", "React", "TypeScript"],
    "frontend": ["JavaScript", "React", "TypeScript"],
    "data": ["Python", "SQL", "Pandas", "Data Analysis"],
    "full": ["Python", "JavaScript", "SQL"],
    "devops": ["Docker", "AWS", "Git"],
    "mobile": ["Flutter", "Dart"],
}

SUBSKILL_KEY_HINTS: tuple[tuple[str, str], ...] = (
    ("python", "Python"),
    ("django", "Django"),
    ("fastapi", "FastAPI"),
    ("react", "React"),
    ("javascript", "JavaScript"),
    ("typescript", "TypeScript"),
    ("sql", "SQL"),
    ("postgres", "PostgreSQL"),
    ("database", "PostgreSQL"),
    ("api", "REST API"),
    ("rest", "REST API"),
    ("docker", "Docker"),
    ("aws", "AWS"),
    ("pandas", "Pandas"),
    ("machine_learning", "Machine Learning"),
    ("data", "Data Analysis"),
)


def normalize_skill_name(name: str) -> str:
    return str(name or "").strip().lower()


def skills_from_subskill_key(key: str) -> list[str]:
    lowered = str(key or "").strip().lower()
    if not lowered:
        return []
    found: list[str] = []
    for fragment, skill in SUBSKILL_KEY_HINTS:
        if fragment in lowered and skill not in found:
            found.append(skill)
    return found


def skills_from_career_text(text: str) -> list[str]:
    lowered = str(text or "").lower()
    found: list[str] = []
    for keyword, skills in CAREER_DEFAULT_SKILLS.items():
        if keyword in lowered:
            for skill in skills:
                if skill not in found:
                    found.append(skill)
    return found


def compare_skill_sets(
    user_skills: set[str],
    job_skills: set[str],
) -> tuple[list[str], list[str], int]:
    """
    Case-insensitive overlap. Returns (matching, missing, match_score 0-100).
    """
    user_by_norm = {normalize_skill_name(s): s for s in user_skills if normalize_skill_name(s)}
    job_by_norm = {normalize_skill_name(s): s for s in job_skills if normalize_skill_name(s)}
    if not job_by_norm:
        return [], [], 0

    common = set(user_by_norm) & set(job_by_norm)
    matching = sorted(job_by_norm[key] for key in common)
    missing = sorted(job_by_norm[key] for key in job_by_norm if key not in common)
    score = int((len(common) / len(job_by_norm)) * 100)
    return matching, missing, score


def skills_from_assessment_strengths(roadmap_signal: dict) -> set[str]:
    """
    Skills the user has demonstrated on assessment (gap <= 1.0).

    Does NOT include priority_order or high-gap subskills — those are learning targets.
    """
    strengths: set[str] = set()
    for item in roadmap_signal.get("subskill_gaps") or []:
        if not isinstance(item, dict):
            continue
        if float(item.get("gap", 99)) > 1.0:
            continue
        strengths.update(skills_from_subskill_key(str(item.get("subskill_key", ""))))
    return strengths


def expand_skill_aliases(skills: set[str]) -> set[str]:
    """Map subskill labels/keys to canonical job-posting skill names."""
    expanded = set(skills)
    for skill in list(skills):
        expanded.update(skills_from_subskill_key(skill.replace(" ", "_")))
    return {item for item in expanded if item}


def collect_user_match_skills(user: User) -> set[str]:
    """
    Build the skill set used for job overlap matching.

    Sources (union):
      - UserSkill profile (includes milestone grants and assessment sync)
      - Latest assessment demonstrated strengths (live signal before profile sync)
    """
    from apps.assessments.models import AssessmentResult
    from apps.users.models import UserSkill

    profile_skills = set(
        UserSkill.objects.filter(user=user, is_deleted=False).values_list(
            "skill__name", flat=True
        )
    )

    assessment_strengths: set[str] = set()
    try:
        latest = (
            AssessmentResult.objects.select_related("assessment")
            .filter(assessment__user=user, is_deleted=False)
            .order_by("-created_at")
            .first()
        )
        if latest and isinstance(latest.roadmap_signal, dict):
            assessment_strengths = skills_from_assessment_strengths(latest.roadmap_signal)
    except Exception:
        pass

    combined = profile_skills | assessment_strengths
    if not combined:
        return set()
    return expand_skill_aliases(combined)
