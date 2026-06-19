# Assessment Scenario Corpus — Authoring Pipeline + Tiered Coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the 7 empty assessment scenario-corpus roles via an LLM-assisted, human-reviewed authoring pipeline, reach a tiered/demand-weighted coverage target, and measure the retrieval + question-quality improvement.

**Architecture:** New management commands draft `ScenarioDocument`s with Gemini into a JSONL staging area, validate/dedup them, and (after human review) promote them into the version-controlled per-role `.py` modules. The retriever and prompt wiring are unchanged; filling the corpus activates the existing RAG path. Coverage is gated by a tiered audit (Tier 1 = stage-1 calibration for all roles; Tier 2 = stage-2 demand-weighted).

**Tech Stack:** Django management commands, `GemmaClient` (Gemini runtime), the existing `scenario_corpus` schema/registry/retriever, Chroma + sentence-transformers, pytest.

**Spec:** `docs/superpowers/specs/2026-06-18-assessment-scenario-corpus-design.md`

---

## Correction vs. spec (verified 2026-06-18)

The spec (§1 Decision 7, §6 Phase 2) assumed `ASSESSMENT_SCENARIO_RAG_ENABLED` is default-**off**. **It is already `default=True`** in `apps/core/ai_settings.py:87`. With the corpus empty for 7 roles, the retriever simply returns `[]` for them (safe). So Phase 2 does **not** flip the flag — it confirms the flag is on, ensures no `.env` override disables it, bumps the corpus version, and publishes the eval. The CLAUDE.md "Default-off" line is stale and gets corrected in Phase 5.

---

## House conventions (apply to every task)

- All commands run from `Backend/`. Use the repo venv, quota-safe: `env -u GEMINI_API_KEY venv/bin/python …`.
- Run tests with: `env -u GEMINI_API_KEY venv/bin/python -m pytest <path> -v`.
- Tests **never** hit the network: mock `apps.core.gemma_client.GemmaClient.generate_structured`.
- Commit after each task with the shown message.

---

## File Structure

**New files**
- `Backend/apps/assessments/scenario_corpus/coverage.py` — blueprint enumeration + tier definitions (shared by generator and audit).
- `Backend/apps/assessments/scenario_corpus/generation.py` — prompt builder, response contract, document assembler, Python-literal formatter.
- `Backend/apps/assessments/scenario_corpus/staging.py` — JSONL staging read/write + promoter into `<role>.py`.
- `Backend/apps/assessments/management/commands/generate_scenarios.py`
- `Backend/apps/assessments/management/commands/review_scenarios.py`
- `Backend/apps/assessments/scenario_corpus/eval/retrieval_eval.py` — deterministic retrieval coverage/precision eval.
- `Backend/apps/assessments/scenario_corpus/eval/rubric.py` — deterministic question-quality rubric scorer.
- `Backend/apps/assessments/scenario_corpus/eval/ab_quality.py` — RAG on/off A/B harness + LLM-judge.
- Tests: `test_coverage_planner.py`, `test_generation.py`, `test_staging.py`, `test_generate_scenarios.py`, `test_review_scenarios.py`, `test_audit_tiers.py`, `test_retrieval_eval.py`, `test_rubric.py` under `apps/assessments/tests/`.
- `docs/product/SCENARIO_RAG_EVAL.md`

**Modified**
- `scenario_corpus/{frontend,fullstack,data_science,devops,android,machine_learning_engineer,ui_ux_designer}.py`, `backend.py` — promoted approved scenarios (content).
- `scenario_corpus/registry.py` — `SCENARIO_CORPUS_VERSION` bumps.
- `management/commands/scenario_corpus_audit.py` — `--tier {1,2,all}`.
- `scenario_corpus/AUTHOR_GUIDE.md`, `Backend/CLAUDE.md`, root `CLAUDE.md` — docs.

---

# Phase 0 — Pipeline scaffolding

### Task 1: Blueprint enumeration + tier definitions

**Files:**
- Create: `Backend/apps/assessments/scenario_corpus/coverage.py`
- Test: `Backend/apps/assessments/tests/test_coverage_planner.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_coverage_planner.py
from __future__ import annotations

import pytest

from apps.assessments.scenario_corpus.coverage import (
    Blueprint,
    stage1_calibration_subskills,
    tier1_blueprints,
    uncovered_blueprints,
)


@pytest.mark.django_db
def test_stage1_calibration_returns_five_backend_subskills():
    subs = stage1_calibration_subskills("backend")
    assert len(subs) == 5
    assert all(isinstance(s, str) for s in subs)


def test_tier1_blueprints_are_stage1_single_choice():
    bps = tier1_blueprints("backend")
    assert bps, "tier-1 blueprint set must be non-empty"
    assert all(bp.stage == 1 and bp.question_type == "single_choice" for bp in bps)
    # Two blueprints per calibration subskill (floor is >= 2).
    assert len(bps) == 2 * len(stage1_calibration_subskills("backend"))
    bp = bps[0]
    assert bp.role_key == "backend"
    assert bp.competency and bp.dimension_key  # populated from the role graph


def test_uncovered_excludes_already_satisfied_subskills():
    # backend.py ships >=1 stage-1 single_choice for several subskills already;
    # uncovered must return strictly fewer blueprints than the full tier-1 set.
    full = tier1_blueprints("backend")
    todo = uncovered_blueprints("backend", tier=1)
    assert len(todo) < len(full)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_coverage_planner.py -v`
Expected: FAIL with `ModuleNotFoundError: ...scenario_corpus.coverage`.

- [ ] **Step 3: Implement `coverage.py`**

```python
# Backend/apps/assessments/scenario_corpus/coverage.py
"""Blueprint enumeration and tier definitions for the scenario corpus.

A *blueprint* is one (role, subskill, stage, question_type) cell the corpus
should cover. The generator drafts for uncovered blueprints; the audit gates
on whether each tier's blueprints are satisfied. This module is the single
source of truth for "what counts as covered", so generator and audit agree.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.assessments.role_graph_data import ROLE_GRAPHS
from apps.assessments.scenario_corpus.registry import iter_approved_scenarios

# Floors mirror scenario_corpus_audit + AUTHOR_GUIDE.
TIER1_STAGE1_SINGLE_CHOICE_MIN = 2


@dataclass(frozen=True)
class Blueprint:
    role_key: str
    subskill_key: str
    competency: str
    dimension_key: str
    stage: int
    question_type: str


def _subskill_lookup(role_key: str) -> dict[str, object]:
    graph = ROLE_GRAPHS[role_key]
    return {
        subskill.key: subskill
        for dimension in graph.dimensions
        for subskill in dimension.subskills
    }


def stage1_calibration_subskills(role_key: str) -> list[str]:
    """The subskills stage-1 calibration actually targets (the high-leverage set)."""
    targets = StageAllocator.allocate_stage_one(load_role_graph(role_key))
    return [target.key for target in targets]


def tier1_blueprints(role_key: str) -> list[Blueprint]:
    """Full Tier-1 floor: stage-1 single_choice, >=2 per calibration subskill."""
    lookup = _subskill_lookup(role_key)
    blueprints: list[Blueprint] = []
    for subskill_key in stage1_calibration_subskills(role_key):
        subskill = lookup[subskill_key]
        for _ in range(TIER1_STAGE1_SINGLE_CHOICE_MIN):
            blueprints.append(
                Blueprint(
                    role_key=role_key,
                    subskill_key=subskill_key,
                    competency=subskill.label,
                    dimension_key=subskill.dimension,
                    stage=1,
                    question_type="single_choice",
                )
            )
    return blueprints


def _approved_counts() -> dict[tuple[str, int, str, str], int]:
    counts: dict[tuple[str, int, str, str], int] = defaultdict(int)
    for scenario in iter_approved_scenarios():
        counts[
            (
                scenario["role_key"],
                int(scenario["stage"]),
                scenario["question_type"],
                scenario["subskill_key"],
            )
        ] += 1
    return counts


def uncovered_blueprints(role_key: str, *, tier: int) -> list[Blueprint]:
    """Blueprints still below floor, accounting for already-approved scenarios."""
    if tier != 1:
        raise ValueError(f"tier {tier} not yet supported (Phase 4 adds tier 2)")
    counts = _approved_counts()
    needed: dict[tuple[str, str], int] = defaultdict(int)
    todo: list[Blueprint] = []
    for bp in tier1_blueprints(role_key):
        cell = (bp.role_key, bp.stage, bp.question_type, bp.subskill_key)
        have = counts.get(cell, 0) + needed[(bp.subskill_key, bp.question_type)]
        if have < TIER1_STAGE1_SINGLE_CHOICE_MIN:
            todo.append(bp)
            needed[(bp.subskill_key, bp.question_type)] += 1
    return todo
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_coverage_planner.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/scenario_corpus/coverage.py apps/assessments/tests/test_coverage_planner.py
git commit -m "feat(assessments): blueprint enumeration + tier-1 coverage planner"
```

