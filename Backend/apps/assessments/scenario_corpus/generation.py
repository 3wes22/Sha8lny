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
