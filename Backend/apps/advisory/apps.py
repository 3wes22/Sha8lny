"""Django app configuration for ``apps.advisory``.

When ``ADVISORY_WARMUP=1`` is set (recommended for live demos), ``ready()``
pre-builds the RAG retrieval singletons — the collection-wide BM25 hybrid
index, the embedding model, and the cross-encoder re-ranker — in a background
thread, so the first real advisory question does not pay the one-time ~16s
cold-start mid-demo.

The warmup is opt-in and best-effort: it runs only in a request-serving
process, never blocks startup, and never raises — so the test suite, migrations
and one-shot management commands stay fast even if the flag is left set.
"""

from __future__ import annotations

import logging
import os
import sys
import threading

from django.apps import AppConfig


logger = logging.getLogger(__name__)

# Commands that must never trigger a warmup even if the flag is set: tests,
# schema work, and one-shot utilities are not request-serving processes.
_WARMUP_SKIP_ARGV = {
    "test",
    "migrate",
    "makemigrations",
    "collectstatic",
    "shell",
    "dumpdata",
    "loaddata",
    "check",
}


class AdvisoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.advisory"

    def ready(self) -> None:
        if os.environ.get("ADVISORY_WARMUP", "").lower() not in {"1", "true", "yes"}:
            return
        if not self._should_warm():
            return

        thread = threading.Thread(
            target=self._warm_retrieval,
            name="advisory-warmup",
            daemon=True,
        )
        thread.start()

    @staticmethod
    def _should_warm() -> bool:
        """True only inside the process that will actually serve requests."""
        argv = sys.argv
        if any(arg in _WARMUP_SKIP_ARGV for arg in argv):
            return False
        if "runserver" in argv:
            # Under the autoreloader, ready() runs in both the reloader parent
            # and the worker; warm only the worker (RUN_MAIN=true). With
            # --noreload there is no parent, so warm directly.
            return os.environ.get("RUN_MAIN") == "true" or "--noreload" in argv
        # A WSGI/ASGI server (gunicorn/daphne/uvicorn) is not a manage.py
        # command, so there is nothing in argv to skip — treat it as serving.
        return True

    @staticmethod
    def _warm_retrieval() -> None:
        try:
            from importlib import import_module

            retriever = import_module("rag.retriever")
            retrieve_context = getattr(retriever, "retrieve_context", None)
            if not callable(retrieve_context):
                logger.warning(
                    "Advisory warmup: rag.retriever.retrieve_context unavailable."
                )
                return
            # One throwaway query builds the collection-wide BM25 index, loads
            # the embedding model, and loads the cross-encoder re-ranker.
            retrieve_context(
                "career guidance for a software engineer in Egypt",
                top_k=1,
            )
            logger.info("Advisory RAG warmup complete.")
        except Exception as error:  # best-effort; never break startup
            logger.warning("Advisory warmup skipped (non-fatal): %s", error)