---

### Task 2: Generation prompt + response contract + document assembler

**Files:**
- Create: `Backend/apps/assessments/scenario_corpus/generation.py`
- Test: `Backend/apps/assessments/tests/test_generation.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_generation.py
from __future__ import annotations

from apps.assessments.scenario_corpus.coverage import Blueprint
from apps.assessments.scenario_corpus.generation import (
    LLM_CONTENT_KEYS,
    assemble_scenario_document,
    build_generation_prompt,
)
from apps.assessments.scenario_corpus.schema import validate_scenario


def _backend_blueprint() -> Blueprint:
    return Blueprint(
        role_key="backend",
        subskill_key="decorators",
        competency="Decorators",
        dimension_key="python_fundamentals",
        stage=1,
        question_type="single_choice",
    )


def test_prompt_includes_competency_dimension_and_banned_phrases():
    system, prompt = build_generation_prompt(_backend_blueprint(), exemplars=[])
    assert "Decorators" in prompt
    assert "python_fundamentals" in prompt
    assert "Disable logging" in prompt          # banned-phrase guidance present
    assert "single_choice" in prompt
    assert "Select all that apply" not in prompt  # only for multi_select


def test_assembled_document_passes_validation():
    bp = _backend_blueprint()
    llm_payload = {
        "learning_objective": "Assess decorator metadata preservation.",
        "scenario_context": "A logging decorator wraps Django views and breaks help() output in tests.",
        "stem": "Which decorator pattern best preserves the wrapped callable's metadata?",
        "options": [
            {"id": "a", "label": "Use functools.wraps on the inner wrapper."},
            {"id": "b", "label": "Stack bare nested functions without copying __name__."},
            {"id": "c", "label": "Replace the function with a lambda that drops hints."},
            {"id": "d", "label": "Avoid decorators and inline the logging call."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "functools.wraps copies metadata to the wrapper.",
        "correct_answer_rationale": "It keeps introspection and tests stable.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Standard metadata forwarding."},
            {"option_id": "b", "is_correct": False, "rationale": "Loses metadata."},
            {"option_id": "c", "is_correct": False, "rationale": "Hides the signature."},
            {"option_id": "d", "is_correct": False, "rationale": "Avoids the concern asked."},
        ],
        "difficulty": 3,
        "estimated_seconds": 50,
    }
    doc = assemble_scenario_document(bp, llm_payload, slug="gen-test")
    assert doc["doc_id"] == "backend.decorators.s1.single_choice.gen-test"
    assert doc["review_status"] == "draft"
    assert validate_scenario(doc) == []


def test_llm_content_keys_are_the_required_keys():
    assert "scenario_context" in LLM_CONTENT_KEYS
    assert "stem" in LLM_CONTENT_KEYS
    assert "doc_id" not in LLM_CONTENT_KEYS  # governance fields are injected, not generated
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_generation.py -v`
Expected: FAIL with `ModuleNotFoundError: ...scenario_corpus.generation`.

- [ ] **Step 3: Implement `generation.py`**

```python
# Backend/apps/assessments/scenario_corpus/generation.py
"""Prompt construction, response contract, and document assembly for the
LLM-assisted scenario generator. Pure functions only — no I/O, no Gemini call
(the command owns the GemmaClient). Kept side-effect-free so it is fully
unit-testable without the network.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from apps.assessments.scenario_corpus.coverage import Blueprint
from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION
from apps.assessments.scenario_corpus.schema import ScenarioDocument

GENERATION_AUTHOR = "llm-assisted-pipeline"

# The content fields the LLM produces. Governance/identity fields are injected
# by assemble_scenario_document(), never trusted from the model.
LLM_CONTENT_KEYS: tuple[str, ...] = (
    "learning_objective",
    "scenario_context",
    "stem",
    "options",
    "answer_key",
    "explanation",
    "correct_answer_rationale",
    "option_rationales",
    "difficulty",
    "estimated_seconds",
)

_BANNED_PHRASES = (
    "Disable logging",
    "Choose the option that preserves correctness, clarity, and maintainability",
    "generic self-rating",
)

_ANSWER_KEY_SHAPE = {
    "single_choice": 'answer_key = {"correct_option_ids": ["a"], "scoring": "single_best"}; exactly 4 options.',
    "multi_select": 'answer_key = {"correct_option_ids": ["a","b"], "scoring": "partial_credit"}; exactly 5 options; stem ends with "Select all that apply.". Mark 2 or 3 correct.',
    "open_ended": 'answer_key = {"expected_concepts": [3 items], "required_concept_count": 2, "forbidden_concepts": [1 item], "scoring": "concept_coverage"}; options=[]; option_rationales=[].',
}


def build_generation_prompt(
    blueprint: Blueprint, *, exemplars: list[dict[str, Any]]
) -> tuple[str, str]:
    """Return (system, prompt) for one blueprint. `exemplars` are existing
    approved scenarios used purely as style anchors."""
    system = (
        "You are an expert technical assessment author. You write one scenario-"
        "based question as strict JSON. No markdown, no commentary."
    )
    exemplar_block = ""
    if exemplars:
        ex = exemplars[0]
        exemplar_block = (
            "\nStyle reference (do NOT copy; match the shape and rigor):\n"
            f"  scenario_context: {ex.get('scenario_context','')}\n"
            f"  stem: {ex.get('stem','')}\n"
        )
    prompt = (
        f"Role: {blueprint.role_key}\n"
        f"Competency (must be the subject): {blueprint.competency}\n"
        f"Dimension: {blueprint.dimension_key}\n"
        f"Stage: {blueprint.stage} (1=calibration ~difficulty 3, 2=targeted ~difficulty 4)\n"
        f"question_type: {blueprint.question_type}\n\n"
        "Quality bar:\n"
        "1. Open with a concrete engineering scenario (name a system/failure/finding).\n"
        "2. Pose a decision between real tradeoffs, never a definition.\n"
        "3. All distractors must be plausible to a junior; options parallel in shape/length.\n"
        f"4. Use real {blueprint.role_key} engineering vocabulary.\n"
        f"5. Never use these phrases: {', '.join(_BANNED_PHRASES)}.\n\n"
        f"Answer-key contract: {_ANSWER_KEY_SHAPE[blueprint.question_type]}\n"
        f"{exemplar_block}\n"
        "Return JSON with exactly these keys: "
        f"{', '.join(LLM_CONTENT_KEYS)}."
    )
    return system, prompt


def assemble_scenario_document(
    blueprint: Blueprint,
    llm_payload: dict[str, Any],
    *,
    slug: str,
    created_at: str | None = None,
) -> ScenarioDocument:
    """Merge model content with injected governance/identity fields."""
    doc: ScenarioDocument = {
        "doc_id": (
            f"{blueprint.role_key}.{blueprint.subskill_key}."
            f"s{blueprint.stage}.{blueprint.question_type}.{slug}"
        ),
        "role_key": blueprint.role_key,
        "subskill_key": blueprint.subskill_key,
        "competency": blueprint.competency,
        "dimension_key": blueprint.dimension_key,
        "stage": blueprint.stage,
        "question_type": blueprint.question_type,
        "author": GENERATION_AUTHOR,
        "license": "internal",
        "review_status": "draft",
        "created_at": created_at or date.today().isoformat(),
        "corpus_version": SCENARIO_CORPUS_VERSION,
    }
    for key in LLM_CONTENT_KEYS:
        if key in llm_payload:
            doc[key] = llm_payload[key]
    if "helper" in llm_payload:
        doc["helper"] = llm_payload["helper"]
    return doc
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_generation.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/scenario_corpus/generation.py apps/assessments/tests/test_generation.py
git commit -m "feat(assessments): scenario generation prompt + document assembler"
```

