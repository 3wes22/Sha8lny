#!/usr/bin/env python3
"""
Train the committed LightGBM job ranker from a JSON export of jobs.

Export jobs from Django (recommended):
    cd Backend && python manage.py export_jobs_for_ranker --output ../ai-models/data/job_ranker_training.json

Train:
    cd ai-models && python scripts/train_job_ranker.py

Pseudo-labels: per synthetic user profile, jobs are labeled 0–3 by overlap quartile
and a title keyword boost (backend/frontend/data) to avoid training only on overlap.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recommendations.feature_engineering import build_feature_vector  # noqa: E402
from recommendations.ranker import train_ranker_from_labeled_groups  # noqa: E402

SYNTHETIC_USERS = [
    {"skills": ["Python", "Django", "PostgreSQL", "REST API"], "level": "mid", "keyword": "backend"},
    {"skills": ["JavaScript", "React", "TypeScript", "CSS"], "level": "mid", "keyword": "frontend"},
    {"skills": ["Python", "SQL", "Pandas", "Data Analysis"], "level": "mid", "keyword": "data"},
    {"skills": ["Python", "FastAPI", "Docker", "AWS"], "level": "senior", "keyword": "backend"},
    {"skills": ["Java", "Spring", "SQL"], "level": "senior", "keyword": "java"},
    {"skills": ["Flutter", "Dart", "Firebase"], "level": "entry", "keyword": "mobile"},
    {"skills": ["Node.js", "TypeScript", "PostgreSQL"], "level": "mid", "keyword": "full"},
    {"skills": ["Python", "Machine Learning", "TensorFlow"], "level": "senior", "keyword": "machine"},
]


def _pseudo_label(overlap: float, title: str, keyword: str) -> int:
    title_lower = title.lower()
    keyword_hit = keyword.lower() in title_lower if keyword else False
    if overlap <= 0:
        return 0
    if overlap >= 0.75 and keyword_hit:
        return 3
    if overlap >= 0.5:
        return 2
    if overlap >= 0.25:
        return 1
    return 1 if keyword_hit else 0


def build_training_data(jobs: list[dict]) -> tuple[np.ndarray, np.ndarray, list[int]]:
    rows = []
    labels = []
    group_sizes = []

    for profile in SYNTHETIC_USERS:
        user_skills = profile["skills"]
        skill_set = set(user_skills)
        group_rows = []
        group_labels = []
        for job in jobs:
            required = set(job.get("required_skills") or [])
            overlap = len(skill_set & required) / len(required) if required else 0.0
            vector = build_feature_vector(
                user_skills,
                job,
                user_experience_level=profile["level"],
            )
            label = _pseudo_label(overlap, str(job.get("title") or ""), profile["keyword"])
            group_rows.append(vector)
            group_labels.append(label)
        if group_rows:
            rows.extend(group_rows)
            labels.extend(group_labels)
            group_sizes.append(len(group_rows))

    return np.vstack(rows), np.asarray(labels, dtype=np.float32), group_sizes


def main() -> None:
    parser = argparse.ArgumentParser(description="Train job LightGBM ranker")
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data" / "job_ranker_training.json",
        help="JSON list of job dicts (from Django export)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "models" / "custom" / "job_ranker.lgb",
        help="Output model path",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(
            f"Training file not found: {args.input}\n"
            "Run: python manage.py export_jobs_for_ranker"
        )

    jobs = json.loads(args.input.read_text(encoding="utf-8"))
    if len(jobs) < 10:
        raise SystemExit(f"Need at least 10 jobs for training, got {len(jobs)}")

    matrix, labels, groups = build_training_data(jobs)
    output = train_ranker_from_labeled_groups(matrix, labels, groups, output_path=args.output)
    print(f"Saved ranker to {output} ({len(jobs)} jobs, {len(groups)} user groups)")


if __name__ == "__main__":
    main()
