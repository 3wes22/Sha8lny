"""
Staged assessment AI helpers, deterministic fallbacks, and legacy compatibility.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
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
    merge_evidence,
)
from apps.assessments.chains.post_process import enrich_questions
from apps.assessments.chains.router import build_default_router
from apps.assessments.fallback_scenarios import get_curated_fallback_scenario
from apps.assessments.models import Assessment
from apps.assessments.role_graph import load_role_graph, resolve_role_key
from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION
from apps.assessments.scenario_retriever import ScenarioRetriever
from apps.assessments.services import BaselineAssessmentAnalyzer
from apps.core.ai_contracts import (
    AIInvocationMetadata,
    AssessmentAnalysisInput,
    AssessmentAnalysisResult,
    RoadmapSignal,
)
from apps.core.ai_logging import build_ai_metadata
from apps.core import ai_settings as core_ai_settings
from apps.core.ai_settings import (
    AI_PROVIDER,
    ASSESSMENT_SCENARIO_RAG_ENABLED,
    LLM_TIMEOUT_SECONDS,
    SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT,
)
from apps.core.ai_validation import (
    build_stage_validation_flags,
    build_stage_choice_options,
    sanitize_evaluation_payload,
    sanitize_stage_question_payload,
)
from apps.core.exceptions import AIServiceError


@dataclass(frozen=True)
class RetrievedExamplesResult:
    """Captures both the prompt block and provenance from RAG retrieval."""

    prompt_block: str
    doc_ids: list[str] = field(default_factory=list)
    doc_count: int = 0
    rag_enabled: bool = False


from apps.core.gemma_client import GemmaClient, GemmaResponse


logger = logging.getLogger(__name__)


QUESTION_SYSTEM_PROMPT = """You generate concise, role-specific staged assessment questions for the {career} track at {difficulty} difficulty.
The candidate already reports these skills: {existing_skills} — avoid trivial questions on mastered areas; probe depth and edges instead.
Return STRICT JSON only with a top-level "questions" array. Each question: id, subskill_key (from provided blueprint), question_text, question_type (single_choice|multi_select|open_ended), options (for choice types), answer_key, difficulty (1-5).
Never include explanations outside the JSON. Distractors must be plausible and mutually exclusive; no "all of the above"."""
OPTION_REPAIR_SYSTEM_PROMPT = """You repair malformed staged assessment items.
Return strict JSON with a top-level "questions" array only."""

EVALUATION_SYSTEM_PROMPT = """You summarize staged assessment evidence for an Egyptian-market career platform. Be specific and encouraging, not generic.
Return STRICT JSON only: overall_score (0-100), strengths[], areas_for_improvement[], recommended_careers[{title,match_score,reasoning}], recommended_learning_paths[{skill,priority,resources}], ai_insights (2-4 sentences), ai_confidence_score (0-100).
Base every claim on the provided evidence; do not invent skills the candidate did not demonstrate."""

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
    from apps.assessments.chains.enums import QuestionType
    from apps.assessments.role_graph_taxonomy import is_debugging_dimension

    question_types = _stage_question_type_sequence(stage=stage, count=len(targets))
    debugging_slots_seen = 0
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
        chain_question_type = None
        if is_debugging_dimension(target.dimension):
            if debugging_slots_seen == 0:
                chain_question_type = QuestionType.DEBUGGING_SINGLE.value
                question_type = "single_choice"
            else:
                chain_question_type = QuestionType.DEBUGGING_MULTI.value
                question_type = "multi_select"
            debugging_slots_seen += 1
        intent = {
            "single_choice": "narrow one decision so exactly one best answer exists",
            "multi_select": "ask for multiple concrete practices that are all required",
            "open_ended": "ask for a concise written explanation of strategy and tradeoffs",
        }[question_type]
        blueprint: dict[str, Any] = {
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
        if chain_question_type:
            blueprint["chain_question_type"] = chain_question_type
        blueprints.append(blueprint)
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


def _is_debugging_subskill(subskill) -> bool:
    return getattr(subskill, "frame", None) == "debugging"


def _apply_chain_helper_to_template(
    template: dict[str, Any],
    *,
    subskill,
    question_type: str,
) -> dict[str, Any]:
    """Set helper from the type-scoped chain — never from shared fallback bleed."""
    router = build_default_router()
    probe = {"question_type": question_type, "subskill_key": subskill.key}
    router.assign_helper(probe, subskill=subskill)
    helper = probe.get("helper")
    if helper:
        template["helper"] = helper
    else:
        template.pop("helper", None)
    return template


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
        return _apply_chain_helper_to_template(
            dict(curated),
            subskill=subskill,
            question_type=question_type,
        )

    skill = subskill.label.lower()
    role = role_label.lower()
    debugging = _is_debugging_subskill(subskill)

    if question_type == "multi_select":
        scenario_context = (
            f"A {role} team is reviewing a {skill} change before it reaches production."
        )
        stem = "Which practices are strongest for this scenario? Select all that apply."
        template = {
            "scenario_context": scenario_context,
            "stem": stem,
            "question_text": f"{scenario_context}\n\n{stem}",
            "type": "multiple_choice",
            "interaction_mode": "multi_select",
            "options": [
                {"id": "a", "value": "a", "label": "Define acceptance criteria and validate inputs before merging."},
                {"id": "b", "value": "b", "label": "Add automated tests that cover the changed behavior and edge cases."},
                {"id": "c", "value": "c", "label": "Defer testing until after release to preserve velocity."},
                {"id": "d", "value": "d", "label": "Document the change and add monitoring for the affected path."},
                {"id": "e", "value": "e", "label": "Rewrite unrelated modules in the same pull request."},
            ],
            "answer_key": {
                "correct_option_ids": ["a", "b", "d"],
                "scoring": "partial_credit",
            },
            "learning_objective": f"Identify the strongest practices for {skill}.",
            "explanation": "Strong answers combine validation, testing, and observability.",
            "correct_answer_rationale": "The best combination reduces risk while keeping delivery predictable.",
            "option_rationales": [
                {"option_id": "a", "is_correct": True, "rationale": "Clear criteria prevent ambiguous requirements."},
                {"option_id": "b", "is_correct": True, "rationale": "Tests catch regressions in the changed behavior."},
                {"option_id": "c", "is_correct": False, "rationale": "Deferring tests increases production risk."},
                {"option_id": "d", "is_correct": True, "rationale": "Monitoring supports safe rollout."},
                {"option_id": "e", "is_correct": False, "rationale": "Unrelated rewrites increase review cost and risk."},
            ],
        }
        return _apply_chain_helper_to_template(template, subskill=subskill, question_type=question_type)

    if question_type == "open_ended":
        scenario_context = (
            f"A {role} team must improve how they handle {skill} in an upcoming release."
        )
        stem = (
            "What would you implement, what would you explicitly not do, and what tradeoffs "
            "would you accept?"
        )
        template = {
            "scenario_context": scenario_context,
            "stem": stem,
            "question_text": f"{scenario_context}\n\n{stem}",
            "type": "text",
            "interaction_mode": "text",
            "options": [],
            "answer_key": {
                "expected_concepts": ["approach", "tradeoffs", "constraints"],
                "required_concept_count": 2,
                "forbidden_concepts": ["no plan"],
                "scoring": "concept_coverage",
            },
            "learning_objective": f"Explain strategy and tradeoffs for {skill}.",
            "explanation": "A strong answer names concrete techniques and explicit tradeoffs.",
            "correct_answer_rationale": "The answer should balance delivery speed, quality, and maintainability.",
            "option_rationales": [],
        }
        return _apply_chain_helper_to_template(template, subskill=subskill, question_type=question_type)

    if debugging and stage >= 2:
        scenario_context = (
            f"A production issue tied to {skill} has mixed signals and the {role} team must choose "
            "the next diagnostic step carefully."
        )
        stem = "What should the team do first to isolate the issue without widening impact?"
        options = [
            {"id": "a", "value": "a", "label": "Collect logs, traces, and reproduction steps for the failing path first."},
            {"id": "b", "value": "b", "label": "Change timeout and retry settings globally before confirming the failing component."},
            {"id": "c", "value": "c", "label": "Refactor adjacent modules before confirming the root cause."},
            {"id": "d", "value": "d", "label": "Wait for more incidents before investigating."},
        ]
        learning_objective = f"Choose the strongest first diagnostic step for {skill}."
        correct_option_ids = ["a"]
        correct_answer_rationale = "Evidence-first diagnosis limits blast radius."
        option_rationales = [
            {"option_id": "a", "is_correct": True, "rationale": "Targeted evidence narrows the failure boundary."},
            {"option_id": "b", "is_correct": False, "rationale": "Global changes can mask the real failure."},
            {"option_id": "c", "is_correct": False, "rationale": "Refactors before diagnosis increase scope."},
            {"option_id": "d", "is_correct": False, "rationale": "Waiting delays resolution without new evidence."},
        ]
    elif stage == 1:
        scenario_context = (
            f"A {role} team is preparing a {skill} change that could affect users and release timing."
        )
        stem = "Which option best balances quality and delivery for this change?"
        options = [
            {"id": "a", "value": "a", "label": "Clarify requirements and ship the smallest change that meets them with tests."},
            {"id": "b", "value": "b", "label": "Bundle several adjacent refactors into the same release to deploy once."},
            {"id": "c", "value": "c", "label": "Ship without tests and fix issues reported in production."},
            {"id": "d", "value": "d", "label": "Postpone the change until a full rewrite is possible."},
        ]
        learning_objective = f"Choose the strongest engineering approach for {skill}."
        correct_option_ids = ["a"]
        correct_answer_rationale = "A narrow, tested change reduces risk while preserving delivery."
        option_rationales = [
            {"option_id": "a", "is_correct": True, "rationale": "Clear scope and tests support safe delivery."},
            {"option_id": "b", "is_correct": False, "rationale": "Bundling unrelated work increases review and release risk."},
            {"option_id": "c", "is_correct": False, "rationale": "Production-driven QA is costly and unreliable."},
            {"option_id": "d", "is_correct": False, "rationale": "Indefinite deferral does not address the requirement."},
        ]
    else:
        scenario_context = (
            f"A {role} team is deciding how to improve {skill} in the next sprint."
        )
        stem = "Which option is the strongest next step for this team?"
        options = [
            {"id": "a", "value": "a", "label": "Define a measurable goal, implement incrementally, and validate with tests."},
            {"id": "b", "value": "b", "label": "Rewrite the entire module before shipping any improvement."},
            {"id": "c", "value": "c", "label": "Copy a pattern from another team without adapting it to context."},
            {"id": "d", "value": "d", "label": "Skip documentation because the code is self-explanatory."},
        ]
        learning_objective = f"Choose the strongest next step for {skill}."
        correct_option_ids = ["a"]
        correct_answer_rationale = "Incremental, measurable improvement is the most reliable path."
        option_rationales = [
            {"option_id": "a", "is_correct": True, "rationale": "Measurable goals and tests keep progress verifiable."},
            {"option_id": "b", "is_correct": False, "rationale": "Big-bang rewrites delay value and increase risk."},
            {"option_id": "c", "is_correct": False, "rationale": "Context-free copying often misses constraints."},
            {"option_id": "d", "is_correct": False, "rationale": "Undocumented systems are harder to maintain."},
        ]

    template = {
        "scenario_context": scenario_context,
        "stem": stem,
        "question_text": f"{scenario_context}\n\n{stem}",
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": options,
        "answer_key": {
            "correct_option_ids": correct_option_ids,
            "scoring": "single_best",
        },
        "learning_objective": learning_objective,
        "explanation": "The strongest answer matches the scenario constraints and team goals.",
        "correct_answer_rationale": correct_answer_rationale,
        "option_rationales": option_rationales,
    }
    return _apply_chain_helper_to_template(template, subskill=subskill, question_type=question_type)


def _target_map(role_graph, targets, *, stage: int, gap_profile=None):
    blueprints = _build_stage_blueprints(role_graph, targets, stage=stage, gap_profile=gap_profile)
    return {
        target.key: {
            **(
                lambda template: {
                    "type": template["type"],
                    "interaction_mode": template["interaction_mode"],
                    "options": template["options"],
                    "helper": template.get("helper", ""),
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
    stage_question_prompt_version = "v8"
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
        # Gemini rejects deeply constrained schemas for this prompt with
        # "too many states for serving". Keep the provider schema shallow and
        # enforce the full contract in sanitize/validation immediately after.
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["questions"],
            "properties": {
                "questions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {
                            "subskill_key": {"type": "string"},
                            "question_type": {"type": "string"},
                            "question_text": {"type": "string"},
                            "scenario_context": {"type": "string"},
                            "stem": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "label": {"type": "string"},
                                    },
                                },
                            },
                            "answer_key": {
                                "type": "object",
                                "properties": {
                                    "correct_option_ids": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "expected_concepts": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "required_concept_count": {"type": "integer"},
                                    "scoring": {"type": "string"},
                                },
                            },
                        },
                    },
                }
            },
        }

    _last_retrieval_info: dict[str, Any] = {}

    @classmethod
    def _subskill_lookup(cls, role_graph) -> dict[str, Any]:
        return {
            subskill.key: subskill
            for dimension in role_graph.dimensions
            for subskill in dimension.subskills
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
        retrieved_result = cls._build_retrieved_examples_block(
            role_graph=role_graph, blueprints=blueprints, stage=stage,
        )
        gap_lines = ""
        if gap_profile is not None:
            gap_lines = (
                f"High priority gaps: {', '.join(gap_profile.high_priority_gaps)}.\n"
                f"Uncertain areas: {', '.join(gap_profile.uncertain_areas)}.\n"
            )

        router = build_default_router()
        lookup = cls._subskill_lookup(role_graph)
        slots = [{**bp, "stage": stage} for bp in blueprints]

        if core_ai_settings.ASSESSMENT_GENERATION_MODE == "per_question":
            typed_block = "\n\n".join(
                router.chain_for_slot(
                    slot,
                    subskill=lookup.get(str(slot.get("subskill_key") or "")),
                ).build_prompt(slot)
                for slot in slots
            )
            prompt = (
                f"Generate {len(slots)} questions for {role_graph.role_label} (stage {stage}).\n"
                f"{typed_block}\n"
                f"{gap_lines}"
                f"{STAGE_QUESTION_FEW_SHOT_EXAMPLES}\n"
                f"{retrieved_result.prompt_block}"
            )
        else:
            typed_block = router.build_batch_prompt(
                role_label=role_graph.role_label,
                stage=stage,
                slots=slots,
                subskill_lookup=lookup,
            )
            stage_label = "calibration" if stage == 1 else "targeted follow-up"
            prompt = (
                f"Generate 5 {stage_label} questions for {role_graph.role_label}.\n"
                f"{typed_block}\n"
                f"{gap_lines}"
                'Return exactly 5 question objects in a top-level JSON field named "questions".\n'
                "Every stem MUST begin with a concrete scenario.\n"
                "Do not embed sub-instructions in stems.\n"
                'Each object must include: "subskill_key", "competency", "learning_objective", '
                '"scenario_context", "stem", "question_type", "difficulty", "estimated_seconds", '
                '"options", "answer_key", "explanation", "correct_answer_rationale", '
                'and "option_rationales".\n'
                'For closed questions, "answer_key.correct_option_ids" MUST contain option ids from "options".\n'
                "Do not ask generic self-rating questions.\n"
                "Each distractor must be something a junior developer might plausibly choose, "
                "but it must still be wrong.\n"
                "Do not use these banned low-signal patterns:\n"
                '- "Which option is the strongest engineering choice for X?"\n'
                f"{STAGE_QUESTION_FEW_SHOT_EXAMPLES}\n"
                f"{retrieved_result.prompt_block}"
            )
        if stage == 2:
            prompt += "Do not repeat stage-one wording or reuse the same stem template across questions.\n"
        if stage == 1:
            prompt += (
                "Across the 5 questions, progress from fundamentals to applied work and "
                "finish with tradeoff reasoning.\n"
            )
        else:
            prompt += (
                "Across the 5 questions, focus on deeper diagnosis, evidence-backed tradeoffs, "
                "and failure analysis.\n"
            )
        cls._last_retrieval_info = {
            "retrieved_doc_ids": retrieved_result.doc_ids,
            "retrieved_count": retrieved_result.doc_count,
            "rag_enabled": retrieved_result.rag_enabled,
        }
        return prompt

    @classmethod
    def _build_retrieved_examples_block(
        cls,
        *,
        role_graph,
        blueprints: list[dict[str, Any]],
        stage: int,
    ) -> RetrievedExamplesResult:
        """Return a ``RetrievedExamplesResult`` with the prompt block and provenance.

        Returns an empty-block result when the feature flag is off, when the
        corpus has nothing for the blueprint mix, or when retrieval fails.
        That empty-block contract is what keeps the prompt byte-identical
        to the pre-feature behaviour when ``ASSESSMENT_SCENARIO_RAG_ENABLED``
        is ``False``.
        """
        _empty = RetrievedExamplesResult(
            prompt_block="", doc_ids=[], doc_count=0,
            rag_enabled=ASSESSMENT_SCENARIO_RAG_ENABLED,
        )
        if not ASSESSMENT_SCENARIO_RAG_ENABLED:
            return _empty

        collected: list[dict[str, Any]] = []
        seen_doc_ids: set[str] = set()
        ordered_doc_ids: list[str] = []
        role_key = getattr(role_graph, "role_key", None) or ""

        for blueprint in blueprints or []:
            if len(collected) >= SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT:
                break
            scenarios = ScenarioRetriever.retrieve_for_blueprint(
                role_key=role_key,
                blueprint=blueprint,
                stage=stage,
            )
            for scenario in scenarios:
                doc_id = str(scenario.get("doc_id") or "")
                if doc_id and doc_id in seen_doc_ids:
                    continue
                if doc_id:
                    seen_doc_ids.add(doc_id)
                    ordered_doc_ids.append(doc_id)
                collected.append(scenario)
                if len(collected) >= SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT:
                    break

        if not collected:
            return RetrievedExamplesResult(
                prompt_block="", doc_ids=ordered_doc_ids, doc_count=0,
                rag_enabled=True,
            )

        slim_examples = [
            {
                "subskill_key": scenario.get("subskill_key"),
                "competency": scenario.get("competency"),
                "question_type": scenario.get("question_type"),
                "scenario_context": scenario.get("scenario_context"),
                "stem": scenario.get("stem"),
                "options": scenario.get("options") or [],
                "answer_key": scenario.get("answer_key") or {},
                "explanation": scenario.get("explanation"),
            }
            for scenario in collected
        ]
        prompt_block = (
            "Additional on-topic examples retrieved from the curated corpus "
            "(use as stylistic and scenario references, do not copy verbatim):\n"
            f"{json.dumps(slim_examples, ensure_ascii=True)}\n"
        )
        return RetrievedExamplesResult(
            prompt_block=prompt_block,
            doc_ids=ordered_doc_ids,
            doc_count=len(collected),
            rag_enabled=True,
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
    def _finalize_stage_questions(
        cls,
        questions: list[dict[str, Any]],
        *,
        role_graph,
        blueprints: list[dict[str, Any]],
        client: GemmaClient | None = None,
    ) -> list[dict[str, Any]]:
        if not questions:
            return questions
        llm_passes = cls._gemini_configured()
        return enrich_questions(
            questions,
            role_graph=role_graph,
            blueprints=blueprints,
            client=client if llm_passes else None,
            run_ambiguity=llm_passes,
            run_rubric=True,
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
            "helper": template.get("helper"),
        }
        build_default_router().assign_helper(question, subskill=subskill)
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
    def _question_system_prompt(
        cls,
        role_graph,
        *,
        difficulty: int = 3,
        existing_skills: str = "none reported yet",
    ) -> str:
        return QUESTION_SYSTEM_PROMPT.format(
            career=role_graph.role_label,
            difficulty=difficulty,
            existing_skills=existing_skills,
        )

    @classmethod
    def _gemini_configured(cls) -> bool:
        return bool(str(core_ai_settings.GEMINI_API_KEY or "").strip())

    @classmethod
    def _curated_stage_questions(
        cls,
        role_graph,
        targets,
        *,
        stage: int,
        gap_profile=None,
        error_code: str = "curated_fallback",
        processing_time_ms: int = 0,
    ) -> tuple[list[dict[str, Any]], AIInvocationMetadata]:
        """Scenario-based questions with scored answer keys (no live LLM)."""
        cls._last_retrieval_info = {
            "rag_enabled": False,
            "retrieved_doc_ids": [],
            "retrieved_count": 0,
        }
        blueprints = _build_stage_blueprints(
            role_graph,
            targets,
            stage=stage,
            gap_profile=gap_profile,
        )
        questions = cls._deterministic_questions(
            role_graph,
            targets,
            stage=stage,
            gap_profile=gap_profile,
        )
        questions = cls._finalize_stage_questions(
            questions,
            role_graph=role_graph,
            blueprints=blueprints,
            client=None,
        )
        metadata = build_ai_metadata(
            source="curated_fallback",
            processing_time_ms=processing_time_ms,
            model=None,
            provider="curated",
            version=role_graph.version,
            fallback_used=True,
            error_code=error_code,
        )
        return questions, metadata

    @classmethod
    def _stage_one_cache_key(cls, role_key: str, graph_version: str) -> str:
        base_key = (
            f"assessment:stage1:{cls.stage_question_prompt_version}:"
            f"{role_key}:{graph_version}"
        )
        if ASSESSMENT_SCENARIO_RAG_ENABLED:
            return f"{base_key}:{SCENARIO_CORPUS_VERSION}"
        return base_key

    @classmethod
    def generate_stage_one(
        cls,
        role_key: str,
        role_graph,
    ) -> tuple[list[dict[str, Any]], AIInvocationMetadata, dict[str, Any]]:
        cache_key = cls._stage_one_cache_key(role_key, role_graph.version)
        cached = cache.get(cache_key)
        if cached:
            cached_retrieval = cached.get("retrieval_info", {}) if isinstance(cached, dict) else {}
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
                ), cached_retrieval
            return cached, build_ai_metadata(
                source="cache",
                processing_time_ms=0,
                model=None,
                provider="django-cache",
                version=role_graph.version,
            ), cached_retrieval

        targets = StageAllocator.allocate_stage_one(role_graph)
        gemini_configured = cls._gemini_configured()
        if not gemini_configured:
            logger.info(
                "GEMINI_API_KEY is not configured; serving curated scenario questions for stage one."
            )
            questions, metadata = cls._curated_stage_questions(
                role_graph,
                targets,
                stage=1,
                error_code="gemini_api_key_missing",
            )
            retrieval_info = dict(cls._last_retrieval_info)
            return questions, metadata, retrieval_info

        blueprints = _build_stage_blueprints(role_graph, targets, stage=1)
        allowed_targets = _target_map(role_graph, targets, stage=1)
        response_json_schema = cls._build_stage_question_response_json_schema(blueprints)
        started_at = monotonic()

        try:
            client = cls._get_stage_question_client()
            prompt = cls._build_stage_one_prompt(role_graph, targets, blueprints=blueprints)
            response = client.generate_structured(
                prompt=prompt,
                system=cls._question_system_prompt(role_graph),
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
            questions = cls._finalize_stage_questions(
                questions,
                role_graph=role_graph,
                blueprints=blueprints,
                client=client,
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
            questions, metadata = cls._curated_stage_questions(
                role_graph,
                targets,
                stage=1,
                error_code=type(error).__name__,
                processing_time_ms=int((monotonic() - started_at) * 1000),
            )

        retrieval_info = dict(cls._last_retrieval_info) if cls._last_retrieval_info else {}
        if not metadata.fallback_used:
            cache.set(
                cache_key,
                {"questions": questions, "metadata": metadata, "retrieval_info": retrieval_info},
                timeout=cls.stage_one_cache_ttl_seconds,
            )
        return questions, metadata, retrieval_info

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
        *,
        stage_one_questions: list[dict[str, Any]] | None = None,
    ) -> tuple[list[dict[str, Any]], AIInvocationMetadata, dict[str, Any]]:
        targets = Stage2Allocator.allocate_stage_two(
            role_graph,
            gap_profile,
            stage_one_questions=stage_one_questions,
        )
        blueprints = _build_stage_blueprints(
            role_graph,
            targets,
            stage=2,
            gap_profile=gap_profile,
        )
        allowed_targets = _target_map(role_graph, targets, stage=2, gap_profile=gap_profile)
        response_json_schema = cls._build_stage_question_response_json_schema(blueprints)
        started_at = monotonic()
        known_skills = ", ".join(
            str(item.subskill_key).replace("_", " ")
            for item in gap_profile.subskill_evidence
            if getattr(item, "gap", 99) <= 1
        ) or "baseline calibration complete"

        if not cls._gemini_configured():
            logger.info(
                "GEMINI_API_KEY is not configured; serving curated scenario questions for stage two."
            )
            questions, metadata = cls._curated_stage_questions(
                role_graph,
                targets,
                stage=2,
                gap_profile=gap_profile,
                error_code="gemini_api_key_missing",
            )
            retrieval_info = dict(cls._last_retrieval_info)
            return questions, metadata, retrieval_info

        try:
            response = cls._get_stage_question_client().generate_structured(
                prompt=cls._build_stage_two_prompt(
                    role_graph,
                    targets,
                    gap_profile,
                    blueprints=blueprints,
                ),
                system=cls._question_system_prompt(
                    role_graph,
                    difficulty=4,
                    existing_skills=known_skills,
                ),
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
            questions = cls._finalize_stage_questions(
                questions,
                role_graph=role_graph,
                blueprints=blueprints,
                client=cls._get_stage_question_client(),
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
            questions, metadata = cls._curated_stage_questions(
                role_graph,
                targets,
                stage=2,
                gap_profile=gap_profile,
                error_code=type(error).__name__,
                processing_time_ms=int((monotonic() - started_at) * 1000),
            )

        retrieval_info = dict(cls._last_retrieval_info) if cls._last_retrieval_info else {}
        return questions, metadata, retrieval_info

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
    def _weighted_overall(cls, role_graph, dimension_scores: dict[str, float]) -> float:
        """Roll dimension scores up to a single overall score using role weights.

        Each dimension's importance comes from its ``assessment_weight`` (an
        assessment-specific override) when present, otherwise its canonical
        ``weight`` (defined for every role and validated to sum to 1.0). Weights
        are re-normalized over the dimensions actually measured, so a partially
        covered assessment never divides by an assumed total of 1.0. Falls back
        to a flat mean only when no weights can be resolved.
        """
        if not dimension_scores:
            return 0.0
        weight_map = {
            dimension.key: (
                dimension.assessment_weight
                if dimension.assessment_weight is not None
                else dimension.weight
            )
            for dimension in role_graph.dimensions
        }
        weighted_sum = 0.0
        total_weight = 0.0
        for dimension_key, score in dimension_scores.items():
            weight = weight_map.get(dimension_key)
            if weight is None:
                continue
            weighted_sum += weight * score
            total_weight += weight
        if total_weight <= 0:
            return round(mean(dimension_scores.values()), 2)
        return round(weighted_sum / total_weight, 2)

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
        overall_score = cls._weighted_overall(role_graph, dimension_scores)
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
                # Headline score is a reproducible weighted roll-up we compute,
                # not the LLM's self-reported number.
                overall_score=deterministic.overall_score,
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
        questions, metadata, _retrieval_info = cls.generate_stage_one(role_graph.role_key, role_graph)
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