---

### Task 3: Staging store + Python-literal promoter

**Files:**
- Create: `Backend/apps/assessments/scenario_corpus/staging.py`
- Test: `Backend/apps/assessments/tests/test_staging.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_staging.py
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
    parsed = ast.literal_eval(literal)
    assert parsed["doc_id"] == _doc()["doc_id"]
    assert parsed["corpus_version"] == "scenario-v1"  # emitted as a string, not a symbol
    assert literal.rstrip().endswith("},")            # trailing comma for list insertion
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_staging.py -v`
Expected: FAIL with `ModuleNotFoundError: ...scenario_corpus.staging`.

- [ ] **Step 3: Implement `staging.py`**

```python
# Backend/apps/assessments/scenario_corpus/staging.py
"""JSONL staging for generated drafts + promotion into per-role .py modules.

Drafts live in `_staging/<role>.jsonl` and are NEVER imported by the registry
(it only enumerates the role modules), so staged content can never reach
retrieval. Promotion appends reviewed dict literals into `<role>.py`'s
SCENARIOS list, keeping version control the source of truth.
"""

from __future__ import annotations

import json
import pprint
from pathlib import Path
from typing import Any

_CORPUS_DIR = Path(__file__).resolve().parent
_STAGING_DIR = _CORPUS_DIR / "_staging"


def staging_path(role_key: str) -> Path:
    return _STAGING_DIR / f"{role_key}.jsonl"


def append_drafts(role_key: str, docs: list[dict[str, Any]]) -> int:
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    path = staging_path(role_key)
    with path.open("a", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=True) + "\n")
    return len(docs)


def read_drafts(role_key: str) -> list[dict[str, Any]]:
    path = staging_path(role_key)
    if not path.exists():
        return []
    drafts: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            drafts.append(json.loads(line))
    return drafts


def write_drafts(role_key: str, docs: list[dict[str, Any]]) -> None:
    """Overwrite staging (used to drop promoted/rejected drafts)."""
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    path = staging_path(role_key)
    with path.open("w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=True) + "\n")


def format_scenario_literal(doc: dict[str, Any]) -> str:
    """Render one scenario as a black-compatible dict literal with trailing comma.
    `corpus_version` is emitted as a plain string value (not the symbol)."""
    body = pprint.pformat(dict(doc), width=88, sort_dicts=False)
    return f"    {body},\n"


def promote_to_module(role_key: str, docs: list[dict[str, Any]]) -> int:
    """Insert literals before the closing `]` of the module's SCENARIOS list."""
    module_path = _CORPUS_DIR / f"{role_key}.py"
    source = module_path.read_text(encoding="utf-8")
    marker = "SCENARIOS: list[ScenarioDocument] = ["
    if marker not in source:
        raise ValueError(f"{module_path} has no recognizable SCENARIOS list opener")
    # Handle the empty-stub form `SCENARIOS: list[ScenarioDocument] = []`.
    empty_form = "SCENARIOS: list[ScenarioDocument] = []"
    if empty_form in source:
        source = source.replace(empty_form, marker + "\n]")
    closing_index = source.index("]", source.index(marker))
    literals = "".join(format_scenario_literal(doc) for doc in docs)
    new_source = source[:closing_index] + literals + source[closing_index:]
    module_path.write_text(new_source, encoding="utf-8")
    return len(docs)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_staging.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/scenario_corpus/staging.py apps/assessments/tests/test_staging.py
git commit -m "feat(assessments): scenario draft staging + module promoter"
```

---

### Task 4: `generate_scenarios` management command

**Files:**
- Create: `Backend/apps/assessments/management/commands/generate_scenarios.py`
- Test: `Backend/apps/assessments/tests/test_generate_scenarios.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_generate_scenarios.py
from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command

from apps.assessments.scenario_corpus.staging import read_drafts
from apps.core.ai_logging import build_ai_metadata
from apps.core.gemma_client import GemmaResponse


def _valid_payload() -> dict:
    return {
        "learning_objective": "Assess decorator metadata preservation.",
        "scenario_context": "A logging decorator wraps Django views and breaks help() output.",
        "stem": "Which decorator pattern best preserves the wrapped callable's metadata?",
        "options": [
            {"id": "a", "label": "Use functools.wraps on the inner wrapper."},
            {"id": "b", "label": "Stack bare nested functions without copying __name__."},
            {"id": "c", "label": "Replace the function with a lambda dropping hints."},
            {"id": "d", "label": "Avoid decorators and inline the logging."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "functools.wraps copies metadata to the wrapper.",
        "correct_answer_rationale": "Keeps introspection stable.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "Standard forwarding."},
            {"option_id": "b", "is_correct": False, "rationale": "Loses metadata."},
            {"option_id": "c", "is_correct": False, "rationale": "Hides the signature."},
            {"option_id": "d", "is_correct": False, "rationale": "Avoids the concern."},
        ],
        "difficulty": 3,
        "estimated_seconds": 50,
    }


@pytest.mark.django_db
def test_generate_writes_only_valid_drafts_to_staging(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )

    def fake_generate_structured(self, *, prompt, system="", required_keys=(), response_json_schema=None):  # noqa: ARG001
        return GemmaResponse(
            text="{}",
            payload=_valid_payload(),
            metadata=build_ai_metadata(source="llm", processing_time_ms=1, model="mock"),
            prompt_tokens=1,
            completion_tokens=1,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    call_command("generate_scenarios", "--role", "frontend", "--tier", "1", "--limit", "2", stdout=StringIO())

    drafts = read_drafts("frontend")
    assert len(drafts) == 2
    assert all(d["review_status"] == "draft" for d in drafts)
    assert all(d["role_key"] == "frontend" for d in drafts)


@pytest.mark.django_db
def test_generate_skips_invalid_model_output(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path
    )

    def fake_generate_structured(self, *, prompt, system="", required_keys=(), response_json_schema=None):  # noqa: ARG001
        bad = _valid_payload()
        bad["options"] = bad["options"][:2]  # only 2 options -> invalid single_choice
        return GemmaResponse(
            text="{}", payload=bad,
            metadata=build_ai_metadata(source="llm", processing_time_ms=1, model="mock"),
            prompt_tokens=1, completion_tokens=1,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    call_command("generate_scenarios", "--role", "frontend", "--tier", "1", "--limit", "2", stdout=StringIO())
    assert read_drafts("frontend") == []  # nothing valid was staged
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_generate_scenarios.py -v`
Expected: FAIL with `Unknown command: 'generate_scenarios'`.

