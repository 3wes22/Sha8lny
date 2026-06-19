"""Rebuild the Chroma course embedding index."""

from django.core.management.base import BaseCommand

from apps.courses.course_index import CourseIndex


class Command(BaseCommand):
    help = "Rebuild the ChromaDB course embedding index for roadmap matching."

    def handle(self, *args, **options) -> None:
        CourseIndex.reset()
        count = CourseIndex.rebuild()
        self.stdout.write(self.style.SUCCESS(f"Indexed {count} courses."))
