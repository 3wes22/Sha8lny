from dataclasses import replace

import pytest

from apps.assessments.role_graph import (
    SUPPORTED_ROLES,
    RoleGraphValidationError,
    load_role_graph,
    resolve_role_key,
)
from apps.assessments.role_graph_data import ROLE_GRAPHS


def test_supported_role_graphs_are_structurally_valid():
    for role_key in SUPPORTED_ROLES:
        graph = load_role_graph(role_key)

        assert graph.role_key == role_key
        assert graph.role_label
        assert graph.version
        assert len(graph.dimensions) == 4
        assert round(sum(dimension.weight for dimension in graph.dimensions), 4) == 1.0

        subskill_keys = []
        for dimension in graph.dimensions:
            assert dimension.key
            assert dimension.label
            assert 4 <= len(dimension.subskills) <= 5
            for subskill in dimension.subskills:
                assert subskill.dimension == dimension.key
                assert 1 <= subskill.target_proficiency <= 5
                subskill_keys.append(subskill.key)

        assert 15 <= len(subskill_keys) <= 20
        assert len(subskill_keys) == len(set(subskill_keys))


@pytest.mark.parametrize(
    ("target_career", "expected_role_key"),
    [
        ("Backend Developer", "backend"),
        ("Frontend Engineer", "frontend"),
        ("Data Scientist", "data_science"),
        ("Full Stack Developer", "fullstack"),
        ("Mobile Developer", "mobile"),
        ("DevOps Engineer", "devops"),
        ("Software Engineer", "fullstack"),
    ],
)
def test_resolve_role_key_maps_supported_aliases(target_career, expected_role_key):
    assert resolve_role_key(target_career) == expected_role_key


def test_load_role_graph_rejects_invalid_graph(monkeypatch):
    backend_graph = ROLE_GRAPHS["backend"]
    invalid_graph = replace(
        backend_graph,
        dimensions=backend_graph.dimensions[:-1],
    )
    monkeypatch.setitem(ROLE_GRAPHS, "backend", invalid_graph)

    with pytest.raises(RoleGraphValidationError):
        load_role_graph("backend")


def test_load_role_graph_accepts_curated_replacement_in_role_graph_mapping(monkeypatch):
    backend_graph = ROLE_GRAPHS["backend"]
    replacement_graph = replace(backend_graph, version="curated-v2")
    monkeypatch.setitem(ROLE_GRAPHS, "backend", replacement_graph)

    loaded_graph = load_role_graph("backend")

    assert loaded_graph.version == "curated-v2"
    assert loaded_graph.role_key == "backend"


def test_load_role_graph_rejects_missing_supported_role_keys(monkeypatch):
    monkeypatch.delitem(ROLE_GRAPHS, "mobile")

    with pytest.raises(RoleGraphValidationError, match="Missing supported role graph"):
        load_role_graph("backend")