- [ ] **Step 3: Implement the command**

```python
# Backend/apps/assessments/management/commands/generate_scenarios.py
"""Draft scenario documents with Gemini for uncovered blueprints.

Validated drafts are appended to `_staging/<role>.jsonl` as review_status=draft.
Never writes to role .py modules or Chroma. Invalid model output is skipped
(with one logged warning), so the staging file only ever holds schema-valid drafts.
"""

from __future__ import annotations

import uuid
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.assessments.scenario_corpus.coverage import uncovered_blueprints
from apps.assessments.scenario_corpus.generation import (
    LLM_CONTENT_KEYS,
    assemble_scenario_document,
    build_generation_prompt,
)
from apps.assessments.scenario_corpus.registry import iter_approved_scenarios
from apps.assessments.scenario_corpus.schema import validate_scenario
from apps.assessments.scenario_corpus.staging import append_drafts
from apps.core.gemma_client import GemmaClient


class Command(BaseCommand):
    help = "Generate draft scenarios for uncovered blueprints into JSONL staging."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--role", required=True)
        parser.add_argument("--tier", type=int, default=1, choices=[1, 2])
        parser.add_argument("--limit", type=int, default=10)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        role_key = options["role"]
        todo = uncovered_blueprints(role_key, tier=options["tier"])[: options["limit"]]
        if not todo:
            self.stdout.write(self.style.SUCCESS(f"{role_key}: already covered for tier {options['tier']}."))
            return

        exemplars_by_subskill: dict[str, list[dict]] = {}
        for scn in iter_approved_scenarios():
            exemplars_by_subskill.setdefault(scn["subskill_key"], []).append(scn)

        client = GemmaClient(task_type="json_generation")
        staged: list[dict] = []
        for bp in todo:
            system, prompt = build_generation_prompt(
                bp, exemplars=exemplars_by_subskill.get(bp.subskill_key, [])
            )
            if options["dry_run"]:
                self.stdout.write(f"[dry-run] would generate {bp.subskill_key}/{bp.question_type}")
                continue
            try:
                response = client.generate_structured(
                    prompt=prompt, system=system, required_keys=LLM_CONTENT_KEYS
                )
            except Exception as error:  # noqa: BLE001 - generation must never abort the batch
                self.stderr.write(self.style.WARNING(f"generation failed for {bp.subskill_key}: {error}"))
                continue
            doc = assemble_scenario_document(
                bp, response.payload or {}, slug=f"gen-{uuid.uuid4().hex[:8]}"
            )
            errors = validate_scenario(doc)
            if errors:
                self.stderr.write(self.style.WARNING(
                    f"discarded invalid draft for {bp.subskill_key}: {errors[0]}"
                ))
                continue
            staged.append(doc)

        if staged:
            append_drafts(role_key, staged)
        self.stdout.write(self.style.SUCCESS(
            f"{role_key}: staged {len(staged)} valid draft(s) of {len(todo)} attempted."
        ))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_generate_scenarios.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/management/commands/generate_scenarios.py apps/assessments/tests/test_generate_scenarios.py
git commit -m "feat(assessments): generate_scenarios command (drafts -> JSONL staging)"
```

---

### Task 5: `review_scenarios` command (validate + dedup + promote)

**Files:**
- Create: `Backend/apps/assessments/management/commands/review_scenarios.py`
- Test: `Backend/apps/assessments/tests/test_review_scenarios.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_review_scenarios.py
from __future__ import annotations

import ast
from io import StringIO

import pytest
from django.core.management import call_command

from apps.assessments.scenario_corpus.staging import append_drafts, read_drafts


def _draft(slug: str, subskill: str = "component_composition") -> dict:
    # frontend subskill; competency/dimension match role graph for frontend.
    from apps.assessments.role_graph_data import ROLE_GRAPHS
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
        "scenario_context": "A modal re-renders its entire subtree on every keystroke in a form.",
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


@pytest.mark.django_db
def test_review_yes_promotes_into_module(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path)
    # Promote into a temp copy of the module so the test never edits real source.
    fake_module = tmp_path / "frontend.py"
    fake_module.write_text(
        "from apps.assessments.scenario_corpus.schema import ScenarioDocument\n"
        "SCENARIOS: list[ScenarioDocument] = []\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "apps.assessments.scenario_corpus.staging._CORPUS_DIR", tmp_path
    )
    append_drafts("frontend", [_draft("gen-1")])

    call_command("review_scenarios", "--role", "frontend", "--yes", stdout=StringIO())

    promoted = fake_module.read_text(encoding="utf-8")
    # The literal is present and the module still parses.
    assert "frontend.component_composition.s1.single_choice.gen-1" in promoted
    ast.parse(promoted)
    # Promoted drafts are removed from staging.
    assert read_drafts("frontend") == []


@pytest.mark.django_db
def test_review_rejects_near_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._STAGING_DIR", tmp_path)
    monkeypatch.setattr("apps.assessments.scenario_corpus.staging._CORPUS_DIR", tmp_path)
    (tmp_path / "frontend.py").write_text(
        "from apps.assessments.scenario_corpus.schema import ScenarioDocument\n"
        "SCENARIOS: list[ScenarioDocument] = []\n",
        encoding="utf-8",
    )
    d1 = _draft("gen-1")
    d2 = _draft("gen-2")  # identical text -> exact duplicate cluster
    append_drafts("frontend", [d1, d2])

    out = StringIO()
    call_command("review_scenarios", "--role", "frontend", "--yes", "--duplicate-threshold", "0.92", stdout=out)
    text = (tmp_path / "frontend.py").read_text(encoding="utf-8")
    # Only the first promotes; the near-duplicate is held back.
    assert text.count("review_status") >= 0  # module parses
    assert "gen-1" in text and "gen-2" not in text
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_review_scenarios.py -v`
Expected: FAIL with `Unknown command: 'review_scenarios'`.

- [ ] **Step 3: Implement the command**

