"""Seed demo courses for roadmap course matching."""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.courses.models import Course, CoursePlatform, CourseSkill
from apps.users.models import Skill


DEMO_COURSES = [
    {
        "external_id": "demo-python-backend",
        "title": "Python Backend Foundations",
        "description": "Core Python syntax, OOP, and backend API fundamentals for junior developers.",
        "level": "beginner",
        "skills": ["Python", "REST APIs", "Git"],
    },
    {
        "external_id": "demo-sql-backend",
        "title": "SQL for Backend Developers",
        "description": "Query design, indexing, joins, and relational modeling for production APIs.",
        "level": "intermediate",
        "skills": ["SQL", "PostgreSQL", "Database Design"],
    },
    {
        "external_id": "demo-git-workflows",
        "title": "Git Workflows for Teams",
        "description": "Branching, pull requests, code review, and release hygiene for software teams.",
        "level": "beginner",
        "skills": ["Git", "Collaboration"],
    },
    {
        "external_id": "demo-react-frontend",
        "title": "React Frontend Essentials",
        "description": "Components, hooks, state management, and API integration for modern web apps.",
        "level": "intermediate",
        "skills": ["React", "TypeScript", "JavaScript"],
    },
    {
        "external_id": "demo-data-python",
        "title": "Python for Data Analysis",
        "description": "Pandas, visualization, and exploratory analysis workflows for data roles.",
        "level": "intermediate",
        "skills": ["Python", "Data Analysis", "Pandas"],
    },
    {
        "external_id": "demo-devops-basics",
        "title": "DevOps and CI/CD Basics",
        "description": "Containers, pipelines, and deployment fundamentals for cloud-native teams.",
        "level": "intermediate",
        "skills": ["Docker", "CI/CD", "Linux"],
    },
]


class Command(BaseCommand):
    help = "Seed demo courses for roadmap embedding-based matching."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing demo-platform courses before seeding.",
        )

    def handle(self, *args, **options) -> None:
        platform, _ = CoursePlatform.objects.get_or_create(
            slug="sha8alny-demo-library",
            defaults={
                "name": "Sha8alny Demo Library",
                "website_url": "https://sha8alny.local/courses",
                "integration_type": CoursePlatform.MANUAL,
                "is_active": True,
            },
        )

        if options["clear"]:
            Course.objects.filter(platform=platform).delete()
            self.stdout.write("Cleared existing demo courses.")

        created_count = 0
        for item in DEMO_COURSES:
            course, created = Course.objects.update_or_create(
                platform=platform,
                external_id=item["external_id"],
                defaults={
                    "title": item["title"],
                    "slug": slugify(item["title"])[:240],
                    "description": item["description"],
                    "short_description": item["description"][:240],
                    "url": f"https://sha8alny.local/courses/{item['external_id']}",
                    "level": item["level"],
                    "course_type": Course.VIDEO,
                    "is_free": True,
                    "is_published": True,
                },
            )
            if created:
                created_count += 1

            CourseSkill.objects.filter(course=course).delete()
            for skill_name in item["skills"]:
                skill, _ = Skill.objects.get_or_create(name=skill_name)
                CourseSkill.objects.get_or_create(
                    course=course,
                    skill=skill,
                    defaults={"is_primary": True},
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo courses ready ({created_count} created, {len(DEMO_COURSES)} total)."
            )
        )
