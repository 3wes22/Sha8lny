"""Unit tests for skill profile → job matching rules."""

from apps.jobs.skill_matching import skills_from_assessment_strengths


def test_assessment_gaps_are_not_match_skills():
    signal = {
        "subskill_gaps": [
            {
                "subskill_key": "django_core",
                "gap": 3.0,
                "observed_level": 1.0,
                "target_level": 4,
            },
            {
                "subskill_key": "python_basics",
                "gap": 0.5,
                "observed_level": 3.5,
                "target_level": 4,
            },
        ],
        "priority_order": ["django_core", "api_design"],
    }
    strengths = skills_from_assessment_strengths(signal)
    assert "Python" in strengths
    assert "Django" not in strengths
