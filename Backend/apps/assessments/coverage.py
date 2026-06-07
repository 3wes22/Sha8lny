from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from apps.assessments.role_graph import CoreDimension, RoleGraph

logger = logging.getLogger(__name__)


class CoverageError(ValueError):
    """Raised when assessment coverage minimums are not met across stages."""


@dataclass
class CoverageTracker:
    """
    Tracks dimension coverage for the full multi-stage assessment.

    min_questions_per_stage on each dimension is interpreted as the minimum number
    of questions that must touch that dimension across all stages combined.
    """

    role_graph: RoleGraph
    required_dimensions: list[str]
    counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.required_dimensions:
            self.required_dimensions = [
                dimension.key for dimension in self.role_graph.dimensions
            ]
        for dimension_key in self.required_dimensions:
            self.counts.setdefault(dimension_key, 0)

    @classmethod
    def from_role_graph(cls, role_graph: RoleGraph) -> CoverageTracker:
        return cls(
            role_graph=role_graph,
            required_dimensions=[dimension.key for dimension in role_graph.dimensions],
        )

    @classmethod
    def from_blueprints(
        cls,
        role_graph: RoleGraph,
        blueprints: list[dict[str, Any]],
    ) -> CoverageTracker:
        """Legacy helper — prefer from_role_graph for assessment-wide tracking."""
        return cls.from_role_graph(role_graph)

    def seed_from_questions(self, questions: list[dict[str, Any]]) -> None:
        for question in questions:
            self.record(question)

    def _dimension(self, dimension_key: str) -> CoreDimension | None:
        for dimension in self.role_graph.dimensions:
            if dimension.key == dimension_key:
                return dimension
        return None

    def record(self, question: dict[str, Any]) -> None:
        dimension_key = str(
            question.get("dimension_key")
            or question.get("skill_area")
            or ""
        ).strip()
        if dimension_key:
            self.counts[dimension_key] = self.counts.get(dimension_key, 0) + 1

    def get_dimension_count(self, dimension_key: str) -> int:
        return self.counts.get(dimension_key, 0)

    def get_next_target_dimension(self) -> str | None:
        worst_key = None
        worst_gap = 0
        for dimension_key in self.required_dimensions:
            dimension = self._dimension(dimension_key)
            minimum = dimension.min_questions_per_stage if dimension else 1
            gap = minimum - self.counts.get(dimension_key, 0)
            if gap > worst_gap:
                worst_gap = gap
                worst_key = dimension_key
        return worst_key if worst_gap > 0 else None

    def get_uncovered_dimensions(self) -> list[str]:
        uncovered: list[str] = []
        for dimension_key in self.required_dimensions:
            dimension = self._dimension(dimension_key)
            minimum = dimension.min_questions_per_stage if dimension else 1
            if self.counts.get(dimension_key, 0) < minimum:
                uncovered.append(dimension_key)
        return uncovered

    def assert_complete(self) -> None:
        uncovered = self.get_uncovered_dimensions()
        if uncovered:
            report = self.generate_coverage_report()
            logger.error("Coverage incomplete: %s", report)
            raise CoverageError(
                f"Assessment coverage incomplete for dimensions: {', '.join(uncovered)}. "
                f"Report: {report}"
            )

    def assert_assessment_complete(
        self,
        stage_one_questions: list[dict[str, Any]],
        stage_two_questions: list[dict[str, Any]],
    ) -> None:
        combined = CoverageTracker.from_role_graph(self.role_graph)
        combined.seed_from_questions(stage_one_questions)
        combined.seed_from_questions(stage_two_questions)
        combined.assert_complete()

    def generate_coverage_report(self) -> dict[str, Any]:
        report: dict[str, Any] = {"dimensions": {}, "uncovered": self.get_uncovered_dimensions()}
        for dimension in self.role_graph.dimensions:
            minimum = dimension.min_questions_per_stage
            generated = self.counts.get(dimension.key, 0)
            report["dimensions"][dimension.key] = {
                "generated": generated,
                "min_questions_per_stage": minimum,
                "assessment_weight": dimension.assessment_weight or dimension.weight,
                "status": "ok" if generated >= minimum else "under",
            }
        return report
