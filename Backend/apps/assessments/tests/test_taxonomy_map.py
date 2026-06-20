"""Integrity tests for the external→curated taxonomy maps (Task 3.5).

Every mapping target must resolve to a real ``(role_key, subskill_key)`` in the
curated role graph, and the maps must carry the documented minimum coverage so
the methodology doc and the code stay in sync.
"""

from __future__ import annotations

from apps.assessments.role_graph import load_role_graph
from apps.assessments.scenario_corpus.taxonomy_map import (
    CSV_TO_ROLE_GRAPH,
    LINKEDIN_TO_ROLE_GRAPH,
)


def _subskill_keys(role_key: str) -> set[str]:
    graph = load_role_graph(role_key)
    return {
        subskill.key
        for dimension in graph.dimensions
        for subskill in dimension.subskills
    }


def _all_targets() -> list[tuple[str, str]]:
    return [*LINKEDIN_TO_ROLE_GRAPH.values(), *CSV_TO_ROLE_GRAPH.values()]


def test_every_mapping_resolves_to_a_real_role_and_subskill():
    cache: dict[str, set[str]] = {}
    for role_key, subskill_key in _all_targets():
        if role_key not in cache:
            cache[role_key] = _subskill_keys(role_key)
        assert subskill_key in cache[role_key], (
            f"taxonomy_map target ({role_key!r}, {subskill_key!r}) does not resolve "
            f"to a real subskill in the curated role graph"
        )


def test_maps_carry_at_least_fifteen_entries():
    # The methodology doc commits to >=15 declared mappings.
    assert len(LINKEDIN_TO_ROLE_GRAPH) + len(CSV_TO_ROLE_GRAPH) >= 15
