"""Evaluate roadmap course-matching quality against the real ingested catalog.

For every course-type milestone across all 8 role ladders, runs the deterministic
matcher and measures:
  - coverage:        % of milestones that get >=1 course match
  - role-appropriate: % of top matches tagged with the milestone's role
  - level-appropriate: % of top matches within +/-1 difficulty level of the band

Writes a JSON artifact to ai-models/eval_results/courses/ and prints a summary.
Run after `ingest_courses` (needs the catalog loaded). Defense-facing evidence.

Usage: python manage.py eval_course_matching
"""

from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.assessments.role_graph import SUPPORTED_ROLES
from apps.courses.matching import CourseCatalog, _LEVEL_RANK, match_courses, target_level_for_order
from apps.courses.models import Course
from apps.roadmaps.ladder import build_ladder_blueprint

CAREER_BY_ROLE = {
    "backend": "Backend Developer",
    "frontend": "Frontend Developer",
    "data_science": "Data Scientist",
    "fullstack": "Full Stack Developer",
    "devops": "DevOps Engineer",
    "android": "Android Developer",
    "machine_learning_engineer": "Machine Learning Engineer",
    "ui_ux_designer": "UI/UX Designer",
}


class Command(BaseCommand):
    help = "Evaluate roadmap course-matching quality against the ingested catalog."

    def handle(self, *args, **options):
        CourseCatalog.reset()
        catalog_size = Course.objects.filter(is_published=True, is_deleted=False).count()
        if catalog_size == 0:
            self.stdout.write(self.style.ERROR("Course catalog is empty — run ingest_courses first."))
            return

        per_role: dict[str, dict] = {}
        totals = {"milestones": 0, "covered": 0, "role_ok": 0, "level_ok": 0}

        for role in SUPPORTED_ROLES:
            career = CAREER_BY_ROLE[role]
            phases = build_ladder_blueprint(
                target_career=career, current_level="beginner",
                priority_skills=[], gaps=[], top_skills=[], strengths=[], weekly_hours=8,
            )
            stats = {"milestones": 0, "covered": 0, "role_ok": 0, "level_ok": 0}
            for order, phase in enumerate(phases, start=1):
                target_level = target_level_for_order(order)
                for milestone in phase["milestones"]:
                    if milestone.get("type") != "course":
                        continue
                    stats["milestones"] += 1
                    matches = match_courses(
                        target_career=career, role_key=role,
                        milestone_title=milestone["title"],
                        milestone_skills=milestone.get("skills", []),
                        target_level=target_level, top_k=1,
                    )
                    if not matches:
                        continue
                    stats["covered"] += 1
                    course = Course.objects.get(id=matches[0]["course_id"])
                    roles = (course.metadata or {}).get("roles", [])
                    if role in roles:
                        stats["role_ok"] += 1
                    if course.level in _LEVEL_RANK and target_level in _LEVEL_RANK:
                        if abs(_LEVEL_RANK[course.level] - _LEVEL_RANK[target_level]) <= 1:
                            stats["level_ok"] += 1
            per_role[role] = stats
            for key in totals:
                totals[key] += stats[key]

        def pct(num: int, den: int) -> float:
            return round(100.0 * num / den, 1) if den else 0.0

        report = {
            "catalog_size": catalog_size,
            "method": "deterministic skill/role/level matcher over the 8-role ladders, top-1",
            "totals": {
                "milestones": totals["milestones"],
                "coverage_pct": pct(totals["covered"], totals["milestones"]),
                "role_appropriate_pct": pct(totals["role_ok"], totals["covered"]),
                "level_appropriate_pct": pct(totals["level_ok"], totals["covered"]),
            },
            "per_role": {
                role: {
                    "milestones": s["milestones"],
                    "coverage_pct": pct(s["covered"], s["milestones"]),
                    "role_appropriate_pct": pct(s["role_ok"], s["covered"]),
                    "level_appropriate_pct": pct(s["level_ok"], s["covered"]),
                }
                for role, s in per_role.items()
            },
        }

        repo_root = Path(__file__).resolve().parents[5]
        out_dir = repo_root / "ai-models" / "eval_results" / "courses"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "course_matching_eval.json"
        out_path.write_text(json.dumps(report, indent=2))

        t = report["totals"]
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("COURSE-MATCHING EVAL (deterministic matcher)"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"catalog size .............. {catalog_size} courses")
        self.stdout.write(f"course-milestones evaluated  {t['milestones']}")
        self.stdout.write(f"coverage .................. {t['coverage_pct']}%")
        self.stdout.write(f"role-appropriate (top-1) .. {t['role_appropriate_pct']}%")
        self.stdout.write(f"level-appropriate (+/-1) .. {t['level_appropriate_pct']}%")
        self.stdout.write("")
        self.stdout.write(f"{'role':28} {'cov%':>6} {'role%':>7} {'lvl%':>6}")
        for role, s in report["per_role"].items():
            self.stdout.write(
                f"{role:28} {s['coverage_pct']:>6} {s['role_appropriate_pct']:>7} {s['level_appropriate_pct']:>6}"
            )
        self.stdout.write("=" * 60)
        self.stdout.write(f"wrote {out_path.relative_to(repo_root)}")
