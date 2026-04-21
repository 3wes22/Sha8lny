from dataclasses import replace

import pytest

from apps.assessments.role_graph import (
    SUPPORTED_ROLES,
    RoleGraphValidationError,
    load_role_graph,
    resolve_role_key,
)
from apps.assessments.role_graph_data import ROLE_GRAPHS
from apps.assessments.services import BaselineAssessmentAnalyzer


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
            assert len(dimension.subskills) == 4
            for subskill in dimension.subskills:
                assert subskill.dimension == dimension.key
                assert 1 <= subskill.target_proficiency <= 5
                subskill_keys.append(subskill.key)

        assert len(subskill_keys) == 16
        assert len(subskill_keys) == len(set(subskill_keys))


@pytest.mark.parametrize(
    ("target_career", "expected_role_key"),
    [
        ("Backend Developer", "backend"),
        ("Frontend Engineer", "frontend"),
        ("Data Scientist", "data_science"),
        ("Full Stack Developer", "fullstack"),
        ("DevOps Engineer", "devops"),
        ("Android Developer", "android"),
        ("Mobile Developer", "android"),
        ("iOS Developer", "android"),
        ("Machine Learning Engineer", "machine_learning_engineer"),
        ("Machine Learning", "data_science"),
        ("ML", "data_science"),
        ("UI/UX Designer", "ui_ux_designer"),
        ("UI Engineer", "frontend"),
        ("Software Engineer", "fullstack"),
    ],
)
def test_resolve_role_key_maps_supported_aliases(target_career, expected_role_key):
    assert resolve_role_key(target_career) == expected_role_key


def test_deterministic_role_aliases_branch_on_resolved_role_keys():
    ml_engineer_aliases = BaselineAssessmentAnalyzer._career_aliases("Machine Learning Engineer")
    generic_ml_aliases = BaselineAssessmentAnalyzer._career_aliases("Machine Learning")

    assert ml_engineer_aliases[1]["title"] == "Data Scientist"
    assert generic_ml_aliases[1]["title"] == "Machine Learning Engineer"


def test_deterministic_learning_paths_support_new_first_class_roles():
    uiux_paths = BaselineAssessmentAnalyzer._learning_paths("UI/UX Designer")
    android_paths = BaselineAssessmentAnalyzer._learning_paths("Mobile Developer")

    assert uiux_paths[0]["skill"] == "User research and problem framing"
    assert android_paths[0]["skill"] == "Kotlin and Android app architecture"


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
    monkeypatch.delitem(ROLE_GRAPHS, "android")

    with pytest.raises(RoleGraphValidationError, match="Missing supported role graph"):
        load_role_graph("backend")
