"""Tests for LightGBM job ranker integration."""

from pathlib import Path

import numpy as np
import pytest

from apps.core.ai_bridge import ensure_ai_models_path


@pytest.fixture(scope="module")
def ranker_modules():
    ensure_ai_models_path()
    from recommendations.feature_engineering import build_feature_vector
    from recommendations.ranker import JobRanker, train_ranker_from_labeled_groups

    return build_feature_vector, JobRanker, train_ranker_from_labeled_groups


def test_feature_vector_has_five_features(ranker_modules):
    build_feature_vector, _, _ = ranker_modules
    vector = build_feature_vector(
        ["Python", "Django"],
        {
            "title": "Backend Developer",
            "description": "Python Django API",
            "requirements": "PostgreSQL",
            "required_skills": ["Python", "Django", "PostgreSQL"],
            "experience_level": "mid",
            "posted_date": "2026-05-01",
            "location_country": "Egypt",
        },
    )
    assert vector.shape == (5,)


def test_ranker_loads_or_trains(tmp_path, ranker_modules):
    build_feature_vector, JobRanker, train_ranker_from_labeled_groups = ranker_modules
    model_path = tmp_path / "job_ranker.lgb"

    jobs = [
        {
            "id": "1",
            "title": "Backend Developer",
            "description": "Python Django",
            "requirements": "",
            "required_skills": ["Python", "Django"],
            "experience_level": "mid",
            "posted_date": "2026-05-01",
            "location_country": "Egypt",
        },
        {
            "id": "2",
            "title": "Frontend Developer",
            "description": "React TypeScript",
            "requirements": "",
            "required_skills": ["React", "TypeScript"],
            "experience_level": "mid",
            "posted_date": "2026-05-02",
            "location_country": "Egypt",
        },
    ]

    rows = []
    labels = []
    groups = []
    for skills in (["Python", "Django"], ["React", "TypeScript"]):
        group_rows = []
        group_labels = []
        for job in jobs:
            overlap = len(set(skills) & set(job["required_skills"])) / len(job["required_skills"])
            group_rows.append(build_feature_vector(skills, job))
            group_labels.append(3 if overlap >= 0.5 else 0)
        rows.extend(group_rows)
        labels.extend(group_labels)
        groups.append(len(group_rows))

    train_ranker_from_labeled_groups(
        np.vstack(rows),
        np.asarray(labels, dtype=np.float32),
        groups,
        output_path=model_path,
    )

    ranker = JobRanker(model_path=model_path)
    assert ranker.is_available
    ranked = ranker.rank_jobs(["Python", "Django"], jobs, limit=2)
    assert ranked[0]["job"]["id"] == "1"
    assert ranked[0]["explanation"]["top_factors"]

