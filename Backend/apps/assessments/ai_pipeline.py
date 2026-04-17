"""
Staged assessment AI helpers, deterministic fallbacks, and legacy compatibility.
"""

from __future__ import annotations

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
from apps.core.ai_validation import sanitize_evaluation_payload, sanitize_stage_question_payload
from apps.core.gemma_client import GemmaClient, GemmaResponse


QUESTION_SYSTEM_PROMPT = """You generate concise staged assessment questions.
Return strict JSON with a top-level "questions" array only."""

EVALUATION_SYSTEM_PROMPT = """You summarize staged assessment evidence for a career platform.
Return strict JSON only with overall_score, strengths, areas_for_improvement,
recommended_careers, recommended_learning_paths, ai_insights, and ai_confidence_score."""


@dataclass(frozen=True)
class StagedAssessmentEvaluation:
    analysis: AssessmentAnalysisResult
    roadmap_signal: RoadmapSignal
    prompt_tokens: int
    completion_tokens: int


def _choice_options(subskill_label: str) -> list[dict[str, Any]]:
    return [
        {
            "value": "low",
            "label": f"Need help with {subskill_label}",
            "score": 1,
        },
        {
            "value": "mid",
            "label": f"Can apply {subskill_label} independently in straightforward work",
            "score": 3,
        },
        {
            "value": "high",
            "label": f"Can make tradeoffs and lead on {subskill_label}",
            "score": 5,
        },
    ]


def _target_map(role_graph, targets):
    return {
        target.key: {
            "dimension_key": target.dimension,
            "category": target.label,
        }
        for target in targets
    }


def _normalize_question(
    *,
    stage: int,
    index: int,
    subskill,
    role_label: str,
    targeted: bool = False,
) -> dict[str, Any]:
    prompt_prefix = "Probe more deeply" if targeted else "How comfortable are you"
    question_text = (
        f"{prompt_prefix} with {subskill.label.lower()} for {role_label.lower()} work?"
    )
    return {
        "id": f"s{stage}_q{index}",
        "stage": stage,
        "subskill_key": subskill.key,
        "dimension_key": subskill.dimension,
        "question_text": question_text,
        "question": question_text,
        "question_type": "multiple_choice",
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": _choice_options(subskill.label),
        "difficulty": min(5, max(1, subskill.target_proficiency)),
        "estimated_seconds": 45,
        "category": subskill.label,
        "helper": "",
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

    @classmethod
    def _get_client(cls) -> GemmaClient:
        return cls.client_class()

    @classmethod
    def _build_stage_one_prompt(cls, role_graph, targets) -> str:
        target_lines = "\n".join(
            f"- {target.key}: {target.label} ({target.dimension})"
            for target in targets
        )
        return (
            f"Generate 5 calibration questions for {role_graph.role_label}.\n"
            f"Return one question for each target below.\n{target_lines}\n"
            "Every question must be concise and evaluative."
        )

    @classmethod
    def _build_stage_two_prompt(cls, role_graph, targets, gap_profile) -> str:
        target_lines = "\n".join(
            f"- {target.key}: {target.label} ({target.dimension})"
            for target in targets
        )
        return (
            f"Generate 5 targeted follow-up questions for {role_graph.role_label}.\n"
            f"High priority gaps: {', '.join(gap_profile.high_priority_gaps)}.\n"
            f"Uncertain areas: {', '.join(gap_profile.uncertain_areas)}.\n"
            f"Targets:\n{target_lines}"
        )

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
    def _deterministic_questions(cls, role_graph, targets, *, stage: int) -> list[dict[str, Any]]:
        return [
            _normalize_question(
                stage=stage,
                index=index,
                subskill=target,
                role_label=role_graph.role_label,
                targeted=(stage == 2),
            )
            for index, target in enumerate(targets, start=1)
        ]

    @classmethod
    def _stage_one_cache_key(cls, role_key: str, graph_version: str) -> str:
        return f"assessment:stage1:{role_key}:{graph_version}"

    @classmethod
    def generate_stage_one(
        cls,
        role_key: str,
        role_graph,
    ) -> tuple[list[dict[str, Any]], AIInvocationMetadata]:
        cache_key = cls._stage_one_cache_key(role_key, role_graph.version)
        cached = cache.get(cache_key)
        if cached:
            return cached, build_ai_metadata(
                source="cache",
                processing_time_ms=0,
                model=None,
                provider="django-cache",
                version=role_graph.version,
            )

        targets = StageAllocator.allocate_stage_one(role_graph)
        allowed_targets = _target_map(role_graph, targets)
        started_at = monotonic()

        try:
            response = cls._get_client().generate_structured(
                prompt=cls._build_stage_one_prompt(role_graph, targets),
                system=QUESTION_SYSTEM_PROMPT,
                required_keys=("questions",),
            )
            questions = sanitize_stage_question_payload(
                response.payload.get("questions"),
                stage=1,
                allowed_targets=allowed_targets,
            )
            metadata = response.metadata
        except Exception as error:
            questions = cls._deterministic_questions(role_graph, targets, stage=1)
            metadata = build_ai_metadata(
                source="fallback",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=None,
                provider="sha8alny",
                version=role_graph.version,
                fallback_used=True,
                error_code=type(error).__name__,
            )

        cache.set(cache_key, questions, timeout=cls.stage_one_cache_ttl_seconds)
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
        allowed_targets = _target_map(role_graph, targets)
        started_at = monotonic()

        try:
            response = cls._get_client().generate_structured(
                prompt=cls._build_stage_two_prompt(role_graph, targets, gap_profile),
                system=QUESTION_SYSTEM_PROMPT,
                required_keys=("questions",),
            )
            questions = sanitize_stage_question_payload(
                response.payload.get("questions"),
                stage=2,
                allowed_targets=allowed_targets,
            )
            metadata = response.metadata
        except Exception as error:
            questions = cls._deterministic_questions(role_graph, targets, stage=2)
            metadata = build_ai_metadata(
                source="fallback",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=None,
                provider="sha8alny",
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
            recommended_careers=BaselineAssessmentAnalyzer._career_aliases(role_graph.role_label),
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
            response = cls._get_client().generate_structured(
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
            metadata = build_ai_metadata(
                source="fallback",
                processing_time_ms=int((monotonic() - started_at) * 1000),
                model=None,
                provider="sha8alny",
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
