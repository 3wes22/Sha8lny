"""
Orchestrate RAG-grounded roadmap structure assembly (C1 pipeline).

Primary path: retrieve roadmap.sh chunks → normalize → gap reorder → O*NET crosswalk.
Fallback: deterministic ``RoadmapService._build_personalized_phase_blueprint`` when
retrieval returns no chunks (``fallback_used=True`` in provenance).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from apps.assessments.models import AssessmentResult
from apps.assessments.role_graph import resolve_role_key
from apps.roadmaps.onet_mapper import RoadmapONETMapper
from apps.roadmaps.path_normalizer import NormalizedPhase, RoadmapPathNormalizer
from apps.roadmaps.path_retriever import RoadmapPathRetriever
from apps.users.models import User


ASSEMBLER_VERSION = "roadmap-assembler-v1"


# Honest licensing tier for the structure source (see DATASET_REGISTRY.md):
# roadmap.sh content is personal-use-only — a development-only fallback that must
# never be defended as the licensed corpus; our deterministic templates are
# internally authored. The frontend renders this so sourced vs. fallback
# roadmaps are never misrepresented.
STRUCTURE_LICENSE_DEV_ONLY = "dev_only"
STRUCTURE_LICENSE_INTERNAL = "internal"


@dataclass
class RoadmapProvenanceMetadata:
    structure_source: str
    retrieved_doc_ids: list[str]
    retrieved_urls: list[str]
    onet_mappings: list[dict[str, Any]]
    fallback_used: bool
    structure_license_tier: str = STRUCTURE_LICENSE_INTERNAL
    assembler_version: str = ASSEMBLER_VERSION
    phase_sources: list[dict[str, Any]] = field(default_factory=list)
    retrieval_chunk_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RoadmapAssembler:
    """Assemble assessment-aware roadmap blueprints from retrieved sources."""

    @staticmethod
    def _milestone_priority(title: str, priority_terms: list[str]) -> int:
        normalized = title.lower()
        score = 0
        for index, term in enumerate(priority_terms):
            if term.lower() in normalized:
                score += max(1, len(priority_terms) - index)
        return score

    @classmethod
    def _gap_reorder_milestones(
        cls,
        phases: list[NormalizedPhase],
        priority_skills: list[str],
        gaps: list[str],
    ) -> list[NormalizedPhase]:
        """Personalize the retrieved roadmap.sh structure to the assessment.

        Beyond reordering, this weaves explicit milestones for the top priority
        skills and gaps into the structure so the deterministic roadmap reflects
        the user's assessment even when the LLM personalization layer is
        unavailable (offline demo or exhausted quota). Priority-skill milestones
        land in the foundational phase; gap-closing milestones land in the
        intermediate phase.
        """
        priority_terms = [*(priority_skills or []), *(gaps or [])]
        if not priority_terms:
            return phases

        skill_titles = [f"Build {skill} depth" for skill in (priority_skills or [])[:2]]
        gap_titles = [f"Close the {gap} gap" for gap in (gaps or [])[:2]]

        reordered: list[NormalizedPhase] = []
        for phase in phases:
            injected: list[str] = []
            if phase.phase_number == 1:
                injected = skill_titles
            elif phase.phase_number == 2:
                injected = gap_titles

            seen: set[str] = set()
            titles: list[str] = []
            for title in [*injected, *phase.milestone_titles]:
                key = title.lower()
                if key in seen:
                    continue
                seen.add(key)
                titles.append(title)

            titles.sort(
                key=lambda title: cls._milestone_priority(title, priority_terms),
                reverse=True,
            )
            reordered.append(
                NormalizedPhase(
                    phase_number=phase.phase_number,
                    title=phase.title,
                    milestone_titles=titles,
                    estimated_hours=phase.estimated_hours,
                    source_doc_ids=phase.source_doc_ids,
                    source_urls=phase.source_urls,
                )
            )
        return reordered

    @staticmethod
    def _estimate_weeks(total_hours: int, weekly_hours: int) -> int:
        return max(2, math.ceil(total_hours / max(weekly_hours, 1)))

    @classmethod
    def _phases_to_blueprint(
        cls,
        phases: list[NormalizedPhase],
        *,
        role_key: str,
        weekly_hours: int,
        onet_mappings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        blueprint: list[dict[str, Any]] = []

        for phase in phases:
            milestone_count = max(1, len(phase.milestone_titles))
            hours_per_milestone = max(6, phase.estimated_hours // milestone_count)
            weeks = cls._estimate_weeks(phase.estimated_hours, weekly_hours)

            milestones: list[dict[str, Any]] = []
            for index, title in enumerate(phase.milestone_titles):
                milestone_type = "project" if phase.phase_number == 3 and index == len(phase.milestone_titles) - 1 else "course"
                resources: list[dict[str, str]] = []
                for url in phase.source_urls:
                    resources.append(
                        {
                            "title": "roadmap.sh learning path",
                            "url": url,
                            "type": "roadmap.sh",
                        }
                    )
                for mapping in onet_mappings:
                    if mapping.get("milestone_title") == title:
                        resources.append(mapping["resource"])

                milestones.append(
                    {
                        "title": title,
                        "type": milestone_type,
                        "hours": hours_per_milestone,
                        "skills": [title],
                        "resources": resources,
                    }
                )

            blueprint.append(
                {
                    "title": phase.title,
                    "description": (
                        f"Phase {phase.phase_number} grounded in roadmap.sh retrieval "
                        f"for {role_key.replace('_', ' ')}."
                    ),
                    "weeks": weeks,
                    "objectives": [
                        f"Complete {len(phase.milestone_titles)} milestones in {phase.title}.",
                        "Follow retrieved roadmap.sh topic ordering.",
                    ],
                    "milestones": milestones,
                    "source_urls": phase.source_urls,
                    "source_doc_ids": phase.source_doc_ids,
                }
            )
        return blueprint

    @classmethod
    def assemble(
        cls,
        *,
        user: User,
        target_career: str,
        assessment_result: AssessmentResult | None,
        current_level: str,
        weekly_hours: int,
        priority_skills: list[str],
        gaps: list[str],
        strengths: list[str],
        top_skills: list[str],
    ) -> tuple[list[dict[str, Any]], RoadmapProvenanceMetadata]:
        """
        Build phases blueprint and provenance metadata.

        Falls back to ``RoadmapService._build_personalized_phase_blueprint`` when
        retrieval returns no chunks.
        """
        from apps.roadmaps.services import RoadmapService

        role_key = resolve_role_key(target_career)
        chunks = RoadmapPathRetriever.retrieve_path_chunks(role_key, target_career)

        if not chunks:
            phases_data = RoadmapService._build_personalized_phase_blueprint(
                target_career=target_career,
                current_level=current_level,
                strengths=strengths,
                gaps=gaps,
                priority_skills=priority_skills,
                top_skills=top_skills,
                weekly_hours=weekly_hours,
            )
            provenance = RoadmapProvenanceMetadata(
                structure_source="deterministic_fallback",
                retrieved_doc_ids=[],
                retrieved_urls=[],
                onet_mappings=[],
                fallback_used=True,
                structure_license_tier=STRUCTURE_LICENSE_INTERNAL,
                retrieval_chunk_count=0,
            )
            return phases_data, provenance

        normalized = RoadmapPathNormalizer.normalize(chunks, role_key)
        normalized = cls._gap_reorder_milestones(normalized, priority_skills, gaps)

        onet_mappings: list[dict[str, Any]] = []
        for phase in normalized:
            for title in phase.milestone_titles:
                onet_mappings.extend(RoadmapONETMapper.map_milestone(title, role_key))

        phases_data = cls._phases_to_blueprint(
            normalized,
            role_key=role_key,
            weekly_hours=weekly_hours,
            onet_mappings=onet_mappings,
        )

        all_doc_ids: list[str] = []
        all_urls: list[str] = []
        phase_sources: list[dict[str, Any]] = []
        for index, phase in enumerate(normalized, start=1):
            all_doc_ids.extend(phase.source_doc_ids)
            all_urls.extend(phase.source_urls)
            phase_sources.append(
                {
                    "phase_order": index,
                    "urls": phase.source_urls,
                    "doc_ids": phase.source_doc_ids,
                }
            )

        provenance = RoadmapProvenanceMetadata(
            structure_source="roadmap.sh",
            retrieved_doc_ids=list(dict.fromkeys(all_doc_ids)),
            retrieved_urls=list(dict.fromkeys(all_urls)),
            onet_mappings=onet_mappings,
            fallback_used=False,
            structure_license_tier=STRUCTURE_LICENSE_DEV_ONLY,
            phase_sources=phase_sources,
            retrieval_chunk_count=len(chunks),
        )
        return phases_data, provenance
