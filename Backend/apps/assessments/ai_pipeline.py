"""
Staged assessment AI helpers, deterministic fallbacks, and legacy compatibility.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from decimal import Decimal
from statistics import mean
from time import monotonic
from typing import Any

from django.core.cache import cache

from apps.assessments.engine import (
    AnswerScorer,
    GapProfileBuilder,
    Stage2Allocator,
    StageAllocator,
    evidence_to_dicts,
    merge_evidence,
)
from apps.assessments.fallback_scenarios import get_curated_fallback_scenario
from apps.assessments.models import Assessment
from apps.assessments.role_graph import load_role_graph, resolve_role_key
from apps.assessments.services import BaselineAssessmentAnalyzer
from apps.core.ai_contracts import (
    AIInvocationMetadata,
    AssessmentAnalysisInput,
    AssessmentAnalysisResult,
    RoadmapSignal,
)
from apps.core.ai_logging import build_ai_metadata
from apps.core.ai_settings import AI_PROVIDER, LLM_TIMEOUT_SECONDS
from apps.core.ai_validation import (
    build_stage_validation_flags,
    build_stage_choice_options,
    sanitize_evaluation_payload,
    sanitize_stage_question_payload,
)
from apps.core.exceptions import AIServiceError
from apps.core.gemma_client import GemmaClient, GemmaResponse


logger = logging.getLogger(__name__)


QUESTION_SYSTEM_PROMPT = """You generate concise staged assessment questions.
Return strict JSON with a top-level "questions" array only."""
OPTION_REPAIR_SYSTEM_PROMPT = """You repair malformed staged assessment items.
Return strict JSON with a top-level "questions" array only."""

EVALUATION_SYSTEM_PROMPT = """You summarize staged assessment evidence for a career platform.
Return strict JSON only with overall_score, strengths, areas_for_improvement,
recommended_careers, recommended_learning_paths, ai_insights, and ai_confidence_score."""

STAGE_QUESTION_FEW_SHOT_EXAMPLES = """
Use the few-shot examples below as the quality bar. Follow the same field names and realism level.

Example single_choice:
{
  "subskill_key": "http_api_design",
  "competency": "HTTP API Design",
  "learning_objective": "Choose the safest payment retry design for a write endpoint.",
  "scenario_context": "A payment API receives duplicate POST /payments requests after the client times out and retries.",
  "stem": "Which design best prevents a double charge while keeping the API predictable?",
  "question_type": "single_choice",
  "difficulty": 3,
  "estimated_seconds": 50,
  "options": [
    {"id": "a", "label": "Require an idempotency key and replay the first successful result."},
    {"id": "b", "label": "Accept both requests and reconcile duplicate charges later."},
    {"id": "c", "label": "Convert the endpoint to GET so retries are safe."},
    {"id": "d", "label": "Delay each charge for a few seconds before processing."}
  ],
  "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
  "explanation": "The API needs deterministic write deduplication at request time.",
  "correct_answer_rationale": "Idempotency keys treat retries as the same logical operation without changing the write contract.",
  "option_rationales": [
    {"option_id": "a", "is_correct": true, "rationale": "It makes duplicate retries deterministic and observable."},
    {"option_id": "b", "is_correct": false, "rationale": "It accepts corruption first and relies on cleanup later."},
    {"option_id": "c", "is_correct": false, "rationale": "GET must not perform side effects."},
    {"option_id": "d", "is_correct": false, "rationale": "Timing delays do not eliminate duplicates under concurrency."}
  ]
}

Example multi_select:
{
  "subskill_key": "query_optimization",
  "competency": "Query Optimization",
  "learning_objective": "Choose the strongest evidence-first actions for a slow relational query.",
  "scenario_context": "A products query takes four seconds on two million rows and the team has not checked the execution plan yet.",
  "stem": "Which next actions are strongest? Select all that apply.",
  "question_type": "multi_select",
  "difficulty": 4,
  "estimated_seconds": 70,
  "options": [
    {"id": "a", "label": "Capture EXPLAIN ANALYZE output to inspect row estimates and scan strategy."},
    {"id": "b", "label": "Add an index that matches the hot predicate after the plan confirms it."},
    {"id": "c", "label": "Refactor unrelated ORM code before collecting measurements."},
    {"id": "d", "label": "Check cardinality and whether the predicate belongs in a dedicated indexed column."},
    {"id": "e", "label": "Drop the JSONB column immediately because relational databases dislike flexible schemas."}
  ],
  "answer_key": {"correct_option_ids": ["a", "b", "d"], "scoring": "partial_credit"},
  "explanation": "Strong tuning starts with measured plan evidence and a targeted index or schema change.",
  "correct_answer_rationale": "The right sequence moves from evidence to a specific fix instead of guessing at causes.",
  "option_rationales": [
    {"option_id": "a", "is_correct": true, "rationale": "The plan shows where time and bad estimates come from."},
    {"option_id": "b", "is_correct": true, "rationale": "Index design should match the confirmed access pattern."},
    {"option_id": "c", "is_correct": false, "rationale": "It changes unrelated code before confirming the database bottleneck."},
    {"option_id": "d", "is_correct": true, "rationale": "Cardinality and schema shape determine whether indexing can help."},
    {"option_id": "e", "is_correct": false, "rationale": "It jumps to a destructive schema change without evidence."}
  ]
}

