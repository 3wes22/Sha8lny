"""Django app configuration for ``apps.assessments``.

``ready()`` runs the scenario-corpus integrity check on app load so that
content regressions surface at ``manage.py check`` / ``runserver`` boot
time rather than at retrieval time. Set ``SKIP_SCENARIO_CORPUS_CHECK=true``
in the environment to skip the check in disaster-recovery scenarios where
a bad commit must not brick deployment.
"""

from __future__ import annotations

import logging
import os

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


logger = logging.getLogger(__name__)


class AssessmentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.assessments"

    def ready(self) -> None:
        if os.environ.get("SKIP_SCENARIO_CORPUS_CHECK", "").lower() in {
            "1",
            "true",
            "yes",
        }:
            logger.warning(
                "Skipping scenario corpus integrity check (SKIP_SCENARIO_CORPUS_CHECK is set)."
            )
            return

        try:
            # Imported lazily so this module stays importable even if the
            # corpus package fails to load (e.g. during a partial deploy).
            from apps.assessments.scenario_corpus.registry import (
                assert_corpus_integrity,
            )

            assert_corpus_integrity()
        except ImproperlyConfigured:
            raise
        except Exception as error:
            logger.exception(
                "Unexpected error while validating scenario corpus integrity: %s",
                error,
            )
            raise
