"""Grant profile skills when roadmap milestones are completed."""

from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.utils.text import slugify

from apps.users.models import Skill, User, UserSkill
from apps.roadmaps.models import RoadmapMilestone

PROFICIENCY_RANK = ("beginner", "intermediate", "advanced", "expert")


def _max_proficiency(current: str | None, proposed: str) -> str:
    current_rank = PROFICIENCY_RANK.index(current) if current in PROFICIENCY_RANK else 0
    proposed_rank = PROFICIENCY_RANK.index(proposed) if proposed in PROFICIENCY_RANK else 1
    return PROFICIENCY_RANK[max(current_rank, proposed_rank)]


def _resolve_skill(raw: Any) -> Skill | None:
    """Resolve milestone.skills entry (UUID string or skill name)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    try:
        skill_id = uuid.UUID(text)
        return Skill.objects.filter(id=skill_id, is_deleted=False).first()
    except (ValueError, AttributeError):
        pass

    try:
        return Skill.objects.get(name__iexact=text, is_deleted=False)
    except Skill.DoesNotExist:
        return Skill.objects.create(
            name=text,
            slug=slugify(text) or text.lower().replace(" ", "-"),
            category="technical",
        )


class MilestoneSkillService:
    """Sync UserSkill rows from completed roadmap milestones."""

    @staticmethod
    @transaction.atomic
    def grant_milestone_skills(user: User, milestone: RoadmapMilestone) -> list[str]:
        """
        Idempotently grant skills listed on a milestone to the user's profile.

        Returns canonical skill names granted/updated.
        """
        granted: list[str] = []
        for raw in milestone.skills or []:
            skill = _resolve_skill(raw)
            if not skill:
                continue

            existing = UserSkill.objects.filter(
                user=user, skill=skill, is_deleted=False
            ).first()
            proficiency = "intermediate"
            if existing and existing.proficiency_level:
                proficiency = _max_proficiency(existing.proficiency_level, "intermediate")

            UserSkill.objects.update_or_create(
                user=user,
                skill=skill,
                defaults={
                    "proficiency_level": proficiency,
                    "skill_type": existing.skill_type if existing else "hard",
                    "source": "roadmap_milestone",
                    "is_deleted": False,
                },
            )
            granted.append(skill.name)
        return granted