Example open_ended:
{
  "subskill_key": "logging_monitoring",
  "competency": "Logging and Monitoring",
  "learning_objective": "Explain how to isolate a cross-service latency incident with correlated telemetry.",
  "scenario_context": "A checkout request intermittently spikes to five seconds across three services during peak traffic.",
  "stem": "Explain how you would narrow the failing boundary and what evidence you would collect first.",
  "question_type": "open_ended",
  "difficulty": 4,
  "estimated_seconds": 90,
  "options": [],
  "answer_key": {
    "expected_concepts": ["trace or correlation id", "structured logs", "latency or error-rate metrics by hop"],
    "required_concept_count": 2,
    "forbidden_concepts": ["disable logging"],
    "scoring": "concept_coverage"
  },
  "explanation": "A strong answer correlates evidence across services instead of restarting blindly.",
  "correct_answer_rationale": "The answer should connect request tracing with per-hop telemetry.",
  "option_rationales": []
}
"""


@dataclass(frozen=True)
class StagedAssessmentEvaluation:
    analysis: AssessmentAnalysisResult
    roadmap_signal: RoadmapSignal
    prompt_tokens: int
    completion_tokens: int


def _stage_question_type_sequence(*, stage: int, count: int) -> list[str]:
    if stage == 1:
        return ["single_choice"] * count
    base = ["single_choice", "single_choice", "multi_select", "single_choice", "open_ended"]
    return (base + ["single_choice"] * count)[:count]


def _build_stage_blueprints(role_graph, targets, *, stage: int, gap_profile=None) -> list[dict[str, Any]]:
    question_types = _stage_question_type_sequence(stage=stage, count=len(targets))
    if stage == 2 and gap_profile and gap_profile.uncertain_areas:
        uncertain_lookup = {
            key: index
            for index, key in enumerate(target.key for target in targets)
            if key in set(gap_profile.uncertain_areas)
        }
        if uncertain_lookup and "open_ended" in question_types:
            open_ended_index = question_types.index("open_ended")
            uncertain_index = min(uncertain_lookup.values())
            question_types[open_ended_index], question_types[uncertain_index] = (
                question_types[uncertain_index],
                question_types[open_ended_index],
            )

    blueprints: list[dict[str, Any]] = []
    for index, (target, question_type) in enumerate(zip(targets, question_types, strict=False), start=1):
        if stage == 1:
            progression_band = (
                "fundamentals"
                if index <= 2
                else "applied_debugging"
                if index <= 4
                else "tradeoff_reasoning"
            )
        else:
            progression_band = (
                "targeted_diagnosis"
                if question_type == "single_choice"
                else "evidence_selection"
                if question_type == "multi_select"
                else "written_tradeoff_reasoning"
            )
        intent = {
            "single_choice": "narrow one decision so exactly one best answer exists",
            "multi_select": "ask for multiple concrete practices that are all required",
            "open_ended": "ask for a concise written explanation of strategy and tradeoffs",
        }[question_type]
        blueprints.append(
            {
                "slot": index,
                "subskill_key": target.key,
                "competency": target.label,
                "dimension_key": target.dimension,
                "question_type": question_type,
                "difficulty": min(5, max(1, target.target_proficiency + (1 if stage == 2 else 0))),
                "estimated_seconds": 45 if question_type == "single_choice" else 70 if question_type == "multi_select" else 90,
                "learning_objective_hint": (
                    f"Assess concrete judgment in {target.label.lower()} using one main competency only."
                    if stage == 1
                    else f"Assess deeper diagnosis, tradeoffs, or failure analysis in {target.label.lower()}."
                ),
                "progression_band": progression_band,
                "focus": intent,
                "gap_priority": (
                    "uncertain"
                    if gap_profile and target.key in set(gap_profile.uncertain_areas)
                    else "high_priority"
                    if gap_profile and target.key in set(gap_profile.high_priority_gaps)
                    else "normal"
                ),
            }
        )
    return blueprints


def _choice_options(subskill_label: str) -> list[dict[str, Any]]:
    return build_stage_choice_options(subskill_label)


def _default_question_text(*, stage: int, subskill, role_label: str) -> str:
    role = role_label.lower()
    skill = subskill.label.lower()
    if stage == 1:
        return (
            f"In a real {role} task, which option best matches how you would handle "
            f"{skill}?"
        )
    return (
        f"You are reviewing a {role} task focused on {skill}. "
        "Which option best matches your next step?"
    )


def _contract_safe_stage_template(
    *,
    stage: int,
    subskill,
    role_key: str,
    role_label: str,
    question_type: str,
) -> dict[str, Any]:
    curated = get_curated_fallback_scenario(
        role_key=role_key,
        subskill_key=subskill.key,
        stage=stage,
        question_type=question_type,
    )
    if curated is not None:
        return curated

    skill = subskill.label.lower()
    role = role_label.lower()

    if question_type == "multi_select":
        scenario_context = (
            f"A {role} team is reviewing a risky {skill} change before it reaches production."
        )
        stem = "Which next actions are strongest? Select all that apply."
        return {
            "scenario_context": scenario_context,
            "stem": stem,
            "question_text": f"{scenario_context} {stem}",
            "type": "multiple_choice",
            "interaction_mode": "multi_select",
            "options": [
                {"id": "a", "value": "a", "label": "Collect the logs, traces, tests, or request evidence that isolate the risky path."},
                {"id": "b", "value": "b", "label": "Confirm assumptions, inputs, and edge cases before changing multiple components."},
                {"id": "c", "value": "c", "label": "Refactor adjacent modules first so the final change can be bundled into one deploy."},
                {"id": "d", "value": "d", "label": "Add targeted guards, validation, or rollback protection around the risky behavior."},
                {"id": "e", "value": "e", "label": "Expand the scope to nearby services before confirming the primary failure boundary."},
            ],
            "answer_key": {
                "correct_option_ids": ["a", "b", "d"],
                "scoring": "partial_credit",
            },
            "learning_objective": f"Identify the strongest diagnostic or review actions for {skill}.",
            "explanation": "Strong answers focus on evidence, constraints, and safe changes.",
            "correct_answer_rationale": (
                "The strongest actions gather evidence, validate assumptions, and narrow the risky path before broadening the change."
            ),
            "option_rationales": [
                {
                    "option_id": "a",
                    "is_correct": True,
                    "rationale": "It gathers direct evidence about the path that is actually risky.",
                },
                {
                    "option_id": "b",
                    "is_correct": True,
                    "rationale": "It reduces avoidable mistakes before code changes compound the incident.",
                },
                {
                    "option_id": "c",
                    "is_correct": False,
                    "rationale": "Bundling adjacent refactors increases scope before the core issue is understood.",
                },
                {
                    "option_id": "d",
                    "is_correct": True,
                    "rationale": "Risk-limiting safeguards are useful once the boundary is understood.",
                },
                {
                    "option_id": "e",
                    "is_correct": False,
                    "rationale": "Broadening scope too early makes the diagnosis slower and noisier.",
                },
            ],
            "helper": "Select the actions that gather evidence first and keep the change set controlled.",
        }

    if question_type == "open_ended":
        scenario_context = (
            f"A production issue related to {skill} has mixed signals across a {role} system."
        )
        stem = "Explain how you would narrow the failure boundary and what evidence you would collect first."
        return {
            "scenario_context": scenario_context,
            "stem": stem,
            "question_text": f"{scenario_context} {stem}",
            "type": "text",
            "interaction_mode": "text",
            "options": [],
            "answer_key": {
                "expected_concepts": ["evidence", "failure boundary", "tradeoffs"],
                "required_concept_count": 2,
                "forbidden_concepts": ["guess without evidence"],
                "scoring": "concept_coverage",
            },
            "learning_objective": f"Explain how to reason through the key risks in {skill}.",
            "explanation": "A strong answer names evidence, tradeoffs, and likely failure points before proposing changes.",
            "correct_answer_rationale": (
                "The answer should connect evidence gathering with the tradeoffs that drive the next engineering step."
            ),
            "option_rationales": [],
            "helper": "Name the evidence you would inspect, the likely boundary, and the tradeoffs you would weigh.",
        }

    if stage == 1:
        scenario_context = (
            f"A {role} team is preparing a {skill} change that could affect correctness, rollback safety, and support load."
        )
        stem = "Which option best reduces risk while preserving the intended behavior?"
        options = [
            {"id": "a", "value": "a", "label": "Clarify the highest-risk assumption and make the smallest safe change that preserves observability."},
            {"id": "b", "value": "b", "label": "Bundle several adjacent refactors into the same release so the team only deploys once."},
            {"id": "c", "value": "c", "label": "Ship the change first and plan to handle edge cases after users report them."},
            {"id": "d", "value": "d", "label": "Move the logic to a less familiar subsystem to keep the original code untouched."},
        ]
        helper = "Choose the option that narrows risk without hiding future diagnosis."
        learning_objective = f"Choose the safest first engineering move for {skill}."
        correct_option_ids = ["a"]
        correct_answer_rationale = (
            "The strongest move reduces risk and preserves evidence before the team broadens scope."
        )
        option_rationales = [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It reduces risk while keeping the change narrow and observable.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "Bundling refactors increases blast radius and makes failures harder to isolate.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "It treats production feedback as the requirements process.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "It moves risk to a less understood area instead of managing it directly.",
            },
        ]
    else:
        scenario_context = (
            f"A production issue tied to {skill} has mixed signals and the {role} team must choose the next diagnostic step carefully."
        )
        stem = "Which next step is most likely to isolate the failure boundary without hiding evidence?"
        options = [
            {"id": "a", "value": "a", "label": "Change timeout and retry settings globally before confirming which boundary is failing."},
            {"id": "b", "value": "b", "label": "Use the current evidence to isolate the boundary and validate the highest-risk assumption first."},
            {"id": "c", "value": "c", "label": "Broaden the investigation to nearby components before the core failure mode is confirmed."},
            {"id": "d", "value": "d", "label": "Wait for another incident so the team has more volume before diagnosing."},
        ]
        helper = "Choose the next step that narrows the failing boundary with the least extra blast radius."
        learning_objective = f"Choose the strongest diagnostic or review decision for {skill}."
        correct_option_ids = ["b"]
        correct_answer_rationale = (
            "The best next step narrows the boundary with evidence before applying global mitigations or broadening the change."
        )
        option_rationales = [
            {
                "option_id": "a",
                "is_correct": False,
                "rationale": "Global mitigations can mask the symptom without identifying the actual failing boundary.",
            },
            {
                "option_id": "b",
                "is_correct": True,
                "rationale": "It focuses diagnosis on the highest-value evidence already available.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "It increases scope before the core failure path is verified.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "Deferring diagnosis adds delay without improving the evidence quality.",
            },
        ]

    return {
        "scenario_context": scenario_context,
        "stem": stem,
        "question_text": f"{scenario_context} {stem}",
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": options,
        "answer_key": {
            "correct_option_ids": correct_option_ids,
            "scoring": "single_best",
        },
        "learning_objective": learning_objective,
        "explanation": "The strongest answer preserves evidence, manages risk, and keeps the system diagnosable.",
        "correct_answer_rationale": correct_answer_rationale,
        "option_rationales": option_rationales,
        "helper": helper,
    }


def _target_map(role_graph, targets, *, stage: int, gap_profile=None):
    blueprints = _build_stage_blueprints(role_graph, targets, stage=stage, gap_profile=gap_profile)
    return {
        target.key: {
            **(
                lambda template: {
                    "type": template["type"],
                    "interaction_mode": template["interaction_mode"],
                    "options": template["options"],
                    "helper": template["helper"],
                    "fallback_question_text": template["question_text"],
                    "fallback_scenario_context": template.get("scenario_context", ""),
                    "fallback_answer_key": template["answer_key"],
                    "fallback_explanation": template.get("explanation", ""),
                    "fallback_correct_answer_rationale": template.get("correct_answer_rationale", ""),
                    "fallback_option_rationales": template.get("option_rationales", []),
                    "learning_objective": template.get("learning_objective", ""),
                }
            )(
                _contract_safe_stage_template(
                    stage=stage,
                    subskill=target,
                    role_key=role_graph.role_key,
                    role_label=role_graph.role_label,
                    question_type=blueprint["question_type"],
                )
            ),
            "dimension_key": target.dimension,
            "category": target.label,
            "question_type": blueprint["question_type"],
            "difficulty": blueprint["difficulty"],
            "estimated_seconds": blueprint["estimated_seconds"],
        }
        for target, blueprint in zip(targets, blueprints, strict=False)
    }


def _normalize_question(
    *,
    stage: int,
    index: int,
    subskill,
    role_label: str,
    targeted: bool = False,
) -> dict[str, Any]:
    question_text = _default_question_text(
        stage=stage,
        subskill=subskill,
        role_label=role_label,
    )
    return {
        "id": f"s{stage}_q{index}",
        "stage": stage,
        "subskill_key": subskill.key,
        "dimension_key": subskill.dimension,
        "question_text": question_text,
        "question": question_text,
        "question_type": "single_choice",
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": _choice_options(subskill.label),
        "difficulty": min(5, max(1, subskill.target_proficiency)),
        "estimated_seconds": 45,
        "category": subskill.label,
        "competency": subskill.label,
        "learning_objective": "",
        "answer_key": {},
        "explanation": "",
        "validation_flags": [],
        "helper": (
            "Choose the option closest to what you can do without help today."
            if not targeted
            else "Pick the option that best matches your debugging or review judgment."
        ),
    }


def get_default_questions(target_career: str = "") -> list[dict[str, Any]]:
    role_graph = load_role_graph(resolve_role_key(target_career))
    targets = StageAllocator.allocate_stage_one(role_graph)
    return [
        _normalize_question(
            stage=1,
            index=index,
            subskill=target,
            role_label=role_graph.role_label,
        )
        for index, target in enumerate(targets, start=1)
    ]


class AssessmentAIService:
    client_class = GemmaClient
    stage_one_cache_ttl_seconds = 7 * 24 * 60 * 60
    stage_question_prompt_version = "v6"
    # Leave headroom under the 120s task soft limit while avoiding cold-start fallbacks.
    stage_question_timeout_floor_seconds = 115

    @classmethod
    def _get_client(
        cls,
        *,
        task_type: str = "json_generation",
        timeout_seconds: int | None = None,
        max_output_tokens: int | None = None,
    ) -> GemmaClient:
        if timeout_seconds is None:
            timeout_seconds = LLM_TIMEOUT_SECONDS
        return cls.client_class(
            task_type=task_type,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens or cls.client_class().max_output_tokens,
        )

    @classmethod
    def _get_stage_question_client(cls) -> GemmaClient:
        return cls._get_client(
            task_type="assessment_question_generation",
            timeout_seconds=max(
                LLM_TIMEOUT_SECONDS,
                cls.stage_question_timeout_floor_seconds,
            ),
            max_output_tokens=3200,
        )

    @classmethod
    def _get_repair_client(cls) -> GemmaClient:
        return cls._get_client(
            task_type="rewriting",
            timeout_seconds=max(
                LLM_TIMEOUT_SECONDS,
                cls.stage_question_timeout_floor_seconds,
            ),
            max_output_tokens=3200,
        )

    @classmethod
    def _get_evaluation_client(cls) -> GemmaClient:
        return cls._get_client(
            task_type="assessment_quality_review",
            max_output_tokens=800,
        )

    @classmethod
    def _build_stage_question_response_json_schema(
        cls,
        blueprints: list[dict[str, Any]],
    ) -> dict[str, Any]:
        allowed_subskill_keys = [blueprint["subskill_key"] for blueprint in blueprints]
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["questions"],
            "properties": {
                "questions": {
                    "type": "array",
                    "minItems": len(blueprints),
                    "maxItems": len(blueprints),
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "subskill_key",
                            "competency",
                            "learning_objective",
                            "scenario_context",
                            "stem",
                            "question_type",
                            "difficulty",
                            "estimated_seconds",
                            "options",
                            "answer_key",
                            "explanation",
                            "correct_answer_rationale",
                            "option_rationales",
                        ],
                        "properties": {
                            "subskill_key": {
                                "type": "string",
                                "enum": allowed_subskill_keys,
                                "description": "Target backend subskill key for this slot.",
                            },
                            "competency": {
                                "type": "string",
                                "description": "Human-readable skill label.",
                            },
                            "learning_objective": {
                                "type": "string",
                                "description": "One sentence describing what the question measures.",
                            },
                            "scenario_context": {
                                "type": "string",
                                "description": "One or two sentences describing the concrete engineering scenario.",
                            },
                            "stem": {
                                "type": "string",
                                "description": "The decision prompt that follows the scenario.",
                            },
                            "question_type": {
                                "type": "string",
                                "enum": ["single_choice", "multi_select", "open_ended"],
                                "description": "Semantic question type.",
                            },
                            "difficulty": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 5,
                                "description": "Difficulty from 1 (basic) to 5 (advanced).",
                            },
                            "estimated_seconds": {
                                "type": "integer",
                                "minimum": 30,
                                "maximum": 120,
                                "description": "Estimated answer time in seconds.",
                            },
                            "options": {
                                "type": "array",
                                "minItems": 0,
                                "maxItems": 6,
                                "description": "Closed-question answer options. Use an empty array for open-ended questions.",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["id", "label"],
                                    "properties": {
                                        "id": {
                                            "type": "string",
                                            "description": "Stable option identifier such as a, b, c, d.",
                                        },
                                        "label": {
                                            "type": "string",
                                            "description": "User-facing option text.",
                                        },
                                    },
                                },
                            },
                            "answer_key": {
                                "type": "object",
                                "description": "Scoring metadata for the question type.",
                                "properties": {
                                    "correct_option_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "expected_concepts": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "required_concept_count": {
                                        "type": "integer",
                                        "minimum": 1,
                                        "maximum": 5,
                                    },
                                    "forbidden_concepts": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "scoring": {
                                        "type": "string",
                                        "description": "Scoring mode such as single_best, partial_credit, or concept_coverage.",
                                    },
                                },
                            },
                            "explanation": {
                                "type": "string",
                                "description": "Short explanation of the intended answer.",
                            },
                            "correct_answer_rationale": {
                                "type": "string",
                                "description": "Why the correct answer is best.",
                            },
                            "option_rationales": {
                                "type": "array",
                                "description": "One rationale entry per option. Mark the correct option with is_correct=true.",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "required": ["option_id", "is_correct", "rationale"],
                                    "properties": {
                                        "option_id": {"type": "string"},
                                        "is_correct": {"type": "boolean"},
                                        "rationale": {"type": "string"},
                                    },
                                },
                            },
                            "helper": {
                                "type": "string",
                                "description": "Optional concise hint shown under the question.",
                            },
                        },
                    },
                }
            },
        }

    @classmethod
    def _build_stage_prompt(
        cls,
        *,
        role_graph,
        blueprints: list[dict[str, Any]],
        stage: int,
        gap_profile=None,
    ) -> str:
        stage_label = "calibration" if stage == 1 else "targeted follow-up"
        stage_focus = (
            "Across the 5 questions, progress from fundamentals to applied debugging and finish with tradeoff reasoning."
            if stage == 1
            else "Across the 5 questions, focus on deeper diagnosis, evidence-backed tradeoffs, and failure analysis."
        )
        gap_lines = ""
        if gap_profile is not None:
            gap_lines = (
                f"High priority gaps: {', '.join(gap_profile.high_priority_gaps)}.\n"
                f"Uncertain areas: {', '.join(gap_profile.uncertain_areas)}.\n"
            )

        return (
            f"Generate 5 {stage_label} questions for {role_graph.role_label}.\n"
            'Return exactly 5 question objects in a top-level JSON field named "questions".\n'
            "Keep the same target order shown below.\n"
            f"{stage_focus}\n"
            "Every stem MUST begin with a concrete scenario: a system, a failure, a code review finding, or a requirement conflict.\n"
            "Generate scenario-based questions, not generic philosophy questions.\n"
            "Vary question framing across the batch. No two questions may test the same concept from the same angle.\n"
            "Do not repeat stage-one wording or reuse the same stem template across questions.\n"
            "Each distractor must be something a junior developer might plausibly choose, but it must still be wrong.\n"
            "Avoid obvious joke or sabotage answers.\n"
            "For REST questions, include real semantics such as PUT vs PATCH or POST plus idempotency keys when relevant.\n"
            "For database questions, reference evidence such as execution plans, indexes, cardinality, and join strategy when relevant.\n"
            "For observability questions, prefer logs, metrics, traces, and failure boundaries over generic advice.\n"
            "For requirements questions, translate vague requests into measurable acceptance criteria or SLO-like targets.\n"
            'Use only "single_choice", "multi_select", or "open_ended" for "question_type".\n'
            'Each object must include: "subskill_key", "competency", "learning_objective", "scenario_context", '
            '"stem", "question_type", "difficulty", "estimated_seconds", "options", "answer_key", '
            '"explanation", "correct_answer_rationale", and "option_rationales".\n'
            'For "single_choice": write 4 parallel options and make exactly one best answer exist.\n'
            'For "multi_select": the stem must explicitly say "Select all that apply.", write 5 options, and include 2 or 3 correct answers.\n'
            'For "open_ended": options must be [], and answer_key must include expected_concepts plus required_concept_count.\n'
            "Do not ask generic self-rating questions.\n"
            "Do not use these banned low-signal patterns:\n"
            '- "Which option is the strongest engineering choice for X?"\n'
            '- "Choose the option that preserves correctness, clarity, and maintainability."\n'
            '- distractors like "Disable logging" or "Change an unrelated part of the system first."\n'
            f"{gap_lines}"
            f"{STAGE_QUESTION_FEW_SHOT_EXAMPLES}\n"
            f"Blueprints:\n{json.dumps(blueprints, ensure_ascii=True)}"
        )

    @classmethod
    def _build_stage_one_prompt(cls, role_graph, targets, *, blueprints=None) -> str:
        blueprints = blueprints or _build_stage_blueprints(role_graph, targets, stage=1)
        return cls._build_stage_prompt(
            role_graph=role_graph,
            blueprints=blueprints,
            stage=1,
        )

    @classmethod
    def _build_stage_two_prompt(cls, role_graph, targets, gap_profile, *, blueprints=None) -> str:
        blueprints = blueprints or _build_stage_blueprints(
            role_graph,
            targets,
            stage=2,
            gap_profile=gap_profile,
        )
        return cls._build_stage_prompt(
            role_graph=role_graph,
            blueprints=blueprints,
            stage=2,
            gap_profile=gap_profile,
        )

    @staticmethod
    def _question_requires_option_repair(raw_question: Any) -> bool:
        return bool(
            isinstance(raw_question, dict)
            and isinstance(raw_question.get("validation_flags"), list)
            and raw_question.get("validation_flags")
        )

    @classmethod
    def _payload_requires_option_repair(cls, raw_questions: Any) -> bool:
        if not isinstance(raw_questions, list):
            return False
        return any(cls._question_requires_option_repair(question) for question in raw_questions)

    @classmethod
    def _build_option_repair_prompt(cls, role_graph, raw_questions, *, stage: int) -> str:
        repair_targets = []
        for question in raw_questions:
            if not isinstance(question, dict):
                continue
            repair_targets.append(
                {
                    "id": question.get("id"),
                    "subskill_key": question.get("subskill_key"),
                    "scenario_context": question.get("scenario_context"),
                    "question_text": question.get("question_text") or question.get("question"),
                    "helper": question.get("helper"),
                    "category": question.get("category"),
                    "competency": question.get("competency"),
                    "learning_objective": question.get("learning_objective"),
                    "difficulty": question.get("difficulty"),
                    "estimated_seconds": question.get("estimated_seconds"),
                    "question_type": question.get("question_type"),
                    "interaction_mode": question.get("interaction_mode"),
                    "options": question.get("options"),
                    "answer_key": question.get("answer_key"),
                    "explanation": question.get("explanation"),
                    "correct_answer_rationale": question.get("correct_answer_rationale"),
                    "option_rationales": question.get("option_rationales"),
                    "validation_flags": question.get("validation_flags"),
                }
            )

        return (
            f"Repair the malformed stage {stage} assessment items for a {role_graph.role_label} assessment.\n"
            'Return a top-level JSON object with a "questions" array only.\n'
            "Preserve ids and subskill keys, but rewrite scenario_context, stems, options, answer_key, explanation, and rationale fields as needed.\n"
            'Use only "single_choice", "multi_select", or "open_ended" for "question_type".\n'
            'If a question is "single_choice", make exactly one best answer exist.\n'
            'If a question is "multi_select", the stem must explicitly say "Select all that apply." and include 2 or 3 correct answers.\n'
            'If a question is "open_ended", remove options and include answer_key.expected_concepts.\n'
            "Fix duplicate stems, repeated option patterns, weak distractors, generic engineering-judgment phrasing, fallback_slot_filled placeholders, default stems, or stem/format mismatches called out in validation_flags.\n"
            "Every repaired closed question must start with a concrete scenario, use plausible but flawed distractors, and include correct_answer_rationale plus option_rationales.\n"
            "Do not use self-assessment language or capability-scale options.\n"
            f"Questions to repair:\n{json.dumps(repair_targets, ensure_ascii=True)}"
        )

    @classmethod
    def _raise_if_question_contract_invalid(cls, questions, *, stage: int) -> None:
        invalid_questions = [
            {
                "id": question.get("id"),
                "subskill_key": question.get("subskill_key"),
                "validation_flags": question.get("validation_flags"),
            }
            for question in questions
            if isinstance(question, dict) and cls._question_requires_option_repair(question)
        ]
        if invalid_questions:
            raise AIServiceError(
                f"Stage {stage} question payload failed contract validation after repair",
                details={
                    "reason": "invalid_stage_question_contract",
                    "stage": stage,
                    "invalid_questions": invalid_questions,
                },
            )

    @classmethod
    def _build_contract_safe_question(
        cls,
        *,
        stage: int,
        index: int,
        question_id: str,
        subskill,
        role_key: str,
        role_label: str,
        defaults: dict[str, Any],
    ) -> dict[str, Any]:
        question_type = str(defaults.get("question_type") or "single_choice")
        template = _contract_safe_stage_template(
            stage=stage,
            subskill=subskill,
            role_key=role_key,
            role_label=role_label,
            question_type=question_type,
        )
        question = {
            "id": question_id or f"s{stage}_q{index}",
            "stage": stage,
            "subskill_key": subskill.key,
            "dimension_key": subskill.dimension,
            "scenario_context": template.get("scenario_context", ""),
            "question_text": template["question_text"],
            "question": template["question_text"],
            "question_type": question_type,
            "type": template["type"],
            "interaction_mode": template["interaction_mode"],
            "options": template["options"],
            "difficulty": int(defaults.get("difficulty") or max(1, min(5, subskill.target_proficiency))),
            "estimated_seconds": int(defaults.get("estimated_seconds") or 45),
            "category": subskill.label,
            "competency": subskill.label,
            "learning_objective": template["learning_objective"],
            "answer_key": template["answer_key"],
            "explanation": template["explanation"],
            "correct_answer_rationale": template.get("correct_answer_rationale", ""),
            "option_rationales": template.get("option_rationales", []),
            "validation_flags": [],
            "helper": template["helper"],
        }
        validation_flags = build_stage_validation_flags(question)
        if validation_flags:
            raise AIServiceError(
                "Contract-safe fallback question failed validation",
                details={
                    "reason": "fallback_question_invalid",
                    "stage": stage,
                    "subskill_key": subskill.key,
                    "validation_flags": validation_flags,
                },
            )
        return question

    @classmethod
    def _replace_invalid_questions_with_safe_fallbacks(
        cls,
        questions,
        *,
        stage: int,
        role_graph,
        targets,
        allowed_targets: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        target_lookup = {target.key: target for target in targets}
        replaced_questions: list[dict[str, Any]] = []
        invalid_questions: list[dict[str, Any]] = []

        for index, question in enumerate(questions, start=1):
            validation_flags = (
                question.get("validation_flags")
                if isinstance(question, dict) and isinstance(question.get("validation_flags"), list)
                else []
            )
            if not validation_flags:
                replaced_questions.append(question)
                continue

            subskill_key = str(question.get("subskill_key") or "").strip()
            target = target_lookup.get(subskill_key)
            defaults = allowed_targets.get(subskill_key, {})
            if target is None:
                raise AIServiceError(
                    "Invalid question could not be mapped to a stage target",
                    details={
                        "reason": "invalid_stage_target_mapping",
                        "stage": stage,
                        "subskill_key": subskill_key,
                    },
                )

            replaced_questions.append(
                cls._build_contract_safe_question(
                    stage=stage,
                    index=index,
                    question_id=str(question.get("id") or f"s{stage}_q{index}"),
                    subskill=target,
                    role_key=role_graph.role_key,
                    role_label=role_graph.role_label,
                    defaults=defaults,
                )
            )
            invalid_questions.append(
                {
                    "id": question.get("id"),
                    "subskill_key": subskill_key,
                    "validation_flags": validation_flags,
                }
            )

        return replaced_questions, invalid_questions

    @classmethod
    def _repair_stage_question_options(
        cls,
        role_graph,
        raw_questions,
        *,
        stage: int,
        response_json_schema: dict[str, Any],
    ):
        response = cls._get_repair_client().generate_structured(
            prompt=cls._build_option_repair_prompt(role_graph, raw_questions, stage=stage),
            system=OPTION_REPAIR_SYSTEM_PROMPT,
            required_keys=("questions",),
            response_json_schema=response_json_schema,
        )
        return response.payload.get("questions")

    @classmethod
    def _build_evaluation_prompt(cls, role_graph, merged_evidence) -> str:
        serialized = [
            {
                "subskill_key": evidence.subskill_key,
                "dimension_key": evidence.dimension_key,
                "observed_level": evidence.observed_level,
                "target_level": evidence.target_level,
                "gap": evidence.gap,
                "confidence": evidence.confidence,
            }
            for evidence in merged_evidence
        ]
        return (
            f"Summarize this staged assessment evidence for {role_graph.role_label}.\n"
            f"Evidence: {serialized}\n"
            "Return compact JSON only."
        )

    @classmethod
    def _deterministic_questions(
        cls,
        role_graph,
        targets,
        *,
        stage: int,
        gap_profile=None,
    ) -> list[dict[str, Any]]:
        allowed_targets = _target_map(
            role_graph,
            targets,
            stage=stage,
            gap_profile=gap_profile,
        )
        return [
            cls._build_contract_safe_question(
                stage=stage,
                index=index,
                question_id=f"s{stage}_q{index}",
                subskill=target,
                role_key=role_graph.role_key,
                role_label=role_graph.role_label,
                defaults=allowed_targets[target.key],
            )
            for index, target in enumerate(targets, start=1)
        ]

    @classmethod
    def _stage_one_cache_key(cls, role_key: str, graph_version: str) -> str:
        return (
            f"assessment:stage1:{cls.stage_question_prompt_version}:"
            f"{role_key}:{graph_version}"
        )

    @classmethod
    def generate_stage_one(
        cls,
        role_key: str,
        role_graph,
    ) -> tuple[list[dict[str, Any]], AIInvocationMetadata]:
        cache_key = cls._stage_one_cache_key(role_key, role_graph.version)
        cached = cache.get(cache_key)
        if cached:
            if isinstance(cached, dict) and isinstance(cached.get("metadata"), AIInvocationMetadata):
                cached_metadata = cached["metadata"]
                return cached["questions"], build_ai_metadata(
                    source="cache",
                    processing_time_ms=0,
                    model=cached_metadata.model,
                    provider="django-cache",
                    version=cached_metadata.version,
                    fallback_used=cached_metadata.fallback_used,
                    error_code=cached_metadata.error_code,
                )
            return cached, build_ai_metadata(
                source="cache",
                processing_time_ms=0,
                model=None,
                provider="django-cache",
                version=role_graph.version,
            )

        targets = StageAllocator.allocate_stage_one(role_graph)
        blueprints = _build_stage_blueprints(role_graph, targets, stage=1)
        allowed_targets = _target_map(role_graph, targets, stage=1)
        response_json_schema = cls._build_stage_question_response_json_schema(blueprints)
        started_at = monotonic()

        try:
            response = cls._get_stage_question_client().generate_structured(
                prompt=cls._build_stage_one_prompt(role_graph, targets, blueprints=blueprints),
                system=QUESTION_SYSTEM_PROMPT,
                required_keys=("questions",),
                response_json_schema=response_json_schema,
            )
            raw_questions = response.payload.get("questions")
            questions = sanitize_stage_question_payload(
                raw_questions,
                stage=1,
                allowed_targets=allowed_targets,
            )
            if cls._payload_requires_option_repair(questions):
                repaired_questions = cls._repair_stage_question_options(
                    role_graph,
                    questions,
                    stage=1,
                    response_json_schema=response_json_schema,
                )
                questions = sanitize_stage_question_payload(
                    repaired_questions,
                    stage=1,
                    allowed_targets=allowed_targets,
                )
            questions, invalid_questions = cls._replace_invalid_questions_with_safe_fallbacks(
                questions,
                stage=1,
                role_graph=role_graph,
                targets=targets,
                allowed_targets=allowed_targets,
            )
            cls._raise_if_question_contract_invalid(questions, stage=1)
            if invalid_questions:
                logger.warning(
                    "Stage one generation used deterministic replacements for invalid questions: %s",
                    invalid_questions,
                )
                metadata = build_ai_metadata(
                    source="llm",
                    processing_time_ms=response.metadata.processing_time_ms,
                    model=response.metadata.model,
                    provider=response.metadata.provider,
                    version=role_graph.version,
                    trace_id=response.metadata.trace_id,
                    fallback_used=True,
                    error_code="invalid_stage_question_contract",
                )
            else:
                metadata = response.metadata
        except Exception as error:
            logger.warning(
                "Stage one generation fell back to deterministic questions: %s",
                error,
            )
            questions = cls._deterministic_questions(role_graph, targets, stage=1)
            metadata = build_ai_metadata(
                source="fallback",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=None,
                provider=AI_PROVIDER,
                version=role_graph.version,
                fallback_used=True,
                error_code=type(error).__name__,
            )

        if not metadata.fallback_used:
            cache.set(
                cache_key,
                {"questions": questions, "metadata": metadata},
                timeout=cls.stage_one_cache_ttl_seconds,
            )
        return questions, metadata

    @classmethod
    def build_gap_profile(cls, assessment: Assessment, role_graph):
        evidence = AnswerScorer.score_stage(
            role_graph,
            assessment.stage_one_questions or [],
            assessment.stage_one_responses or [],
        )
        return GapProfileBuilder.build(role_graph, evidence)

    @classmethod
    def generate_stage_two(
        cls,
        gap_profile,
        role_graph,
    ) -> tuple[list[dict[str, Any]], AIInvocationMetadata]:
        targets = Stage2Allocator.allocate_stage_two(role_graph, gap_profile)
        blueprints = _build_stage_blueprints(
            role_graph,
            targets,
            stage=2,
            gap_profile=gap_profile,
        )
        allowed_targets = _target_map(role_graph, targets, stage=2, gap_profile=gap_profile)
        response_json_schema = cls._build_stage_question_response_json_schema(blueprints)
        started_at = monotonic()

        try:
            response = cls._get_stage_question_client().generate_structured(
                prompt=cls._build_stage_two_prompt(
                    role_graph,
                    targets,
                    gap_profile,
                    blueprints=blueprints,
                ),
                system=QUESTION_SYSTEM_PROMPT,
                required_keys=("questions",),
                response_json_schema=response_json_schema,
            )
            raw_questions = response.payload.get("questions")
            questions = sanitize_stage_question_payload(
                raw_questions,
                stage=2,
                allowed_targets=allowed_targets,
            )
            if cls._payload_requires_option_repair(questions):
                repaired_questions = cls._repair_stage_question_options(
                    role_graph,
                    questions,
                    stage=2,
                    response_json_schema=response_json_schema,
                )
                questions = sanitize_stage_question_payload(
                    repaired_questions,
                    stage=2,
                    allowed_targets=allowed_targets,
                )
            questions, invalid_questions = cls._replace_invalid_questions_with_safe_fallbacks(
                questions,
                stage=2,
                role_graph=role_graph,
                targets=targets,
                allowed_targets=allowed_targets,
            )
            cls._raise_if_question_contract_invalid(questions, stage=2)
            if invalid_questions:
                logger.warning(
                    "Stage two generation used deterministic replacements for invalid questions: %s",
                    invalid_questions,
                )
                metadata = build_ai_metadata(
                    source="llm",
                    processing_time_ms=response.metadata.processing_time_ms,
                    model=response.metadata.model,
                    provider=response.metadata.provider,
                    version=role_graph.version,
                    trace_id=response.metadata.trace_id,
                    fallback_used=True,
                    error_code="invalid_stage_question_contract",
                )
            else:
                metadata = response.metadata
        except Exception as error:
            logger.warning(
                "Stage two generation fell back to deterministic questions: %s",
                error,
            )
            questions = cls._deterministic_questions(
                role_graph,
                targets,
                stage=2,
                gap_profile=gap_profile,
            )
            metadata = build_ai_metadata(
                source="fallback",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=None,
                provider=AI_PROVIDER,
                version=role_graph.version,
                fallback_used=True,
                error_code=type(error).__name__,
            )

        return questions, metadata

    @classmethod
    def _summarize_dimension_scores(cls, merged_evidence):
        grouped: dict[str, list[float]] = {}
        for evidence in merged_evidence:
            normalized = (evidence.observed_level / max(evidence.target_level, 1)) * 100
            grouped.setdefault(evidence.dimension_key, []).append(min(100.0, round(normalized, 2)))
        return {
            dimension_key: round(mean(scores), 2)
            for dimension_key, scores in grouped.items()
        }

    @classmethod
    def _derive_strengths_and_gaps(cls, role_graph, merged_evidence):
        subskill_lookup = {
            subskill.key: subskill.label
            for dimension in role_graph.dimensions
            for subskill in dimension.subskills
        }
        ordered = sorted(merged_evidence, key=lambda item: (item.gap, -item.confidence))
        strengths = [
            subskill_lookup[item.subskill_key]
            for item in sorted(merged_evidence, key=lambda item: (item.gap, -item.confidence))[:3]
            if item.gap <= 1.0
        ]
        gaps = [
            subskill_lookup[item.subskill_key]
            for item in sorted(merged_evidence, key=lambda item: (item.gap, item.confidence), reverse=True)[:3]
            if item.gap > 0
        ]
        return strengths or [role_graph.dimensions[0].label], gaps or [ordered[-1].dimension_key]

    @classmethod
    def _recommended_learning_paths(cls, role_graph, merged_evidence):
        subskill_lookup = {
            subskill.key: subskill.label
            for dimension in role_graph.dimensions
            for subskill in dimension.subskills
        }
        ordered = sorted(merged_evidence, key=lambda item: (item.gap, item.confidence), reverse=True)
        return [
            {
                "skill": subskill_lookup[item.subskill_key],
                "priority": "high" if index == 0 else "medium",
                "resources": [],
            }
            for index, item in enumerate(ordered[:3])
        ]

    @classmethod
    def _build_roadmap_signal(cls, role_graph, merged_evidence, metadata) -> RoadmapSignal:
        prerequisite_links = {
            subskill.key: subskill.prerequisites
            for dimension in role_graph.dimensions
            for subskill in dimension.subskills
            if subskill.key in {item.subskill_key for item in merged_evidence}
        }
        confidence_score = round(mean([item.confidence for item in merged_evidence]), 2) if merged_evidence else 0.0
        evidence_strength = "strong"
        if confidence_score < 0.8:
            evidence_strength = "moderate"
        if confidence_score < 0.65:
            evidence_strength = "weak"
        priority_order = [item.subskill_key for item in merged_evidence if item.gap > 0]
        if not priority_order:
            priority_order = [item.subskill_key for item in merged_evidence[:3]]

        return RoadmapSignal(
            role=role_graph.role_key,
            target_level="job-ready",
            subskill_gaps=merged_evidence,
            confidence_score=confidence_score,
            evidence_strength=evidence_strength,
            priority_order=priority_order,
            prerequisite_links=prerequisite_links,
            generation_metadata={
                "assessment_version": "staged-v1",
                "fallback_used": metadata.fallback_used,
                "trace_id": metadata.trace_id,
                "model": metadata.model,
                "provider": metadata.provider,
                "version": metadata.version,
            },
        )

    @classmethod
    def _deterministic_staged_analysis(
        cls,
        role_graph,
        merged_evidence,
        metadata: AIInvocationMetadata,
    ) -> AssessmentAnalysisResult:
        dimension_scores = cls._summarize_dimension_scores(merged_evidence)
        overall_score = round(mean(dimension_scores.values()), 2) if dimension_scores else 0.0
        strengths, gaps = cls._derive_strengths_and_gaps(role_graph, merged_evidence)
        return AssessmentAnalysisResult(
            overall_score=Decimal(str(overall_score)),
            skill_scores=dimension_scores,
            strengths=strengths,
            areas_for_improvement=gaps,
            recommended_careers=BaselineAssessmentAnalyzer.staged_role_recommendations(role_graph),
            recommended_learning_paths=cls._recommended_learning_paths(role_graph, merged_evidence),
            ai_insights=(
                f"Your staged assessment for {role_graph.role_label} shows the strongest momentum in "
                f"{strengths[0].lower()} and the biggest next step around {gaps[0].lower()}."
            ),
            ai_confidence_score=Decimal(str(round((metadata.fallback_used and 72 or 82), 2))),
            metadata=metadata,
        )

    @classmethod
    def evaluate_staged_assessment(cls, assessment: Assessment) -> StagedAssessmentEvaluation:
        role_graph = load_role_graph(resolve_role_key(assessment.target_career))
        stage_one_evidence = AnswerScorer.score_stage(
            role_graph,
            assessment.stage_one_questions or [],
            assessment.stage_one_responses or [],
        )
        stage_two_evidence = AnswerScorer.score_stage(
            role_graph,
            assessment.stage_two_questions or [],
            assessment.stage_two_responses or [],
        )
        merged_evidence = merge_evidence(role_graph, stage_one_evidence, stage_two_evidence)
        started_at = monotonic()
        prompt_tokens = 0
        completion_tokens = 0

        try:
            response = cls._get_evaluation_client().generate_structured(
                prompt=cls._build_evaluation_prompt(role_graph, merged_evidence),
                system=EVALUATION_SYSTEM_PROMPT,
                required_keys=(
                    "overall_score",
                    "strengths",
                    "areas_for_improvement",
                    "recommended_careers",
                    "recommended_learning_paths",
                    "ai_insights",
                    "ai_confidence_score",
                ),
            )
            repaired = sanitize_evaluation_payload(
                response.payload,
                fallback_strengths=[],
                fallback_gaps=[],
            )
            metadata = response.metadata
            prompt_tokens = response.prompt_tokens
            completion_tokens = response.completion_tokens
            deterministic = cls._deterministic_staged_analysis(role_graph, merged_evidence, metadata)
            analysis = AssessmentAnalysisResult(
                overall_score=Decimal(str(round(repaired["overall_score"], 2))),
                skill_scores=deterministic.skill_scores,
                strengths=repaired["strengths"],
                areas_for_improvement=repaired["areas_for_improvement"],
                recommended_careers=repaired["recommended_careers"] or deterministic.recommended_careers,
                recommended_learning_paths=repaired["recommended_learning_paths"] or deterministic.recommended_learning_paths,
                ai_insights=repaired["ai_insights"],
                ai_confidence_score=Decimal(str(round(repaired["ai_confidence_score"], 2))),
                metadata=metadata,
            )
        except Exception as error:
            logger.warning(
                "Final staged evaluation fell back to deterministic analysis: %s",
                error,
            )
            metadata = build_ai_metadata(
                source="fallback",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=None,
                provider=AI_PROVIDER,
                version=role_graph.version,
                fallback_used=True,
                error_code=type(error).__name__,
            )
            analysis = cls._deterministic_staged_analysis(role_graph, merged_evidence, metadata)

        roadmap_signal = cls._build_roadmap_signal(role_graph, merged_evidence, analysis.metadata)
        return StagedAssessmentEvaluation(
            analysis=analysis,
            roadmap_signal=roadmap_signal,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    @classmethod
    def generate_questions(cls, assessment: Assessment) -> tuple[list[dict[str, Any]], GemmaResponse | None]:
        role_graph = load_role_graph(resolve_role_key(assessment.target_career))
        questions, metadata = cls.generate_stage_one(role_graph.role_key, role_graph)
        return questions, GemmaResponse(
            text="",
            payload={"questions": questions},
            metadata=metadata,
            prompt_tokens=0,
            completion_tokens=0,
        )

    @classmethod
    def evaluate_assessment(cls, assessment: Assessment) -> AssessmentAnalysisResult:
        payload = AssessmentAnalysisInput(
            assessment_id=str(assessment.id),
            assessment_type=assessment.assessment_type,
            target_career=assessment.target_career,
            responses=assessment.responses or [],
            questions=assessment.questions or [],
        )
        return BaselineAssessmentAnalyzer.analyze(payload)