```python
# Backend/apps/assessments/management/commands/review_scenarios.py
"""Review staged drafts: validate, near-duplicate-check, then (on accept)
promote into the per-role module and remove from staging.

Interactive by default; `--yes` accepts every schema-valid, non-duplicate draft
(used by tests and bulk runs). The near-duplicate check reuses the audit's
embedding text + cosine logic; if sentence-transformers is unavailable it is
skipped with a warning.
"""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from apps.assessments.scenario_corpus.registry import iter_approved_scenarios
from apps.assessments.scenario_corpus.schema import validate_scenario
from apps.assessments.scenario_corpus.staging import (
    promote_to_module,
    read_drafts,
    write_drafts,
)
from apps.assessments.scenario_retriever import ScenarioRetriever


class Command(BaseCommand):
    help = "Review staged scenario drafts and promote accepted ones into the role module."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--role", required=True)
        parser.add_argument("--yes", action="store_true", help="Accept all valid, non-duplicate drafts.")
        parser.add_argument("--duplicate-threshold", type=float, default=0.92)

    def handle(self, *args: Any, **options: Any) -> None:
        role_key = options["role"]
        drafts = read_drafts(role_key)
        if not drafts:
            self.stdout.write(f"{role_key}: no staged drafts.")
            return

        embedder = self._load_embedder()
        approved_texts = [self._text(s) for s in iter_approved_scenarios()]

        accepted: list[dict] = []
        remaining: list[dict] = []
        for draft in drafts:
            errors = validate_scenario(draft)
            if errors:
                self.stderr.write(self.style.WARNING(f"invalid draft {draft.get('doc_id')}: {errors[0]}"))
                remaining.append(draft)
                continue
            if embedder is not None and self._is_duplicate(
                embedder, self._text(draft),
                approved_texts + [self._text(a) for a in accepted],
                options["duplicate_threshold"],
            ):
                self.stderr.write(self.style.WARNING(f"near-duplicate held back: {draft.get('doc_id')}"))
                remaining.append(draft)
                continue
            if options["yes"] or self._prompt_accept(draft):
                draft["review_status"] = "approved"
                accepted.append(draft)
            else:
                remaining.append(draft)

        if accepted:
            promote_to_module(role_key, accepted)
        write_drafts(role_key, remaining)
        self.stdout.write(self.style.SUCCESS(
            f"{role_key}: promoted {len(accepted)}, {len(remaining)} left in staging."
        ))

    @staticmethod
    def _text(scn: dict) -> str:
        return ScenarioRetriever.build_embedding_text(
            competency=scn.get("competency", ""),
            question_type=scn.get("question_type", ""),
            stage=int(scn.get("stage", 0)),
            scenario_context=scn.get("scenario_context", ""),
            stem=scn.get("stem", ""),
        )

    def _load_embedder(self):
        try:
            from sentence_transformers import SentenceTransformer

            from apps.core.ai_settings import EMBEDDING_MODEL

            return SentenceTransformer(EMBEDDING_MODEL)
        except Exception:  # noqa: BLE001 - dedup is best-effort
            self.stderr.write(self.style.WARNING("near-duplicate check skipped (sentence-transformers unavailable)"))
            return None

    @staticmethod
    def _is_duplicate(embedder, text: str, others: list[str], threshold: float) -> bool:
        if not others:
            return False
        vectors = embedder.encode([text, *others], normalize_embeddings=True)
        query = vectors[0]
        for other in vectors[1:]:
            score = float(sum(a * b for a, b in zip(query, other)))
            if score > threshold:
                return True
        return False

    def _prompt_accept(self, draft: dict) -> bool:
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(f"{draft['doc_id']}")
        self.stdout.write(f"scenario: {draft['scenario_context']}")
        self.stdout.write(f"stem:     {draft['stem']}")
        for opt in draft.get("options", []):
            self.stdout.write(f"  ({opt['id']}) {opt['label']}")
        answer = input("accept? [y/N] ").strip().lower()
        return answer == "y"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_review_scenarios.py -v`
Expected: PASS (2 tests). (The dedup test is skipped gracefully if sentence-transformers is unavailable; if so, run it once in an env that has it — the repo venv does.)

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/management/commands/review_scenarios.py apps/assessments/tests/test_review_scenarios.py
git commit -m "feat(assessments): review_scenarios command (validate + dedup + promote)"
```

---

# Phase 1 — Tier-1 floor + content (all 8 roles)

### Task 6: Add `--tier` to the audit (Tier-1 gating)

**Files:**
- Modify: `Backend/apps/assessments/management/commands/scenario_corpus_audit.py`
- Test: `Backend/apps/assessments/tests/test_audit_tiers.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_audit_tiers.py
from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_audit_tier1_runs_and_reports_only_stage1(capsys):
    # Tier-1 audit must not raise on the import path and must restrict its
    # coverage report to stage-1 single_choice (no stage-2 floor noise).
    out = StringIO()
    try:
        call_command("scenario_corpus_audit", "--tier", "1", "--skip-duplicates", stdout=out)
    except SystemExit:
        pass  # audit calls sys.exit; both pass/fail acceptable here
    text = out.getvalue()
    assert "stage 1 single_choice" in text
    assert "stage 2 single_choice" not in text
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_audit_tiers.py -v`
Expected: FAIL — `--tier` is an unrecognized argument.

- [ ] **Step 3: Add the `--tier` argument and filter the checks**

In `scenario_corpus_audit.py`, add to `add_arguments`:

```python
        parser.add_argument(
            "--tier",
            type=str,
            default="all",
            choices=["1", "2", "all"],
            help="Gate only Tier 1 (stage-1 calibration), Tier 2 (stage-2 demand set), or all.",
        )
```

Then in `_report_coverage`, accept the tier and filter the `checks` list. Change the method signature to `def _report_coverage(self, approved, tier: str) -> bool:` and pass `options["tier"]` from `handle`. Replace the `checks` construction with:

```python
            all_checks: list[tuple[str, int, list[str], int]] = [
                ("stage 1 single_choice", 1, sorted(stage1_targets), _STAGE1_SINGLE_CHOICE_MIN),
                ("stage 2 single_choice", 2, role_subskills, _STAGE2_SINGLE_CHOICE_MIN),
                ("stage 2 multi_select", 2, role_subskills, _STAGE2_MULTI_SELECT_MIN),
                ("stage 2 open_ended", 2, role_subskills, _STAGE2_OPEN_ENDED_MIN),
            ]
            if tier == "1":
                checks = [c for c in all_checks if c[1] == 1]
            elif tier == "2":
                checks = [c for c in all_checks if c[1] == 2]
            else:
                checks = all_checks
```

Update the `handle` call site: `coverage_ok = self._report_coverage(approved, options["tier"])`.

- [ ] **Step 4: Run the test + the existing corpus tests to verify no regression**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_audit_tiers.py apps/assessments/tests/test_scenario_corpus.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/management/commands/scenario_corpus_audit.py apps/assessments/tests/test_audit_tiers.py
git commit -m "feat(assessments): tiered scenario_corpus_audit (--tier 1|2|all)"
```

---

### Task 7: Generate → review → promote Tier-1 content for all roles (operational)

**Files:**
- Modify (content): `scenario_corpus/{frontend,fullstack,data_science,devops,android,machine_learning_engineer,ui_ux_designer}.py`, `backend.py`

This task consumes Gemini quota — run deliberately with a real `GEMINI_API_KEY`, not in CI.

- [ ] **Step 1: Generate drafts for each empty role (Tier 1)**

For each role, run (example for `frontend`):

```bash
cd Backend
venv/bin/python manage.py generate_scenarios --role frontend --tier 1 --limit 12
```

