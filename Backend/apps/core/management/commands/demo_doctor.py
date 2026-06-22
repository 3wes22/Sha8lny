"""Pre-flight health check for the graduation demo.

Run this right before an evaluator walks in to confirm every demo surface has the
data it needs. It is **read-only** — it never seeds or mutates — and prints a
single PASS / FAIL with the first failing check called out.

By default it does not spend Gemini quota; pass ``--online`` to also make one
live Gemini round-trip (the offline demo path is fully supported, so a missing
key is only a warning).

Usage::

    python manage.py demo_doctor             # offline checks only
    python manage.py demo_doctor --online    # also verify a live Gemini call
"""

from __future__ import annotations

import sys

from django.core.management.base import BaseCommand


_CORPUS_MIN_DOCS = 1000

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"

NEW_USER_EMAIL = "demo.new@sha8alny.local"
RETURNING_USER_EMAIL = "demo.progress@sha8alny.local"


class Command(BaseCommand):
    help = "Read-only pre-flight check that the graduation demo is ready."

    def add_arguments(self, parser):
        parser.add_argument(
            "--online",
            action="store_true",
            help="Also make one live Gemini round-trip (spends a little quota).",
        )

    def handle(self, *args, **options):
        checks = [
            ("Demo accounts", self._check_accounts),
            ("Returning-user journey", self._check_returning_user),
            ("New user is clean", self._check_new_user),
            ("Jobs seeded + skills", self._check_jobs),
            ("Courses published", self._check_courses),
            ("Advisory corpus built", self._check_corpus),
            ("Advisory grounding", self._check_grounding),
            ("Gemini runtime", lambda: self._check_gemini(options["online"])),
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("\nDemo doctor\n"))
        results = []
        for label, fn in checks:
            try:
                status, detail = fn()
            except Exception as error:
                status, detail = FAIL, f"{type(error).__name__}: {error}"
            results.append((label, status, detail))
            self.stdout.write(f"  {self._mark(status)} {label}: {detail}")

        worst = self._summary(results)
        if worst == FAIL:
            sys.exit(1)

    # -- checks ---------------------------------------------------------------

    def _check_accounts(self):
        from apps.users.models import User

        present = set(
            User.objects.filter(
                email__in=[NEW_USER_EMAIL, RETURNING_USER_EMAIL]
            ).values_list("email", flat=True)
        )
        missing = {NEW_USER_EMAIL, RETURNING_USER_EMAIL} - present
        if missing:
            return FAIL, f"missing {sorted(missing)} — run demo_reset"
        return PASS, "both demo accounts exist"

    def _check_returning_user(self):
        from apps.users.models import User
        from apps.roadmaps.models import Roadmap, RoadmapCourse, RoadmapMilestone

        user = User.objects.filter(email=RETURNING_USER_EMAIL).first()
        if user is None:
            return FAIL, "returning user missing — run demo_reset"
        roadmap = Roadmap.objects.filter(user=user).order_by("-updated_at").first()
        if roadmap is None:
            return FAIL, "no roadmap — run demo_reset"
        if roadmap.status != Roadmap.ACTIVE:
            return WARN, f"roadmap status is {roadmap.status!r}, expected 'active'"
        matched = RoadmapCourse.objects.filter(milestone__phase__roadmap=roadmap).count()
        completed = RoadmapMilestone.objects.filter(
            phase__roadmap=roadmap, status=RoadmapMilestone.COMPLETED
        ).count()
        if matched == 0:
            return FAIL, "0 matched courses — seed courses+index BEFORE the demo seed"
        if completed == 0:
            return WARN, "no completed milestones to show"
        return PASS, f"active roadmap, {matched} courses, {completed} completed milestones"

    def _check_new_user(self):
        from apps.users.models import User
        from apps.roadmaps.models import Roadmap

        user = User.objects.filter(email=NEW_USER_EMAIL).first()
        if user is None:
            return FAIL, "new user missing — run demo_reset"
        roadmaps = Roadmap.objects.filter(user=user).count()
        if roadmaps or user.assessments.count():
            return WARN, "new user is not empty (demo expects a blank slate)"
        return PASS, "new user is a clean slate"

    def _check_jobs(self):
        from apps.jobs.models import Job, JobSkill

        jobs = Job.objects.filter(is_deleted=False, is_active=True).count()
        if jobs == 0:
            return FAIL, "0 active jobs — run demo_reset"
        skilled = JobSkill.objects.values("job").distinct().count()
        if skilled == 0:
            return WARN, f"{jobs} jobs but none have extracted skills (ranking weak)"
        return PASS, f"{jobs} jobs, {skilled} with skills"

    def _check_courses(self):
        from apps.courses.models import Course

        published = Course.objects.filter(is_deleted=False, is_published=True).count()
        if published == 0:
            return FAIL, "0 published courses — run seed_courses"
        return PASS, f"{published} published courses"

    def _check_corpus(self):
        from rag import vector_store

        count = vector_store.get_document_count()
        if count < _CORPUS_MIN_DOCS:
            return FAIL, (
                f"only {count} docs (expected ~64k) — build once with "
                f"`cd ai-models && python -m src.rag.build_vector_db`"
            )
        return PASS, f"{count} docs in career_knowledge"

    def _check_grounding(self):
        """Confirm retrieval returns grounded docs — no Gemini spend."""
        from apps.advisory.llm_service import get_rag_runtime

        runtime = get_rag_runtime()
        if not runtime or not callable(runtime.get("retrieve_context")):
            return FAIL, "RAG runtime unavailable — advisory cannot ground answers"
        docs = runtime["retrieve_context"](
            "How do I negotiate my first developer salary in Cairo?", top_k=4
        )
        if not docs:
            return WARN, "sample question retrieved 0 docs (abstention may be too strict)"
        return PASS, f"sample question grounded with {len(docs)} sources"

    def _check_gemini(self, online: bool):
        from apps.core.ai_settings import GEMINI_API_KEYS

        if not GEMINI_API_KEYS:
            return WARN, "no GEMINI_API_KEY — demo will run on deterministic fallbacks"
        if not online:
            return PASS, f"{len(GEMINI_API_KEYS)} key(s) configured (pass --online to test a live call)"
        from apps.core.gemma_client import GemmaClient

        client = GemmaClient(task_type="json_generation", max_output_tokens=32)
        result = client.generate_structured(
            prompt='Return JSON {"ok": true}',
            system="Return strict JSON only.",
            required_keys=("ok",),
        )
        if result.metadata.fallback_used:
            return WARN, "Gemini call fell back (key may be over quota)"
        return PASS, f"live Gemini round-trip OK ({result.metadata.model})"

    # -- reporting ------------------------------------------------------------

    def _mark(self, status):
        return {
            PASS: self.style.SUCCESS("✓"),
            WARN: self.style.WARNING("!"),
            FAIL: self.style.ERROR("✗"),
        }[status]

    def _summary(self, results):
        fails = [r for r in results if r[1] == FAIL]
        warns = [r for r in results if r[1] == WARN]
        self.stdout.write("")
        if fails:
            self.stdout.write(self.style.ERROR(f"NOT READY — {len(fails)} blocking issue(s):"))
            for label, _s, detail in fails:
                self.stdout.write(self.style.ERROR(f"  ✗ {label}: {detail}"))
            return FAIL
        if warns:
            self.stdout.write(self.style.WARNING(f"READY with {len(warns)} warning(s) — review above."))
            return WARN
        self.stdout.write(self.style.SUCCESS("READY — all demo checks passed."))
        return PASS
