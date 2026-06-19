from __future__ import annotations

import ast

from apps.assessments.scenario_corpus.staging import (
    append_drafts,
    format_scenario_literal,
    read_drafts,
    staging_path,
)


def _doc() -> dict:
    return {
        "doc_id": "backend.decorators.s1.single_choice.gen-x",
        "role_key": "backend",
        "subskill_key": "decorators",
        "competency": "Decorators",
        "dimension_key": "python_fundamentals",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "x",
        "scenario_context": "y",
        "stem": "z",
        "options": [{"id": "a", "label": "l"}],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "e",
        "correct_answer_rationale": "r",
        "option_rationales": [{"option_id": "a", "is_correct": True, "rationale": "ok"}],
        "author": "llm-assisted-pipeline",
        "license": "internal",
        "review_status": "draft",
        "created_at": "2026-06-18",
        "corpus_version": "scenario-v1",
    }


def test_append_and_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )
    append_drafts("backend", [_doc()])
    drafts = read_drafts("backend")
    assert len(drafts) == 1
    assert drafts[0]["doc_id"] == "backend.decorators.s1.single_choice.gen-x"
    assert staging_path("backend") == tmp_path / "backend.jsonl"


def test_literal_is_valid_python_and_roundtrips():
    literal = format_scenario_literal(_doc())
    assert literal.rstrip().endswith("},")            # trailing comma for list insertion
    # Strip the list-insertion trailing comma so literal_eval yields the dict
    # itself (a bare `{...},` parses as a one-element tuple).
    parsed = ast.literal_eval(literal.strip().rstrip(","))
    assert parsed["doc_id"] == _doc()["doc_id"]
    assert parsed["corpus_version"] == "scenario-v1"  # emitted as a string, not a symbol
