from __future__ import annotations

from dataclasses import dataclass
from math import isclose


class RoleGraphValidationError(ValueError):
    """Raised when role-graph data is structurally invalid."""


SUPPORTED_ROLES = [
    "backend",
    "frontend",
    "data_science",
    "fullstack",
    "mobile",
    "devops",
]


@dataclass(frozen=True)
class SubSkill:
    key: str
    label: str
    dimension: str
    target_proficiency: int
    prerequisites: list[str]


@dataclass(frozen=True)
class CoreDimension:
    key: str
    label: str
    weight: float
    subskills: list[SubSkill]


@dataclass(frozen=True)
class RoleGraph:
    role_key: str
    role_label: str
    dimensions: list[CoreDimension]
    version: str


def resolve_role_key(target_career: str) -> str:
    """Map user-facing career labels to the supported role keys."""
    normalized = (target_career or "").strip().lower()
    alias_map = {
        "backend": "backend",
        "api": "backend",
        "server": "backend",
        "frontend": "frontend",
        "front-end": "frontend",
        "ui": "frontend",
        "react": "frontend",
        "data science": "data_science",
        "data scientist": "data_science",
        "machine learning": "data_science",
        "ml": "data_science",
        "fullstack": "fullstack",
        "full stack": "fullstack",
        "full-stack": "fullstack",
        "software engineer": "fullstack",
        "mobile": "mobile",
        "flutter": "mobile",
        "android": "mobile",
        "ios": "mobile",
        "devops": "devops",
        "sre": "devops",
        "cloud": "devops",
        "platform": "devops",
    }
    for needle, role_key in alias_map.items():
        if needle in normalized:
            return role_key
    return "fullstack"


def _validate_graph(graph: RoleGraph) -> RoleGraph:
    if graph.role_key not in SUPPORTED_ROLES:
        raise RoleGraphValidationError(f"Unsupported role key: {graph.role_key}")
    if not graph.role_label:
        raise RoleGraphValidationError("Role graph is missing role_label")
    if not graph.version:
        raise RoleGraphValidationError(f"Role graph {graph.role_key} is missing version")
    if not 3 <= len(graph.dimensions) <= 5:
        raise RoleGraphValidationError(
            f"Role graph {graph.role_key} must define 3-5 dimensions"
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

        if not 3 <= len(dimension.subskills) <= 6:
            raise RoleGraphValidationError(
                f"Dimension {dimension.key} in {graph.role_key} must define 3-6 subskills"
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

    for dimension in graph.dimensions:
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


def load_role_graph(role_key: str) -> RoleGraph:
    from apps.assessments.role_graph_data import ROLE_GRAPHS

    if role_key not in ROLE_GRAPHS:
        raise RoleGraphValidationError(f"Missing role graph for {role_key}")
    return _validate_graph(ROLE_GRAPHS[role_key])
