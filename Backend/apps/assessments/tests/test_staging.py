from __future__ import annotations

import ast

from apps.assessments.scenario_corpus.staging import (
    append_drafts,
    format_scenario_literal,
    promote_to_module,
    read_drafts,
    staging_path,
    write_drafts,
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


def test_promote_into_empty_stub_module_stays_valid_python(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._CORPUS_DIR", tmp_path
    )
    module = tmp_path / "frontend.py"
    module.write_text(
        "from apps.assessments.scenario_corpus.schema import ScenarioDocument\n"
        "SCENARIOS: list[ScenarioDocument] = []\n",
        encoding="utf-8",
    )
    count = promote_to_module("frontend", [_doc()])
    assert count == 1
    text = module.read_text(encoding="utf-8")
    ast.parse(text)  # must still be valid Python (would raise SyntaxError if corrupted)
    assert "backend.decorators.s1.single_choice.gen-x" in text
    # The marker must NOT have been corrupted by inserting inside `list[ScenarioDocument]`.
    assert "SCENARIOS: list[ScenarioDocument] = [" in text


def test_promote_into_nonempty_module_stays_valid_python(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._CORPUS_DIR", tmp_path
    )
    module = tmp_path / "frontend.py"
    # A non-empty list whose existing literal contains its own `]` characters.
    module.write_text(
        "from apps.assessments.scenario_corpus.schema import ScenarioDocument\n"
        "SCENARIOS: list[ScenarioDocument] = [\n"
        "    {'doc_id': 'x', 'options': [{'id': 'a'}]},\n"
        "]\n",
        encoding="utf-8",
    )
    promote_to_module("frontend", [_doc()])
    text = module.read_text(encoding="utf-8")
    ast.parse(text)
    assert "backend.decorators.s1.single_choice.gen-x" in text
    assert "'doc_id': 'x'" in text  # the pre-existing entry is preserved


def test_write_drafts_overwrites_and_can_drain(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )
    append_drafts("backend", [_doc(), _doc()])
    assert len(read_drafts("backend")) == 2
    write_drafts("backend", [])  # drain
    assert read_drafts("backend") == []
