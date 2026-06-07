"""Backfill UserSkill rows from already-completed roadmap milestones."""

from django.core.management.base import BaseCommand

from apps.progress.models import MilestoneAchievement
from apps.users.milestone_skills import MilestoneSkillService


class Command(BaseCommand):
    help = "Grant profile skills for all completed milestones (idempotent backfill)"

    def handle(self, *args, **options):
        achievements = (
            MilestoneAchievement.objects.filter(is_deleted=False)
            .select_related("milestone", "user")
            .order_by("user_id", "milestone_id")
        )
        total = 0
        users_seen = set()
        for achievement in achievements:
            names = MilestoneSkillService.grant_milestone_skills(
                achievement.user, achievement.milestone
            )
            total += len(names)
            users_seen.add(achievement.user_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced skills from {achievements.count()} achievements "
                f"for {len(users_seen)} users ({total} skill updates)."
            )
        )
