"""Tests for ``ScenarioRetriever``.

Uses mocks for ``chromadb`` and ``sentence_transformers`` so the suite is
hermetic and does not require either dependency to import at test time.

Covers tasks T016, T021 from ``specs/005-scenario-rag-corpus/tasks.md``.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION
from apps.assessments.scenario_retriever import ScenarioRetriever


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_retriever_singletons():
    """Drop cached singletons before and after every test so each case gets
    a fresh embedder/collection."""
    ScenarioRetriever.reset()
    yield
    ScenarioRetriever.reset()


@pytest.fixture(autouse=True)
def _allow_apps_logger_to_propagate():
    """The project's LOGGING config sets propagate=False on the ``apps``
    logger (see ``config/settings/base.py``). pytest's ``caplog`` attaches
    its handler at the root logger, so without enabling propagation here
    the assertions on retrieval log events would never observe the records.
    """
    apps_logger = logging.getLogger("apps")
    original = apps_logger.propagate
    apps_logger.propagate = True
    try:
        yield
    finally:
        apps_logger.propagate = original


def _mock_embedder() -> MagicMock:
    embedder = MagicMock()
    embedder.encode.return_value = [[0.1, 0.2, 0.3]]
    return embedder


def _seed_scenario(
    *,
    doc_id: str = "backend.http_api_design.s1.single_choice.test",
    role_key: str = "backend",
    subskill_key: str = "http_api_design",
    competency: str = "HTTP API Design",
    dimension_key: str = "rest_api_design",
    stage: int = 1,
    question_type: str = "single_choice",
) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "role_key": role_key,
        "subskill_key": subskill_key,
        "competency": competency,
        "dimension_key": dimension_key,
        "stage": stage,
        "question_type": question_type,
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Test objective.",
        "scenario_context": "Test scenario context that is non-empty.",
        "stem": "Which design is best?",
        "options": [
            {"id": "a", "label": "First parallel option."},
            {"id": "b", "label": "Second parallel option."},
            {"id": "c", "label": "Third parallel option."},
            {"id": "d", "label": "Fourth parallel option."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "Test explanation.",
        "correct_answer_rationale": "Because option a is best.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Best choice."},
            {"option_id": "b", "is_correct": False, "rationale": "Second-best."},
            {"option_id": "c", "is_correct": False, "rationale": "Worse."},
            {"option_id": "d", "is_correct": False, "rationale": "Worst."},
        ],
        "author": "test",
        "license": "internal",
        "review_status": "approved",
        "created_at": "2026-05-17",
        "corpus_version": SCENARIO_CORPUS_VERSION,
    }


def _install_mock_collection(monkeypatch, *, payloads: list[dict[str, Any]]) -> MagicMock:
    """Install a fake Chroma collection that returns the given payloads."""
    collection = MagicMock()
    metadatas = [{"payload": json.dumps(p, ensure_ascii=True)} for p in payloads]
    collection.query.return_value = {
        "metadatas": [metadatas],
        "distances": [[0.1 for _ in payloads]],
    }
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_collection",
        classmethod(lambda cls: collection),
    )
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_embedder",
        classmethod(lambda cls: _mock_embedder()),
    )
    return collection


def _enable_flag(monkeypatch, *, enabled: bool = True) -> None:
    monkeypatch.setattr(
        "apps.assessments.scenario_retriever.ASSESSMENT_SCENARIO_RAG_ENABLED",
        enabled,
    )
    monkeypatch.setattr(
        "apps.core.ai_settings.ASSESSMENT_SCENARIO_RAG_ENABLED",
        enabled,
    )


def _blueprint(**overrides: Any) -> dict[str, Any]:
    base = {
        "subskill_key": "http_api_design",
        "competency": "HTTP API Design",
        "question_type": "single_choice",
        "focus": "Idempotent retries for payment writes.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Behavior contract (T016)
# ---------------------------------------------------------------------------


def test_returns_empty_when_flag_is_off(monkeypatch):
    _enable_flag(monkeypatch, enabled=False)
    result = ScenarioRetriever.retrieve_for_blueprint(
        role_key="backend",
        blueprint=_blueprint(),
        stage=1,
    )
    assert result == []


def test_returns_documents_when_corpus_has_match(monkeypatch):
    _enable_flag(monkeypatch)
    payload = _seed_scenario()
    _install_mock_collection(monkeypatch, payloads=[payload])

    result = ScenarioRetriever.retrieve_for_blueprint(
        role_key="backend",
        blueprint=_blueprint(),
        stage=1,
    )
    assert len(result) == 1
    assert result[0]["doc_id"] == payload["doc_id"]


def test_applies_role_question_type_and_stage_filter(monkeypatch):
    _enable_flag(monkeypatch)
    collection = _install_mock_collection(monkeypatch, payloads=[_seed_scenario()])

    ScenarioRetriever.retrieve_for_blueprint(
        role_key="frontend",
        blueprint=_blueprint(question_type="multi_select"),
        stage=2,
    )
    call_kwargs = collection.query.call_args.kwargs
    where = call_kwargs["where"]
    assert {"role_key": "frontend"} in where["$and"]
    assert {"question_type": "multi_select"} in where["$and"]
    assert {"stage": 2} in where["$and"]


def test_caps_top_k_at_max_examples_per_prompt(monkeypatch):
    _enable_flag(monkeypatch)
    collection = _install_mock_collection(monkeypatch, payloads=[_seed_scenario()])

    ScenarioRetriever.retrieve_for_blueprint(
        role_key="backend",
        blueprint=_blueprint(),
        stage=1,
        top_k=999,
    )
    assert collection.query.call_args.kwargs["n_results"] <= 5


def test_returns_empty_on_chroma_exception_and_emits_warning(monkeypatch, caplog):
    _enable_flag(monkeypatch)

    collection = MagicMock()
    collection.query.side_effect = RuntimeError("kaboom")
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_collection",
        classmethod(lambda cls: collection),
    )
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_embedder",
        classmethod(lambda cls: _mock_embedder()),
    )

    with caplog.at_level(logging.WARNING, logger="apps.assessments.scenario_retriever"):
        result = ScenarioRetriever.retrieve_for_blueprint(
            role_key="backend",
            blueprint=_blueprint(),
            stage=1,
        )

    assert result == []
    warning_records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "scenario_retrieval_failed"
    ]
    assert len(warning_records) == 1
    assert getattr(warning_records[0], "error_type", None) == "RuntimeError"


def test_skips_results_with_invalid_payload(monkeypatch):
    _enable_flag(monkeypatch)
    invalid = _seed_scenario(doc_id="backend.http_api_design.s1.single_choice.invalid")
    invalid["dimension_key"] = "wrong_dimension"  # fails validate_scenario

    collection = MagicMock()
    collection.query.return_value = {
        "metadatas": [[{"payload": json.dumps(invalid, ensure_ascii=True)}]],
        "distances": [[0.1]],
    }
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_collection",
        classmethod(lambda cls: collection),
    )
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_embedder",
        classmethod(lambda cls: _mock_embedder()),
    )

    result = ScenarioRetriever.retrieve_for_blueprint(
        role_key="backend",
        blueprint=_blueprint(),
        stage=1,
    )
    assert result == []


def test_emits_info_log_with_documented_keys(monkeypatch, caplog):
    _enable_flag(monkeypatch)
    payload = _seed_scenario()
    _install_mock_collection(monkeypatch, payloads=[payload])

    with caplog.at_level(logging.INFO, logger="apps.assessments.scenario_retriever"):
        ScenarioRetriever.retrieve_for_blueprint(
            role_key="backend",
            blueprint=_blueprint(),
            stage=1,
        )
    info_records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "scenario_retrieval"
    ]
    assert len(info_records) == 1
    record = info_records[0]
    assert record.role_key == "backend"
    assert record.subskill_key == "http_api_design"
    assert record.question_type == "single_choice"
    assert record.stage == 1
    assert record.results_count == 1
    assert record.top_doc_id == payload["doc_id"]
    assert record.corpus_version == SCENARIO_CORPUS_VERSION


def test_build_embedding_text_format_is_stable():
    text = ScenarioRetriever.build_embedding_text(
        competency="HTTP API Design",
        question_type="single_choice",
        stage=1,
        scenario_context="A payment retry.",
        stem="Which design is best?",
    )
    assert text == (
        "HTTP API Design | single_choice | stage 1\n"
        "A payment retry.\n"
        "Which design is best?"
    )


# ---------------------------------------------------------------------------
# Operational safety (T021)
# ---------------------------------------------------------------------------


def test_returns_empty_when_persist_dir_missing(monkeypatch, tmp_path, caplog):
    _enable_flag(monkeypatch)
    missing = tmp_path / "does_not_exist_yet"
    monkeypatch.setattr(
        "apps.assessments.scenario_retriever.SCENARIO_VECTOR_DB_PATH",
        str(missing),
    )

    # Simulate Chroma blowing up when given an unreadable directory.
    def raise_io(cls):
        raise OSError("filesystem unavailable")

    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_collection",
        classmethod(raise_io),
    )
    monkeypatch.setattr(
        ScenarioRetriever,
        "_get_embedder",
        classmethod(lambda cls: _mock_embedder()),
    )

    with caplog.at_level(logging.WARNING, logger="apps.assessments.scenario_retriever"):
        result = ScenarioRetriever.retrieve_for_blueprint(
            role_key="backend",
            blueprint=_blueprint(),
            stage=1,
        )

    assert result == []
    warning_records = [
        record for record in caplog.records
        if getattr(record, "event", None) == "scenario_retrieval_failed"
    ]
    assert len(warning_records) == 1
