from __future__ import annotations

from dataclasses import dataclass
from math import isclose
import re


class RoleGraphValidationError(ValueError):
    """Raised when role-graph data is structurally invalid."""


SUPPORTED_ROLES = [
    "backend",
    "frontend",
    "data_science",
    "fullstack",
    "devops",
    "android",
    "machine_learning_engineer",
    "ui_ux_designer",
]


ROLE_ALIAS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bui\s*/\s*ux designer\b"), "ui_ux_designer"),
    (re.compile(r"\bui[\s-]?ux designer\b"), "ui_ux_designer"),
    (re.compile(r"\bux designer\b"), "ui_ux_designer"),
    (re.compile(r"\bmachine learning engineer\b"), "machine_learning_engineer"),
    (re.compile(r"\bml engineer\b"), "machine_learning_engineer"),
    (re.compile(r"\bandroid developer\b"), "android"),
    (re.compile(r"\bandroid engineer\b"), "android"),
    (re.compile(r"\bandroid\b"), "android"),
    (re.compile(r"\bmobile developer\b"), "android"),
    (re.compile(r"\bmobile engineer\b"), "android"),
    (re.compile(r"\bmobile app developer\b"), "android"),
    (re.compile(r"\bmobile\b"), "android"),
    (re.compile(r"\bios developer\b"), "android"),
    (re.compile(r"\bios engineer\b"), "android"),
    (re.compile(r"\bios\b"), "android"),
    (re.compile(r"\bback[- ]?end\b"), "backend"),
    (re.compile(r"\bapi\b"), "backend"),
    (re.compile(r"\bserver\b"), "backend"),
    (re.compile(r"\bfront[- ]?end\b"), "frontend"),
    (re.compile(r"\breact\b"), "frontend"),
    (re.compile(r"\bdata science\b"), "data_science"),
    (re.compile(r"\bdata scientist\b"), "data_science"),
    (re.compile(r"\bmachine learning\b"), "data_science"),
    (re.compile(r"\bml\b"), "data_science"),
    (re.compile(r"\bfull[- ]?stack\b"), "fullstack"),
    (re.compile(r"\bsoftware engineer\b"), "fullstack"),
    (re.compile(r"\bdevops\b"), "devops"),
    (re.compile(r"\bsre\b"), "devops"),
    (re.compile(r"\bcloud\b"), "devops"),
    (re.compile(r"\bplatform\b"), "devops"),
    (re.compile(r"\bui\b"), "frontend"),
)


@dataclass(frozen=True)
class SubSkill:
    key: str
    label: str
    dimension: str
    target_proficiency: int
    prerequisites: list[str]
    frame: str | None = None


@dataclass(frozen=True)
class CoreDimension:
    key: str
    label: str
    weight: float
    subskills: list[SubSkill]
    assessment_weight: float | None = None
    min_questions_per_stage: int = 1
    origin: str | None = None


@dataclass(frozen=True)
class RoleGraph:
    role_key: str
    role_label: str
    dimensions: list[CoreDimension]
    version: str


def resolve_role_key(target_career: str) -> str:
    """Map user-facing career labels to the supported role keys."""
    normalized = (target_career or "").strip().lower()
    for pattern, role_key in ROLE_ALIAS_PATTERNS:
        if pattern.search(normalized):
            return role_key
    return "fullstack"


def _validate_graph(graph: RoleGraph) -> RoleGraph:
    if graph.role_key not in SUPPORTED_ROLES:
        raise RoleGraphValidationError(f"Unsupported role key: {graph.role_key}")
    if not graph.role_label:
        raise RoleGraphValidationError("Role graph is missing role_label")
    if not graph.version:
        raise RoleGraphValidationError(f"Role graph {graph.role_key} is missing version")
    max_dimensions = 30 if graph.role_key == "fullstack" else 15
    if not 3 <= len(graph.dimensions) <= max_dimensions:
        raise RoleGraphValidationError(
            f"Role graph {graph.role_key} must define 3-{max_dimensions} dimensions"
        )

    dimension_keys: set[str] = set()
    subskill_keys: set[str] = set()
    total_weight = 0.0

    for dimension in graph.dimensions:
        if dimension.key in dimension_keys:
            raise RoleGraphValidationError(
                f"Role graph {graph.role_key} has duplicate dimension key {dimension.key}"
            )
        dimension_keys.add(dimension.key)
        total_weight += float(dimension.weight)

        if not 2 <= len(dimension.subskills) <= 10:
            raise RoleGraphValidationError(
                f"Dimension {dimension.key} in {graph.role_key} must define 2-10 subskills"
            )

        for subskill in dimension.subskills:
            if subskill.dimension != dimension.key:
                raise RoleGraphValidationError(
                    f"Subskill {subskill.key} dimension {subskill.dimension} "
                    f"does not match parent {dimension.key}"
                )
            if subskill.key in subskill_keys:
                raise RoleGraphValidationError(
                    f"Role graph {graph.role_key} has duplicate subskill key {subskill.key}"
                )
            if not 1 <= subskill.target_proficiency <= 5:
                raise RoleGraphValidationError(
                    f"Subskill {subskill.key} has invalid target proficiency"
                )
            subskill_keys.add(subskill.key)

    if not isclose(total_weight, 1.0, rel_tol=0.0, abs_tol=1e-6):
        raise RoleGraphValidationError(
            f"Role graph {graph.role_key} weights must sum to 1.0, got {total_weight}"
        )

    assessment_weights = [
        float(dimension.assessment_weight)
        for dimension in graph.dimensions
        if dimension.assessment_weight is not None
    ]
    if assessment_weights and len(assessment_weights) == len(graph.dimensions):
        assessment_total = sum(assessment_weights)
        if not isclose(assessment_total, 1.0, rel_tol=0.0, abs_tol=1e-6):
            raise RoleGraphValidationError(
                f"Role graph {graph.role_key} assessment_weight values must sum to 1.0, "
                f"got {assessment_total}"
            )

    for dimension in graph.dimensions:
        if dimension.min_questions_per_stage < 1:
            raise RoleGraphValidationError(
                f"Dimension {dimension.key} in {graph.role_key} must have "
                f"min_questions_per_stage >= 1"
            )
        for subskill in dimension.subskills:
            missing_prerequisites = [
                prerequisite
                for prerequisite in subskill.prerequisites
                if prerequisite not in subskill_keys
            ]
            if missing_prerequisites:
                raise RoleGraphValidationError(
                    f"Subskill {subskill.key} has unknown prerequisites: "
                    f"{', '.join(missing_prerequisites)}"
                )

    return graph


def _validate_supported_role_mapping(role_graphs: dict[str, RoleGraph]) -> None:
    missing_roles = [role_key for role_key in SUPPORTED_ROLES if role_key not in role_graphs]
    if missing_roles:
        raise RoleGraphValidationError(
            f"Missing supported role graph(s): {', '.join(missing_roles)}"
        )


def load_role_graph(role_key: str) -> RoleGraph:
    from apps.assessments.role_graph_data import ROLE_GRAPHS

    _validate_supported_role_mapping(ROLE_GRAPHS)
    if role_key not in ROLE_GRAPHS:
        raise RoleGraphValidationError(f"Missing role graph for {role_key}")
    graph = ROLE_GRAPHS[role_key]
    if graph.role_key != role_key:
        raise RoleGraphValidationError(
            f"Role graph mapping key {role_key} does not match graph role_key {graph.role_key}"
        )
    return _validate_graph(graph)
