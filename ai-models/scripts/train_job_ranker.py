#!/usr/bin/env python3
"""
Train and evaluate the committed LightGBM job ranker from a JSON export of jobs.

Export jobs from Django (recommended):
    cd Backend && python manage.py export_jobs_for_ranker --output ../ai-models/data/job_ranker_training.json

Train + evaluate:
    cd ai-models && python scripts/train_job_ranker.py

Labeling is **weak supervision** (a.k.a. data programming, cf. Ratner et al.,
"Snorkel: Rapid Training Data Creation with Weak Supervision", VLDB 2017): instead
of human relevance judgements we apply labeling functions — per synthetic user
profile, jobs get a graded relevance 0–3 from required-skill overlap quartiles plus
a role-title keyword boost (backend/frontend/data...). These are deliberate, cheap,
noisy labels — not ground truth — so the model is reported as a *demonstrator* and
always measured against trivial baselines (see EVAL_REPORT.md).

Outputs:
  - models/custom/job_ranker.lgb       (production model, trained on ALL groups)
  - models/custom/job_ranker_eval.json (held-out metrics, machine-readable)
  - models/custom/EVAL_REPORT.md       (human-readable evaluation summary)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recommendations.feature_engineering import (  # noqa: E402
    build_feature_vector,
    embeddings_available,
    required_skill_overlap_ratio,
)
from recommendations.ranker import (  # noqa: E402
    train_and_evaluate,
    train_ranker_from_labeled_groups,
)

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
    """Weak-supervision labeling function: graded relevance 0..3 from skill overlap
    and a role-title keyword match. Noisy by design — not a human judgement."""
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
            # Use the same overlap definition as the LightGBM feature
            # (case-insensitive) so the weak label and the
            # ``required_skill_overlap_ratio`` feature can never disagree —
            # otherwise casing drift in real postings silently inverts labels.
            overlap = required_skill_overlap_ratio(
                skill_set, set(job.get("required_skills") or [])
            )
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

    # 1. Production model: trained on ALL groups.
    output = train_ranker_from_labeled_groups(matrix, labels, groups, output_path=args.output)
    print(f"Saved ranker to {output} ({len(jobs)} jobs, {len(groups)} user groups)")

    # 2. Honest evaluation on a held-out group split (throwaway model).
    evaluation = train_and_evaluate(matrix, labels, groups, seed=42)
    evaluation["n_jobs"] = len(jobs)
    try:
        # Keep committed artifacts portable — record a repo-relative path so
        # regenerating on another machine doesn't churn the diff.
        evaluation["training_input"] = str(args.input.resolve().relative_to(ROOT))
    except ValueError:
        evaluation["training_input"] = args.input.name
    evaluation["generated_on"] = date.today().isoformat()
    evaluation["embeddings_enabled"] = embeddings_available()

    eval_json_path = args.output.parent / "job_ranker_eval.json"
    eval_json_path.write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")

    report_path = args.output.parent / "EVAL_REPORT.md"
    report_path.write_text(_render_report(evaluation), encoding="utf-8")

    _print_metrics(evaluation)
    print(f"Wrote {eval_json_path}")
    print(f"Wrote {report_path}")


def _print_metrics(evaluation: dict) -> None:
    metrics = evaluation["metrics"]
    rankers = ("lightgbm", "overlap_baseline", "random_baseline")
    header = f"{'metric':<10} " + " ".join(f"{r:>17}" for r in rankers)
    print(f"\nLeave-one-group-out ranking quality ({evaluation['n_folds']} folds):")
    print(header)
    for metric_name, scores in metrics.items():
        row = f"{metric_name:<10} " + " ".join(f"{scores[r]:>17.4f}" for r in rankers)
        print(row)


def _render_report(evaluation: dict) -> str:
    metrics = evaluation["metrics"]
    rankers = ("lightgbm", "overlap_baseline", "random_baseline")
    labels = {
        "lightgbm": "LightGBM",
        "overlap_baseline": "Overlap baseline",
        "random_baseline": "Random baseline",
    }

    lines = []
    lines.append("# Job Ranker — Evaluation Report")
    lines.append("")
    lines.append(f"_Generated: {evaluation.get('generated_on', 'n/a')}_")
    lines.append("")
    lines.append("## Dataset")
    lines.append("")
    lines.append(f"- Source export: `{evaluation.get('training_input', 'n/a')}`")
    lines.append(f"- Jobs (documents): {evaluation.get('n_jobs', 'n/a')}")
    lines.append(f"- Query groups (synthetic user profiles): {evaluation['n_groups']}")
    lines.append(
        f"- Evaluation: **leave-one-group-out** cross-validation "
        f"({evaluation['n_folds']} folds, seed={evaluation['seed']})"
    )
    lines.append(f"- Label provenance: **{evaluation['label_provenance']}**")
    embeddings_enabled = evaluation.get("embeddings_enabled", True)
    lines.append(
        f"- Skill-embedding feature: **{'enabled' if embeddings_enabled else 'DISABLED'}** "
        + (
            "(sentence-transformers loaded)."
            if embeddings_enabled
            else "(sentence-transformers unavailable — `skill_embedding_cosine` is 0 for "
            "every pair, so the learned ranker loses its main signal over the overlap "
            "baseline; lift below is a lower bound)."
        )
    )
    lines.append("")
    lines.append("## Method")
    lines.append("")
    lines.append(
        "Relevance grades (0-3) are produced by **weak-supervision labeling functions** "
        "(skill-overlap quartiles + role-title keyword boost), not human judgements. "
        "Each user-group is held out whole in turn (no within-group leakage); the fold "
        "model trains on the remaining groups. These fold models are throwaways — the "
        "committed production model is trained on all data separately."
    )
    lines.append("")
    lines.append("Metrics are averaged over the folds. MAP treats grades "
                 f">= {evaluation['relevant_grade_for_map']} as relevant.")
    lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| Metric | " + " | ".join(labels[r] for r in rankers) + " |")
    lines.append("|" + "---|" * (len(rankers) + 1))
    for metric_name, scores in metrics.items():
        row = f"| {metric_name} | " + " | ".join(f"{scores[r]:.4f}" for r in rankers) + " |"
        lines.append(row)
    lines.append("")

    # Headline lift vs the stronger (overlap) baseline.
    ndcg_keys = [k for k in metrics if k.startswith("ndcg@")]
    if ndcg_keys:
        primary = ndcg_keys[0]
        lift = metrics[primary]["lightgbm"] - metrics[primary]["overlap_baseline"]
        lines.append(
            f"LightGBM {primary} lift over the overlap baseline: **{lift:+.4f}**."
        )
        lines.append("")

    lines.append("## Limitations")
    lines.append("")
    lines.append("- Query groups are a handful of **synthetic** user profiles, not real users.")
    lines.append("- Postings are templated fixtures, not live market data.")
    lines.append("- Labels are **weak/pseudo** (heuristic), so absolute numbers are indicative, "
                 "not authoritative; the meaningful signal is lift over baselines.")
    lines.append("- The holdout is small (few groups); treat metrics as a sanity check.")
    lines.append("")
    lines.append("## Next steps (real-data upgrade)")
    lines.append("")
    lines.append("- Ingest real Egyptian postings (Wuzzuf/Bayt) via "
                 "`Backend/apps/jobs/ingest/csv_loader.py` / `wuzzuf.py`, then "
                 "`manage.py export_jobs_for_ranker --real-only` and "
                 "`manage.py train_job_ranker --real-only`.")
    lines.append("- Build a small human-labeled gold set and re-run evaluation against it.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
