"""Sync demonstrated assessment strengths into the user skill profile."""

from __future__ import annotations

from django.db import transaction

from apps.jobs.skill_matching import skills_from_assessment_strengths, skills_from_subskill_key
from apps.users.models import Skill, User, UserSkill
from apps.users.milestone_skills import _max_proficiency, _resolve_skill

PROFICIENCY_FROM_RATIO = (
    (0.9, "advanced"),
    (0.6, "intermediate"),
    (0.0, "beginner"),
)


def _proficiency_from_evidence(observed: float, target: float) -> str:
    if target <= 0:
        return "intermediate"
    ratio = observed / target
    for threshold, label in PROFICIENCY_FROM_RATIO:
        if ratio >= threshold:
            return label
    return "beginner"


class AssessmentSkillService:
    """Persist assessment strengths (gap <= 1) as UserSkill rows."""

    @staticmethod
    @transaction.atomic
    def sync_from_roadmap_signal(user: User, roadmap_signal: dict | None) -> list[str]:
        if not roadmap_signal:
            return []

        synced: list[str] = []
        for item in roadmap_signal.get("subskill_gaps") or []:
            if not isinstance(item, dict):
                continue
            if float(item.get("gap", 99)) > 1.0:
                continue

            observed = float(item.get("observed_level", 0))
            target = float(item.get("target_level", 1))
            proficiency = _proficiency_from_evidence(observed, target)

            for name in skills_from_subskill_key(str(item.get("subskill_key", ""))):
                skill = _resolve_skill(name)
                if not skill:
                    continue
                existing = UserSkill.objects.filter(
                    user=user, skill=skill, is_deleted=False
                ).first()
                final_proficiency = (
                    _max_proficiency(existing.proficiency_level, proficiency)
                    if existing
                    else proficiency
                )
                UserSkill.objects.update_or_create(
                    user=user,
                    skill=skill,
                    defaults={
                        "proficiency_level": final_proficiency,
                        "skill_type": existing.skill_type if existing else "hard",
                        "source": "assessment",
                        "is_deleted": False,
                    },
                )
                synced.append(skill.name)

        return synced
