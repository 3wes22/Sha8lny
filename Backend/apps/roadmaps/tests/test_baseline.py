from apps.roadmaps.baseline import apply_assessment_baseline


def _phases():
    # 5 bands, two milestones each, distinct skill keywords.
    return [
        {
            "title": "Foundations",
            "milestones": [
                {"title": "Learn HTTP basics", "skills": ["http"]},
                {"title": "Version control with Git", "skills": ["git"]},
            ],
        },
        {
            "title": "Core Skills",
            "milestones": [
                {"title": "Build a REST API", "skills": ["rest"]},
                {"title": "Relational databases and SQL", "skills": ["sql"]},
            ],
        },
        {
            "title": "Intermediate",
            "milestones": [
                {"title": "Automated testing", "skills": ["testing"]},
                {"title": "Caching fundamentals", "skills": ["caching"]},
            ],
        },
        {
            "title": "Advanced",
            "milestones": [
                {"title": "Containerization with Docker", "skills": ["docker"]},
                {"title": "Observability and tracing", "skills": ["observability"]},
            ],
        },
        {
            "title": "Job-Ready",
            "milestones": [
                {"title": "Ship a portfolio project", "skills": ["portfolio"]},
                {"title": "Targeted job search sprint", "skills": ["jobsearch"]},
            ],
        },
    ]


def _all(phase):
    return [(m["status"], m["from_assessment"]) for m in phase["milestones"]]


def test_beginner_passes_nothing():
    out = apply_assessment_baseline(_phases(), "beginner", gaps=[], mastered=[])
    for phase in out:
        for m in phase["milestones"]:
            assert m["status"] == "not_started"
            assert m["from_assessment"] is False


def test_intermediate_passes_foundations_only():
    out = apply_assessment_baseline(_phases(), "intermediate", gaps=[], mastered=[])
    assert all(s == ("completed", True) for s in _all(out[0]))  # Foundations
    assert all(s == ("not_started", False) for s in _all(out[1]))  # Core active


def test_advanced_passes_foundations_and_core():
    out = apply_assessment_baseline(_phases(), "advanced", gaps=[], mastered=[])
    assert all(s == ("completed", True) for s in _all(out[0]))
    assert all(s == ("completed", True) for s in _all(out[1]))
    assert all(s == ("not_started", False) for s in _all(out[2]))  # Intermediate active


def test_gap_in_passed_band_stays_active():
    # advanced learner but SQL is a flagged gap -> that Core milestone stays active.
    out = apply_assessment_baseline(_phases(), "advanced", gaps=["SQL"], mastered=[])
    core = {m["title"]: (m["status"], m["from_assessment"]) for m in out[1]["milestones"]}
    assert core["Relational databases and SQL"] == ("not_started", False)
    assert core["Build a REST API"] == ("completed", True)


def test_mastery_above_entry_prepasses_milestone():
    # beginner, but proven mastery of Docker -> that Advanced milestone is pre-passed.
    out = apply_assessment_baseline(_phases(), "beginner", gaps=[], mastered=["Docker"])
    adv = {m["title"]: (m["status"], m["from_assessment"]) for m in out[3]["milestones"]}
    assert adv["Containerization with Docker"] == ("completed", True)
    assert adv["Observability and tracing"] == ("not_started", False)


def test_does_not_mutate_input():
    phases = _phases()
    apply_assessment_baseline(phases, "advanced", gaps=[], mastered=[])
    assert "status" not in phases[0]["milestones"][0]
