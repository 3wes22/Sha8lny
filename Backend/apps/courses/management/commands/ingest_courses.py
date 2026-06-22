"""Ingest the cleaned Coursera career-course catalog into the Course models.

Reads ai-models/data/courses/coursera_career_courses.json (produced by
build_course_catalog.py), upserts each course under a real "Coursera" platform,
and (optionally) purges the legacy hand-authored demo/junk courses. Rebuilds the
embedding index when the vector store is available; otherwise roadmap matching
uses the deterministic skill/role/level fallback.

Usage:
    python manage.py ingest_courses
    python manage.py ingest_courses --purge-demo
    python manage.py ingest_courses --limit 200 --no-rebuild-index
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.courses.models import Course, CoursePlatform

DEFAULT_PATH = "ai-models/data/courses/coursera_career_courses.json"
PROVIDER_NAME = "Coursera"
DATASET_SOURCE = "azrai99/coursera-course-dataset (Hugging Face, Apache-2.0)"

_VALID_LEVELS = {"beginner", "intermediate", "advanced", "all_levels"}


class Command(BaseCommand):
    help = "Ingest the cleaned Coursera career-course catalog into the Course models."

    def add_arguments(self, parser):
        parser.add_argument("--path", default=DEFAULT_PATH, help="Path to the cleaned catalog JSON.")
        parser.add_argument("--limit", type=int, default=0, help="Ingest at most N courses (0 = all).")
        parser.add_argument(
            "--purge-demo",
            action="store_true",
            help="Hard-delete legacy demo/junk courses + their non-Coursera platforms first.",
        )
        parser.add_argument(
            "--no-rebuild-index",
            action="store_true",
            help="Skip rebuilding the embedding index (it rebuilds by default when available).",
        )

    def _resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if candidate.is_absolute() and candidate.exists():
            return candidate
        repo_root = Path(__file__).resolve().parents[5]
        resolved = repo_root / path
        if not resolved.exists():
            raise CommandError(f"Catalog file not found: {resolved}")
        return resolved

    @staticmethod
    def _decimal_rating(value) -> Decimal | None:
        if value is None:
            return None
        try:
            rating = Decimal(str(value)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return None
        return max(Decimal("0.00"), min(Decimal("5.00"), rating))

    @staticmethod
    def _external_id(url: str) -> str:
        path = urlparse(url).path.strip("/")
        return path or url

    def _purge_demo(self) -> None:
        junk_courses = Course.all_objects.filter(
            url__iregex=r"(demo\.sha8alny\.local|x\.com|//x\.)"
        )
        # Also any course whose platform is a known demo/junk platform.
        junk_platforms = CoursePlatform.all_objects.exclude(slug=slugify(PROVIDER_NAME))
        course_n = 0
        for course in Course.all_objects.filter(platform__in=junk_platforms):
            course.delete(hard=True)
            course_n += 1
        for course in junk_courses:
            course.delete(hard=True)
            course_n += 1
        platform_n = 0
        for platform in junk_platforms:
            if not platform.courses.exists():
                platform.delete(hard=True)
                platform_n += 1
        self.stdout.write(
            self.style.WARNING(f"Purged {course_n} demo/junk course(s) and {platform_n} platform(s).")
        )

    @transaction.atomic
    def handle(self, *args, **options):
        catalog_path = self._resolve_path(options["path"])
        records = json.loads(catalog_path.read_text())
        if options["limit"]:
            records = records[: options["limit"]]
        self.stdout.write(f"Loaded {len(records)} catalog records from {catalog_path.name}.")

        if options["purge_demo"]:
            self._purge_demo()

        platform, _ = CoursePlatform.all_objects.get_or_create(
            slug=slugify(PROVIDER_NAME),
            defaults={
                "name": PROVIDER_NAME,
                "website_url": "https://www.coursera.org",
                "integration_type": CoursePlatform.SCRAPING,
                "is_active": True,
            },
        )
        platform.is_deleted = False
        platform.deleted_at = None
        platform.description = "Public Coursera course metadata catalog (dataset-sourced)."
        platform.metadata = {"dataset_source": DATASET_SOURCE, "license": "Apache-2.0"}
        platform.last_synced_at = timezone.now()
        platform.save()

        created = updated = skipped = 0
        for record in records:
            url = str(record.get("url") or "").strip()
            title = str(record.get("title") or "").strip()
            if not url or not title:
                skipped += 1
                continue

            level = record.get("level")
            level = level if level in _VALID_LEVELS else Course.ALL_LEVELS
            skills = [str(s).strip() for s in (record.get("skills") or []) if str(s).strip()]
            description = str(record.get("description") or "").strip()

            defaults = {
                "title": title[:500],
                "slug": (slugify(title) or "course")[:255],
                "description": description,
                "short_description": description[:497] + "..." if len(description) > 500 else description,
                "url": url[:1000],
                "level": level,
                "course_type": Course.VIDEO,
                "language": "English",
                "is_free": True,  # Coursera courses are auditable for free
                "rating": self._decimal_rating(record.get("rating")),
                "total_reviews": int(record.get("num_reviews") or 0),
                "total_enrollments": int(record.get("enrolled") or 0),
                "is_published": True,
                "has_certificate": True,
                "learning_outcomes": skills[:8],
                "metadata": {
                    "skills": skills,
                    "roles": record.get("roles") or [],
                    "organization": record.get("organization"),
                    "instructor": record.get("instructor"),
                    "satisfaction_rate": record.get("satisfaction_rate"),
                    "provider": PROVIDER_NAME,
                    "dataset_source": DATASET_SOURCE,
                },
                "is_deleted": False,
                "deleted_at": None,
            }

            _, was_created = Course.all_objects.update_or_create(
                platform=platform,
                external_id=self._external_id(url),
                defaults=defaults,
            )
            created += int(was_created)
            updated += int(not was_created)

        platform.total_courses = platform.courses.count()
        platform.save(update_fields=["total_courses", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Ingested catalog: {created} created, {updated} updated, {skipped} skipped. "
                f"'{PROVIDER_NAME}' now has {platform.total_courses} courses."
            )
        )

        if not options["no_rebuild_index"]:
            self._rebuild_index()

    def _rebuild_index(self) -> None:
        from apps.courses.course_index import CourseIndex
        from apps.courses.matching import CourseCatalog

        CourseCatalog.reset()  # refresh the deterministic-matcher cache
        try:
            count = CourseIndex.rebuild()
            self.stdout.write(self.style.SUCCESS(f"Embedding index rebuilt: {count} courses."))
        except Exception as error:  # chromadb/model unavailable -> deterministic fallback
            self.stdout.write(
                self.style.WARNING(
                    f"Embedding index not rebuilt ({type(error).__name__}); roadmap matching will "
                    f"use the deterministic skill/role/level fallback."
                )
            )
