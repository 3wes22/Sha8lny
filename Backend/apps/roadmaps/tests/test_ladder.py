import pytest

from apps.assessments.role_graph import SUPPORTED_ROLES
from apps.roadmaps.ladder import ROLE_LADDERS, build_ladder_blueprint

CAREER_BY_ROLE = {
    "backend": "Backend Developer",
    "frontend": "Frontend Developer",
    "data_science": "Data Scientist",
    "fullstack": "Full Stack Developer",
    "devops": "DevOps Engineer",
    "android": "Android Developer",
    "machine_learning_engineer": "Machine Learning Engineer",
    "ui_ux_designer": "UI/UX Designer",
}


def test_all_supported_roles_have_authored_topics():
    for role in SUPPORTED_ROLES:
        assert role in ROLE_LADDERS, f"missing ladder for {role}"
        bands = ROLE_LADDERS[role]
        assert len(bands) == 4, f"{role} must author bands 0-3 (Job-Ready is generated)"
        for band in bands:
            assert len(band) >= 3, f"{role} band too thin: {band}"


@pytest.mark.parametrize("role", SUPPORTED_ROLES)
def test_build_blueprint_has_five_bands(role):
    phases = build_ladder_blueprint(
        target_career=CAREER_BY_ROLE[role],
        current_level="beginner",
        priority_skills=[],
        gaps=[],
        top_skills=[],
        strengths=[],
        weekly_hours=10,
    )
    assert len(phases) == 5
    for phase in phases:
        assert phase["title"]
        assert phase["weeks"] >= 1
        assert len(phase["milestones"]) >= 1
        for milestone in phase["milestones"]:
            assert milestone["title"]
            assert milestone["type"] in {"course", "project", "practice", "reading"}
            assert milestone["hours"] >= 1
    # Last band is the job-ready band and ends with a project + job-search work.
    job_band = phases[4]
    types = [m["type"] for m in job_band["milestones"]]
    assert "project" in types


def test_unknown_role_falls_back_to_generic_ladder():
    phases = build_ladder_blueprint(
        target_career="Quantum Basket Weaver",
        current_level="beginner",
        priority_skills=[], gaps=[], top_skills=[], strengths=[],
        weekly_hours=10,
    )
    assert len(phases) == 5
    assert all(len(p["milestones"]) >= 1 for p in phases)
