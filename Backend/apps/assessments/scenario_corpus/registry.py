"""Corpus version, iteration helpers, and integrity assertions.

``SCENARIO_CORPUS_VERSION`` is the single string that
``AssessmentAIService._stage_one_cache_key`` (in
``apps.assessments.ai_pipeline``) appends to the cache key suffix so that
bumping it invalidates stage-one cached questions for every role at once.
Mirrors the ``CURATED_VERSION`` discipline used by
``apps.assessments.role_graph_data``.
"""

from __future__ import annotations

import importlib
from typing import Iterable, Iterator

from django.core.exceptions import ImproperlyConfigured

from apps.assessments.scenario_corpus.schema import (
    ScenarioDocument,
    iter_validation_errors,
)


SCENARIO_CORPUS_VERSION = "scenario-v1"


_ROLE_MODULES: tuple[str, ...] = (
    "apps.assessments.scenario_corpus.backend",
    "apps.assessments.scenario_corpus.frontend",
    "apps.assessments.scenario_corpus.fullstack",
    "apps.assessments.scenario_corpus.data_science",
    "apps.assessments.scenario_corpus.devops",
    "apps.assessments.scenario_corpus.android",
    "apps.assessments.scenario_corpus.machine_learning_engineer",
    "apps.assessments.scenario_corpus.ui_ux_designer",
)


def _load_module_scenarios(dotted_path: str) -> list[ScenarioDocument]:
    """Import a per-role module and return its module-level ``SCENARIOS`` list."""
    try:
        module = importlib.import_module(dotted_path)
    except ModuleNotFoundError as error:
        raise ImproperlyConfigured(
            f"Scenario corpus module {dotted_path!r} is missing"
        ) from error

    scenarios = getattr(module, "SCENARIOS", None)
    if scenarios is None:
        raise ImproperlyConfigured(
            f"Scenario corpus module {dotted_path!r} must define a module-level "
            "SCENARIOS list"
        )
    if not isinstance(scenarios, list):
        raise ImproperlyConfigured(
            f"Scenario corpus module {dotted_path!r}.SCENARIOS must be a list, "
            f"got {type(scenarios).__name__}"
        )
    return scenarios


def iter_all_scenarios(
    *, modules: Iterable[str] | None = None
) -> Iterator[ScenarioDocument]:
    """Yield every scenario document declared by the per-role modules.

    Includes both ``draft`` and ``approved`` documents. Consumers that only
    want approved content (the ingest command, the retriever, the audit
    coverage check) must filter on ``review_status == "approved"`` themselves.
    """
    targets = tuple(modules) if modules is not None else _ROLE_MODULES
    for dotted_path in targets:
        for scenario in _load_module_scenarios(dotted_path):
            yield scenario


def iter_approved_scenarios() -> Iterator[ScenarioDocument]:
    for scenario in iter_all_scenarios():
        if scenario.get("review_status") == "approved":
            yield scenario


def assert_corpus_integrity() -> None:
    """Validate every scenario document and assert ``doc_id`` uniqueness.

    Raises ``django.core.exceptions.ImproperlyConfigured`` with a precise,
    aggregated message on first batch of failures so the problem surfaces at
    ``manage.py check`` time rather than at retrieval time.
    """
    seen_ids: dict[str, str] = {}
    duplicate_errors: list[str] = []
    all_scenarios: list[ScenarioDocument] = []

    for scenario in iter_all_scenarios():
        all_scenarios.append(scenario)
        doc_id = str(scenario.get("doc_id") or "")
        if not doc_id:
            # Validation will catch the missing/blank doc_id; skip dup check.
            continue
        if doc_id in seen_ids:
            duplicate_errors.append(
                f"duplicate doc_id {doc_id!r} (first seen in {seen_ids[doc_id]})"
            )
        else:
            seen_ids[doc_id] = scenario.get("role_key") or "<unknown role>"

    validation_failures = iter_validation_errors(all_scenarios)

    if not duplicate_errors and not validation_failures:
        return

    message_lines = [
        f"Scenario corpus integrity check failed (version={SCENARIO_CORPUS_VERSION}):"
    ]
    for failure in duplicate_errors:
        message_lines.append(f"  - {failure}")
    for doc_id, errors in validation_failures:
        message_lines.append(f"  - {doc_id}:")
        for error in errors:
            message_lines.append(f"      * {error}")
    raise ImproperlyConfigured("\n".join(message_lines))
