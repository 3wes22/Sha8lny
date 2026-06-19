"""Tests for the review_scenarios management command.

TDD test file — written before the command implementation.
"""

from __future__ import annotations

import ast
import hashlib
import math
from io import StringIO

import pytest
from django.core.management import call_command

from apps.assessments.role_graph_data import ROLE_GRAPHS
from apps.assessments.scenario_corpus.staging import append_drafts, read_drafts


class _FakeEmbedder:
    """Deterministic, network-free stand-in for SentenceTransformer.

    Identical text -> identical unit vector (cosine 1.0). Different text ->
    near-orthogonal vectors (cosine ~0 for 32 dims), so the >0.92 threshold
    fires only for genuine duplicates.
    """

    def encode(self, texts, normalize_embeddings=True):  # noqa: ARG002
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            raw = [b - 127.5 for b in digest]  # 32 dims
            norm = math.sqrt(sum(x * x for x in raw)) or 1.0
            vectors.append([x / norm for x in raw])
        return vectors


def _use_fake_embedder(monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.management.commands.review_scenarios.Command._load_embedder",
        lambda self: _FakeEmbedder(),
    )


def _draft(slug: str, *, subskill: str = "component_composition", scenario: str | None = None) -> dict:
    lookup = {
        s.key: s for d in ROLE_GRAPHS["frontend"].dimensions for s in d.subskills
    }
    s = lookup[subskill]
    return {
        "doc_id": f"frontend.{subskill}.s1.single_choice.{slug}",
        "role_key": "frontend",
        "subskill_key": subskill,
        "competency": s.label,
        "dimension_key": s.dimension,
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess component composition tradeoffs.",
        "scenario_context": scenario or "A modal re-renders its entire subtree on every keystroke in a form.",
        "stem": "Which composition change most reduces unnecessary re-renders?",
        "options": [
            {"id": "a", "label": "Lift state up and memoize the heavy subtree."},
            {"id": "b", "label": "Inline every child to avoid prop drilling."},
            {"id": "c", "label": "Wrap the whole app in a single context provider."},
            {"id": "d", "label": "Disable React strict mode in development."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "Memoizing the stable subtree avoids re-render on unrelated state.",
        "correct_answer_rationale": "It isolates the frequently-changing state.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Correct isolation + memo."},
            {"option_id": "b", "is_correct": False, "rationale": "Worsens coupling."},
            {"option_id": "c", "is_correct": False, "rationale": "Broadens re-render scope."},
            {"option_id": "d", "is_correct": False, "rationale": "Unrelated to renders."},
        ],
        "author": "llm-assisted-pipeline",
        "license": "internal",
        "review_status": "draft",
        "created_at": "2026-06-18",
        "corpus_version": "scenario-v1",
    }


def _make_stub_module(tmp_path):
    (tmp_path / "frontend.py").write_text(
        "from apps.assessments.scenario_corpus.schema import ScenarioDocument\n"
        "SCENARIOS: list[ScenarioDocument] = []\n",
        encoding="utf-8",
    )


@pytest.mark.django_db
def test_review_yes_promotes_into_module(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path)
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._CORPUS_DIR", tmp_path)
    _use_fake_embedder(monkeypatch)
    _make_stub_module(tmp_path)
    append_drafts("frontend", [_draft("gen-1")])

    call_command("review_scenarios", "--role", "frontend", "--yes", stdout=StringIO(), stderr=StringIO())

    promoted = (tmp_path / "frontend.py").read_text(encoding="utf-8")
    assert "frontend.component_composition.s1.single_choice.gen-1" in promoted
    ast.parse(promoted)  # still valid Python
    assert read_drafts("frontend") == []  # promoted drafts are drained from staging


@pytest.mark.django_db
def test_review_rejects_near_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path)
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._CORPUS_DIR", tmp_path)
    _use_fake_embedder(monkeypatch)
    _make_stub_module(tmp_path)
    # Two drafts with identical embedding text (same competency/qtype/stage/scenario/stem).
    append_drafts("frontend", [_draft("gen-1"), _draft("gen-2")])

    call_command(
        "review_scenarios", "--role", "frontend", "--yes",
        "--duplicate-threshold", "0.92",
        stdout=StringIO(), stderr=StringIO(),
    )

    text = (tmp_path / "frontend.py").read_text(encoding="utf-8")
    ast.parse(text)
    assert "gen-1" in text       # first promotes
    assert "gen-2" not in text   # identical second is held back as a near-duplicate
