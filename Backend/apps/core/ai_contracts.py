"""
Shared AI-facing contracts and metadata helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class AIInvocationMetadata:
    """Normalized metadata returned by deterministic or model-backed engines."""

    source: str
    processing_time_ms: int
    model: Optional[str]
    provider: Optional[str] = None
    version: Optional[str] = None
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    fallback_used: bool = False
    error_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "processing_time_ms": self.processing_time_ms,
            "model": self.model,
            "provider": self.provider,
            "version": self.version,
            "trace_id": self.trace_id,
            "fallback_used": self.fallback_used,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class AssessmentAnalysisInput:
    """Stable input for assessment analyzers."""

    assessment_id: str
    assessment_type: str
    target_career: str
    responses: List[Dict[str, Any]]
    questions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class AssessmentAnalysisResult:
    """Stable output for assessment analyzers."""

    overall_score: Decimal
    skill_scores: Dict[str, Any]
    strengths: List[str]
    areas_for_improvement: List[str]
    recommended_careers: List[Dict[str, Any]]
    recommended_learning_paths: List[Dict[str, Any]]
    ai_insights: str
    ai_confidence_score: Optional[Decimal]
    metadata: AIInvocationMetadata


@dataclass(frozen=True)
class StageQuestion:
    """Single assessment question with role-graph context."""

    id: str
    stage: int
    subskill_key: str
    dimension_key: str
    question_text: str
    question_type: str
    interaction_mode: str
    options: List[Dict[str, Any]] = field(default_factory=list)
    difficulty: int = 3
    estimated_seconds: int = 45


@dataclass(frozen=True)
class SubSkillEvidence:
    """Deterministic scoring evidence for a subskill."""

    subskill_key: str
    dimension_key: str
    observed_level: float
    target_level: int
    gap: float
    confidence: float
    evidence_strength: str


@dataclass(frozen=True)
class GapProfile:
    """Intermediate gap analysis after stage one."""

    role_key: str
    subskill_evidence: List[SubSkillEvidence]
    high_priority_gaps: List[str]
    uncertain_areas: List[str]
    overall_calibration: float


@dataclass(frozen=True)
class RoadmapSignal:
    """Structured assessment output for roadmap generation."""

    role: str
    target_level: str
    subskill_gaps: List[SubSkillEvidence]
    confidence_score: float
    evidence_strength: str
    priority_order: List[str]
    prerequisite_links: Dict[str, List[str]]
    generation_metadata: Dict[str, Any]


@dataclass(frozen=True)
class RoadmapGenerationInput:
    """Stable input for roadmap generators."""

    target_career: str
    current_level: str
    target_level: str
    weekly_hours_commitment: int
    assessment_id: Optional[str] = None
    strengths: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    priority_skills: List[str] = field(default_factory=list)
    top_skills: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AdvisorRequestContext:
    """Stable input for advisor responders."""

    user_id: str
    message: str
    conversation_id: Optional[str]
    conversation_history: List[Dict[str, str]]
    user_context: Dict[str, Any]


@dataclass(frozen=True)
class AdvisorResponseContract:
    """Stable output for advisor responders."""

    response: str
    delay_seconds: float
    metadata: AIInvocationMetadata