Repeat for `fullstack`, `data_science`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`, and `backend` (to top up its stage-1 floor of ≥2 per calibration subskill).

- [ ] **Step 2: Review and promote each role**

```bash
venv/bin/python manage.py review_scenarios --role frontend
```

Inspect each draft against the `AUTHOR_GUIDE` bar; accept good ones, reject weak ones (rejected stay in staging for a regenerate). Repeat per role. For a fast first pass you may use `--yes` then manually prune, but a human read is the quality gate the design depends on.

- [ ] **Step 3: Format promoted modules**

```bash
venv/bin/python -m black apps/assessments/scenario_corpus/
```

- [ ] **Step 4: Gate on the Tier-1 audit for every role**

```bash
env -u GEMINI_API_KEY venv/bin/python manage.py scenario_corpus_audit --tier 1
```

Expected: `Audit PASSED.` — every role's stage-1 calibration subskills now have ≥2 approved `single_choice` scenarios. If gaps remain, generate more for the named subskills and re-review.

- [ ] **Step 5: Rebuild the index and run corpus/retriever tests**

```bash
venv/bin/python manage.py rebuild_scenario_index
env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_scenario_corpus.py apps/assessments/tests/test_scenario_retriever.py -v
```

Expected: PASS, with the index reporting the new total scenario count.

- [ ] **Step 6: Commit**

```bash
git add apps/assessments/scenario_corpus/*.py
git commit -m "content(assessments): Tier-1 stage-1 scenarios for all 8 roles"
```

---

# Phase 2 — Confirm RAG on + retrieval eval

### Task 8: Retrieval coverage/precision eval

**Files:**
- Create: `Backend/apps/assessments/scenario_corpus/eval/__init__.py` (empty)
- Create: `Backend/apps/assessments/scenario_corpus/eval/retrieval_eval.py`
- Test: `Backend/apps/assessments/tests/test_retrieval_eval.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_retrieval_eval.py
from __future__ import annotations

import pytest

from apps.assessments.scenario_corpus.eval.retrieval_eval import (
    RetrievalEvalResult,
    evaluate_role,
)


@pytest.mark.django_db
def test_evaluate_role_returns_coverage_and_precision_fields():
    result = evaluate_role("backend")
    assert isinstance(result, RetrievalEvalResult)
    assert 0.0 <= result.coverage <= 1.0
    assert 0.0 <= result.subskill_precision <= 1.0
    assert result.role_key == "backend"
    assert result.blueprint_count > 0
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_retrieval_eval.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `retrieval_eval.py`**

```python
# Backend/apps/assessments/scenario_corpus/eval/retrieval_eval.py
"""Deterministic retrieval eval for the scenario corpus.

For every Tier-1 blueprint, ask the retriever for a scenario and measure:
  - coverage: fraction of blueprints that returned >=1 scenario
  - subskill_precision: fraction of returned scenarios whose subskill_key
    exactly matches the requested one (i.e. not the broad-where fallback)
No Gemini calls; safe to gate in CI once the index is built.
"""

from __future__ import annotations

from dataclasses import dataclass

from apps.assessments.scenario_corpus.coverage import tier1_blueprints
from apps.assessments.scenario_retriever import ScenarioRetriever


@dataclass(frozen=True)
class RetrievalEvalResult:
    role_key: str
    blueprint_count: int
    coverage: float
    subskill_precision: float


def evaluate_role(role_key: str) -> RetrievalEvalResult:
    blueprints = tier1_blueprints(role_key)
    returned = 0
    subskill_hits = 0
    for bp in blueprints:
        docs = ScenarioRetriever.retrieve_for_blueprint(
            role_key=role_key,
            blueprint={
                "question_type": bp.question_type,
                "subskill_key": bp.subskill_key,
                "competency": bp.competency,
                "focus": bp.competency,
            },
            stage=bp.stage,
        )
        if docs:
            returned += 1
            if any(d.get("subskill_key") == bp.subskill_key for d in docs):
                subskill_hits += 1
    n = len(blueprints) or 1
    return RetrievalEvalResult(
        role_key=role_key,
        blueprint_count=len(blueprints),
        coverage=returned / n,
        subskill_precision=(subskill_hits / returned) if returned else 0.0,
    )


def evaluate_all(role_keys: list[str]) -> list[RetrievalEvalResult]:
    return [evaluate_role(role) for role in role_keys]
```

- [ ] **Step 4: Run the test**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_retrieval_eval.py -v`
Expected: PASS. (Requires the index built in Task 7 Step 5; rebuild if needed.)

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/scenario_corpus/eval/__init__.py apps/assessments/scenario_corpus/eval/retrieval_eval.py apps/assessments/tests/test_retrieval_eval.py
git commit -m "feat(assessments): deterministic scenario retrieval eval"
```

---

### Task 9: Confirm flag, bump corpus version, publish eval doc (operational)

**Files:**
- Modify: `scenario_corpus/registry.py` (version bump)
- Create: `docs/product/SCENARIO_RAG_EVAL.md`

- [ ] **Step 1: Confirm the flag is on and not overridden**

```bash
cd Backend
grep -n "ASSESSMENT_SCENARIO_RAG_ENABLED" apps/core/ai_settings.py   # default=True
grep -n "ASSESSMENT_SCENARIO_RAG_ENABLED" .env 2>/dev/null || echo "no .env override (good)"
```

Expected: code default `True`; no `.env` line forcing `false`. If `.env` disables it, remove that line.

- [ ] **Step 2: Capture the before/after numbers**

Run the eval per role and record the table (coverage + subskill_precision). Before = the pre-Task-7 state (0% for the 7 empty roles — note it from the spec's measured baseline); after = current:

```bash
env -u GEMINI_API_KEY venv/bin/python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development'); django.setup()
from apps.assessments.scenario_corpus.eval.retrieval_eval import evaluate_all
from apps.assessments.role_graph import SUPPORTED_ROLES
for r in evaluate_all(SUPPORTED_ROLES):
    print(f'{r.role_key:28s} coverage={r.coverage:.2f} subskill_precision={r.subskill_precision:.2f} n={r.blueprint_count}')
"
```

- [ ] **Step 3: Bump the corpus version**

In `scenario_corpus/registry.py`, change `SCENARIO_CORPUS_VERSION = "scenario-v1"` → `"scenario-v2"`. Update every promoted scenario's `corpus_version` to match (sed or re-run a small fixup), then re-validate:

```bash
env -u GEMINI_API_KEY venv/bin/python manage.py scenario_corpus_audit --tier 1 --skip-duplicates
```

Expected: validation OK (no `corpus_version` mismatch), Tier-1 coverage OK.

- [ ] **Step 4: Write `docs/product/SCENARIO_RAG_EVAL.md`**

Mirror `docs/product/RAG_RETRIEVAL_EVAL.md`: a per-role before/after table (coverage, subskill_precision), the method (deterministic, Tier-1 blueprints), and the corpus version. State plainly that "before" was ~0% coverage for the 7 empty roles.

- [ ] **Step 5: Rebuild index, full assessment suite, commit**

```bash
venv/bin/python manage.py rebuild_scenario_index
env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/ -q
git add apps/assessments/scenario_corpus/registry.py apps/assessments/scenario_corpus/*.py docs/product/SCENARIO_RAG_EVAL.md
git commit -m "docs(assessments): scenario RAG retrieval eval + corpus v2 bump"
```

---

# Phase 3 — Question-quality A/B (rubric + LLM-judge)

### Task 10: Deterministic rubric scorer

**Files:**
- Create: `Backend/apps/assessments/scenario_corpus/eval/rubric.py`
- Test: `Backend/apps/assessments/tests/test_rubric.py`

- [ ] **Step 1: Write the failing test**

```python
# Backend/apps/assessments/tests/test_rubric.py
from __future__ import annotations

from apps.assessments.scenario_corpus.eval.rubric import score_question


def _good() -> dict:
    return {
        "scenario_context": "A payment API double-charges when a mobile client retries after a timeout.",
        "stem": "Which design prevents a duplicate charge while keeping the API predictable?",
        "options": [
            {"id": "a", "label": "Require an idempotency key and return the first result on retry."},
            {"id": "b", "label": "Let finance reverse duplicate charges overnight in a batch job."},
            {"id": "c", "label": "Convert the endpoint to GET so clients can retry safely each time."},
            {"id": "d", "label": "Delay every charge a few seconds so retries arrive before processing."},
        ],
    }


def test_good_question_scores_high():
    result = score_question(_good(), role_key="backend")
    assert result["has_concrete_scenario"] is True
    assert result["no_banned_phrase"] is True
    assert result["options_parallel"] is True
    assert result["total"] >= 3


def test_banned_phrase_flagged():
    bad = _good()
    bad["options"][0]["label"] = "Disable logging to avoid the duplicate."
    result = score_question(bad, role_key="backend")
    assert result["no_banned_phrase"] is False
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_rubric.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement `rubric.py`**

```python
# Backend/apps/assessments/scenario_corpus/eval/rubric.py
"""Deterministic question-quality rubric, derived from AUTHOR_GUIDE.

Scores a generated question on cheap, reproducible signals so RAG-on vs RAG-off
can be compared without an LLM. Each check is a bool; `total` is their sum.
"""

from __future__ import annotations

import statistics
from typing import Any

_BANNED = (
    "disable logging",
    "preserves correctness, clarity, and maintainability",
    "generic self-rating",
)

# Minimal role-vocabulary anchors (extend per role as needed).
_ROLE_VOCAB = {
    "backend": ("idempotency", "queryset", "index", "transaction", "cache", "latency", "n+1"),
    "frontend": ("hydration", "re-render", "memo", "layout", "accessibility", "bundle"),
    "data_science": ("leakage", "bias", "variance", "stratified", "feature", "overfit"),
    "devops": ("rollback", "pipeline", "container", "scaling", "observability", "deploy"),
    "android": ("lifecycle", "coroutine", "recompose", "viewmodel", "intent", "fragment"),
    "machine_learning_engineer": ("inference", "throughput", "quantization", "serving", "drift"),
    "ui_ux_designer": ("affordance", "hierarchy", "contrast", "flow", "usability", "wireframe"),
    "fullstack": ("api", "state", "cache", "auth", "render", "schema"),
}


def score_question(question: dict[str, Any], *, role_key: str) -> dict[str, Any]:
    scenario = str(question.get("scenario_context") or "").strip()
    stem = str(question.get("stem") or "").lower()
    options = question.get("options") or []
    blob = " ".join([scenario.lower(), stem] + [str(o.get("label", "")).lower() for o in options])

    has_concrete_scenario = len(scenario.split()) >= 8
    no_banned_phrase = not any(b in blob for b in _BANNED)
    decision_not_definition = any(
        w in stem for w in ("which", "best", "most", "strongest", "prevents", "reduces")
    )
    if len(options) >= 2:
        lengths = [len(str(o.get("label", ""))) for o in options]
        options_parallel = (statistics.pstdev(lengths) / (statistics.mean(lengths) or 1)) < 0.5
    else:
        options_parallel = True
    vocab = _ROLE_VOCAB.get(role_key, ())
    uses_role_vocab = any(term in blob for term in vocab)

    checks = {
        "has_concrete_scenario": has_concrete_scenario,
        "no_banned_phrase": no_banned_phrase,
        "decision_not_definition": decision_not_definition,
        "options_parallel": options_parallel,
        "uses_role_vocab": uses_role_vocab,
    }
    checks["total"] = sum(1 for v in checks.values() if v is True)
    return checks
```

- [ ] **Step 4: Run the test**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_rubric.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/assessments/scenario_corpus/eval/rubric.py apps/assessments/tests/test_rubric.py
git commit -m "feat(assessments): deterministic question-quality rubric scorer"
```

---

### Task 11: A/B harness + LLM-judge (operational, quota)

**Files:**
- Create: `Backend/apps/assessments/scenario_corpus/eval/ab_quality.py`
- Append results to: `docs/product/SCENARIO_RAG_EVAL.md`

- [ ] **Step 1: Implement the harness**

Create `ab_quality.py` with `run_ab(role_keys, n_per_role, judge=True)` that, per blueprint: generates a question with `ASSESSMENT_SCENARIO_RAG_ENABLED` forced `False` then `True` (toggle via `apps.core.ai_settings` monkeypatch or env), scores both with `rubric.score_question`, and — when `judge=True` — sends a blind randomized pair to `GemmaClient(task_type="json_generation")` asking for a 1–5 score per side plus a preferred side. Cache raw outputs to `eval/_cache/<role>.json`. Reuse the existing stage generation entry (`AssessmentAIService.generate_stage_one`) for question production so the A/B reflects the real pipeline.

```python
# Backend/apps/assessments/scenario_corpus/eval/ab_quality.py  (skeleton — fill judge prompt)
from __future__ import annotations

import random
from dataclasses import dataclass

from apps.assessments.scenario_corpus.eval.rubric import score_question
from apps.core.gemma_client import GemmaClient


@dataclass
class ABRow:
    role_key: str
    rubric_on: float
    rubric_off: float
    judge_prefers_on: bool | None


_JUDGE_SYSTEM = "You are a strict assessment reviewer. Return JSON only."
_JUDGE_PROMPT = (
    "Two assessment questions, A and B. Score each 1-5 for: concrete scenario, "
    "real tradeoff (not definition), plausible distractors, role vocabulary. "
    'Return {{"a_score": int, "b_score": int, "preferred": "a"|"b"}}.\n\n'
    "A:\n{a}\n\nB:\n{b}"
)


def judge_pair(a_text: str, b_text: str) -> dict:
    client = GemmaClient(task_type="json_generation")
    resp = client.generate_structured(
        prompt=_JUDGE_PROMPT.format(a=a_text, b=b_text),
        system=_JUDGE_SYSTEM,
        required_keys=("a_score", "b_score", "preferred"),
    )
    return resp.payload or {}
```

- [ ] **Step 2: Run the study (real GEMINI_API_KEY, deliberate)**

```bash
cd Backend
venv/bin/python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development'); django.setup()
from apps.assessments.scenario_corpus.eval.ab_quality import run_ab
from apps.assessments.role_graph import SUPPORTED_ROLES
print(run_ab(SUPPORTED_ROLES, n_per_role=4, judge=True))
"
```

- [ ] **Step 3: Record results + caveats**

Append to `docs/product/SCENARIO_RAG_EVAL.md`: rubric deltas (RAG-on minus RAG-off, per role + overall) and the LLM-judge win-rate, with the explicit caveat that it is a small (~30/condition) study, quota-bounded, outputs cached, not a benchmark.

- [ ] **Step 4: Commit**

```bash
git add apps/assessments/scenario_corpus/eval/ab_quality.py docs/product/SCENARIO_RAG_EVAL.md
git commit -m "feat(assessments): RAG on/off question-quality A/B (rubric + LLM-judge)"
```

---

# Phase 4 — Tier 2 demand-weighted

### Task 12: Tier-2 demand set + audit Tier-2 matrix

**Files:**
- Modify: `Backend/apps/assessments/scenario_corpus/coverage.py` (add `tier2_subskills`, extend `uncovered_blueprints` for tier 2)
- Modify: `Backend/apps/assessments/management/commands/scenario_corpus_audit.py` (use the demand set for the tier-2 report)
- Modify: `Backend/apps/assessments/tests/test_coverage_planner.py` (add tier-2 cases)

- [ ] **Step 1: Write the failing test**

Add to `test_coverage_planner.py`:

```python
@pytest.mark.django_db
def test_tier2_subskills_are_a_subset_of_all_subskills():
    from apps.assessments.scenario_corpus.coverage import tier2_subskills
    from apps.assessments.role_graph_data import ROLE_GRAPHS

    all_subs = {s.key for d in ROLE_GRAPHS["backend"].dimensions for s in d.subskills}
    demand = set(tier2_subskills("backend"))
    assert demand and demand.issubset(all_subs)
    assert len(demand) < len(all_subs)  # demand-weighted, not all 44
```

- [ ] **Step 2: Run it to verify it fails**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_coverage_planner.py -k tier2 -v`
Expected: FAIL — `tier2_subskills` undefined.

- [ ] **Step 3: Implement `tier2_subskills`**

Add to `coverage.py`. Derive the stage-2 demand set from the engine's targeting: the stage-1 calibration subskills plus, for each dimension, its highest-`assessment_weight` subskills, capped to keep the set ~10–12. Concretely:

```python
def tier2_subskills(role_key: str, *, per_dimension: int = 2) -> list[str]:
    """Subskills stage 2 actually targets: calibration set + top-weighted per dimension."""
    graph = ROLE_GRAPHS[role_key]
    demand: list[str] = list(stage1_calibration_subskills(role_key))
    for dimension in graph.dimensions:
        ranked = sorted(
            dimension.subskills,
            key=lambda s: getattr(s, "target_proficiency", 0),
            reverse=True,
        )
        for subskill in ranked[:per_dimension]:
            if subskill.key not in demand:
                demand.append(subskill.key)
    return demand
```

Extend `uncovered_blueprints` to handle `tier=2` by iterating `tier2_subskills(role_key)` across the three stage-2 question types with their floors (`single_choice`×2, `multi_select`×1, `open_ended`×1), mirroring the Tier-1 logic. Remove the `if tier != 1: raise` guard.

- [ ] **Step 4: Wire the audit Tier-2 report to the demand set**

In `scenario_corpus_audit.py`, when `tier == "2"`, replace `role_subskills` for the stage-2 checks with `tier2_subskills(role_key)` (import it). Tier-1 and `all` behavior is unchanged except `all` keeps the full per-subskill floor for backwards compatibility — document this in the command docstring.

- [ ] **Step 5: Run tests**

Run: `env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/tests/test_coverage_planner.py apps/assessments/tests/test_audit_tiers.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/assessments/scenario_corpus/coverage.py apps/assessments/management/commands/scenario_corpus_audit.py apps/assessments/tests/test_coverage_planner.py
git commit -m "feat(assessments): Tier-2 demand-weighted coverage + audit matrix"
```

---

### Task 13: Fill Tier-2 for backend + showcase role(s) (operational)

- [ ] **Step 1: Generate Tier-2 drafts**

```bash
cd Backend
venv/bin/python manage.py generate_scenarios --role backend --tier 2 --limit 40
```

Repeat for 1–2 showcase roles (e.g. `frontend`). Other roles' Tier-2 drafts may be generated and left in staging as a demonstration without promotion.

- [ ] **Step 2: Review, promote, format, audit Tier 2**

```bash
venv/bin/python manage.py review_scenarios --role backend
venv/bin/python -m black apps/assessments/scenario_corpus/
env -u GEMINI_API_KEY venv/bin/python manage.py scenario_corpus_audit --tier 2
```

Expected: Tier-2 audit PASSED for backend (+ showcase role).

- [ ] **Step 3: Rebuild index, bump version, test, commit**

```bash
venv/bin/python manage.py rebuild_scenario_index
env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/ -q
git add apps/assessments/scenario_corpus/*.py
git commit -m "content(assessments): Tier-2 stage-2 scenarios for backend + showcase role"
```

---

# Phase 5 — Docs

### Task 14: Update AUTHOR_GUIDE, eval doc, and CLAUDE.md

**Files:**
- Modify: `scenario_corpus/AUTHOR_GUIDE.md`, `Backend/CLAUDE.md`, root `CLAUDE.md`

- [ ] **Step 1: AUTHOR_GUIDE — document the pipeline workflow**

Add a "Pipeline-assisted authoring" section: `generate_scenarios` → `review_scenarios` (validate + dedup + promote) → `rebuild_scenario_index`, and the tiered floor (`--tier 1|2`). Keep the existing manual loop as the fallback.

- [ ] **Step 2: Correct the stale flag claim**

In `Backend/CLAUDE.md`, change the Assessment Scenario RAG line from "Default-off (`ASSESSMENT_SCENARIO_RAG_ENABLED=false`)" to "Default-on; retrieval returns `[]` safely for any role/subskill without approved scenarios." Update the seed-count note to reflect the new corpus.

- [ ] **Step 3: Update the module-status table**

In root `CLAUDE.md`, update the Assessments row to note all 8 roles seeded (Tier 1) + Tier-2 for backend/showcase, with the retrieval + A/B eval at `docs/product/SCENARIO_RAG_EVAL.md`.

- [ ] **Step 4: Full suite + commit**

```bash
cd Backend && env -u GEMINI_API_KEY venv/bin/python -m pytest apps/assessments/ -q
git add ../CLAUDE.md Backend/CLAUDE.md apps/assessments/scenario_corpus/AUTHOR_GUIDE.md
git commit -m "docs(assessments): pipeline workflow, tiered floor, corrected flag status"
```

---

## Self-Review notes (addressed)

- **Spec coverage:** §2 pipeline → Tasks 1–5; §3 tiered coverage → Tasks 1, 6, 12; §4 defensibility (human-review gate + staging) → Tasks 3, 5; §5.1 retrieval eval → Task 8; §5.2 rubric + LLM-judge → Tasks 10, 11; §6 rollout phases → Phases 0–5; §7 testing → tests in every code task; §10 file inventory → File Structure.
- **Flag correction:** spec assumed default-off; code is default-on. Reflected in Phase 2 (confirm, don't flip) and Task 14 Step 2.
- **Type consistency:** `Blueprint` fields and `LLM_CONTENT_KEYS` are defined once (Tasks 1–2) and reused unchanged in Tasks 4, 8, 12; `staging._STAGING_DIR` / `_CORPUS_DIR` are the monkeypatch points used consistently in Tasks 3–5.
- **Quota safety:** every test mocks `generate_structured`; the only quota-consuming steps are Tasks 7, 11, 13 (operational, flagged, never CI).
