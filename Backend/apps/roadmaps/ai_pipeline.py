"""
Roadmap-specific AI personalization and deterministic fallback helpers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from apps.core.ai_contracts import AIInvocationMetadata
from apps.core.ai_logging import build_ai_metadata
from apps.core.ai_settings import OLLAMA_MODEL
from apps.core.gemma_client import GemmaClient


ROADMAP_PERSONALIZATION_PROMPT = """You personalize learning roadmaps for a career-development platform.
Return strict JSON with:
- roadmap_summary: string
- coaching_notes: string[]
- phases: array of exactly 3 phases

Each phase must include:
- title
- description
- objectives: string[]
- milestones: array of milestone objects

Each milestone must include:
- title
- description

Do not change the number of phases or milestones. Personalize wording only.
"""


@dataclass(frozen=True)
class RoadmapPersonalizationResult:
    phases: List[Dict[str, Any]]
    summary: str
    coaching_notes: List[str]
    metadata: AIInvocationMetadata
    prompt_tokens: int = 0
    completion_tokens: int = 0


def _normalize_milestones(
    raw_milestones: List[Dict[str, Any]],
    fallback_milestones: List[Dict[str, Any]],
    phase_title: str,
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, fallback in enumerate(fallback_milestones):
        raw = raw_milestones[index] if index < len(raw_milestones) and isinstance(raw_milestones[index], dict) else {}
        title = str(raw.get("title") or fallback.get("title") or "").strip()
        description = str(raw.get("description") or "").strip()
        normalized.append(
            {
                **fallback,
                "title": title or fallback["title"],
                "description": description or f"Complete {title or fallback['title']} during the {phase_title} phase.",
            }
        )
    return normalized


def _normalize_phases(raw_phases: List[Dict[str, Any]], fallback_phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for index, fallback in enumerate(fallback_phases):
        raw = raw_phases[index] if index < len(raw_phases) and isinstance(raw_phases[index], dict) else {}
        title = str(raw.get("title") or fallback.get("title") or "").strip()
        description = str(raw.get("description") or fallback.get("description") or "").strip()
        objectives = raw.get("objectives") if isinstance(raw.get("objectives"), list) else fallback.get("objectives", [])
        normalized.append(
            {
                **fallback,
                "title": title or fallback["title"],
                "description": description or fallback["description"],
                "objectives": [str(item).strip() for item in objectives if str(item).strip()] or fallback.get("objectives", []),
                "milestones": _normalize_milestones(
                    raw.get("milestones") if isinstance(raw.get("milestones"), list) else [],
                    fallback.get("milestones", []),
                    title or fallback["title"],
                ),
            }
        )
    return normalized


class RoadmapAIService:
    """Personalize deterministic roadmap blueprints with Gemma when available."""

    RUNTIME_VERSION = "roadmap-gemma-v1"
    FALLBACK_VERSION = "roadmap-fallback-v1"

    @staticmethod
    def personalize_blueprint(
        *,
        target_career: str,
        current_level: str,
        target_level: str,
        weekly_hours: int,
        strengths: List[str],
        gaps: List[str],
        priority_skills: List[str],
        top_skills: List[str],
        phases_data: List[Dict[str, Any]],
        default_summary: str,
    ) -> RoadmapPersonalizationResult:
        prompt = (
            f"Target career: {target_career}\n"
            f"Current level: {current_level}\n"
            f"Target level: {target_level}\n"
            f"Weekly hours: {weekly_hours}\n"
            f"Strengths: {strengths}\n"
            f"Gaps: {gaps}\n"
            f"Priority skills: {priority_skills}\n"
            f"Top skills: {top_skills}\n"
            f"Base phases: {phases_data}\n"
            "Personalize the roadmap copy while preserving the structure."
        )

        client = GemmaClient()
        try:
            result = client.generate_structured(
                prompt=prompt,
                system=ROADMAP_PERSONALIZATION_PROMPT,
                required_keys=("roadmap_summary", "phases"),
            )
            payload = result.payload or {}
            coaching_notes = [
                str(item).strip()
                for item in payload.get("coaching_notes", [])
                if str(item).strip()
            ][:4]
            return RoadmapPersonalizationResult(
                phases=_normalize_phases(payload.get("phases", []), phases_data),
                summary=str(payload.get("roadmap_summary") or default_summary).strip(),
                coaching_notes=coaching_notes,
                metadata=build_ai_metadata(
                    source="llm",
                    processing_time_ms=result.metadata.processing_time_ms,
                    model=result.metadata.model,
                    provider=result.metadata.provider,
                    version=RoadmapAIService.RUNTIME_VERSION,
                    trace_id=result.metadata.trace_id,
                ),
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
            )
        except Exception as error:
            return RoadmapPersonalizationResult(
                phases=_normalize_phases([], phases_data),
                summary=default_summary,
                coaching_notes=[],
                metadata=build_ai_metadata(
                    source="fallback",
                    processing_time_ms=0,
                    model=OLLAMA_MODEL,
                    provider="sha8alny",
                    version=RoadmapAIService.FALLBACK_VERSION,
                    fallback_used=True,
                    error_code=type(error).__name__,
                ),
            )
