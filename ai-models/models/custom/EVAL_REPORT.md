# Job Ranker — Evaluation Report

_Generated: 2026-06-08_

## Dataset

- Source export: `/home/user/repo/ai-models/data/job_ranker_training.json`
- Jobs (documents): 60
- Query groups (synthetic user profiles): 8
- Evaluation: **leave-one-group-out** cross-validation (8 folds, seed=42)
- Label provenance: **weak-supervision (pseudo-label), not ground truth**
- Skill-embedding feature: **DISABLED** (sentence-transformers unavailable — `skill_embedding_cosine` is 0 for every pair, so the learned ranker loses its main signal over the overlap baseline; lift below is a lower bound).

## Method

Relevance grades (0-3) are produced by **weak-supervision labeling functions** (skill-overlap quartiles + role-title keyword boost), not human judgements. Each user-group is held out whole in turn (no within-group leakage); the fold model trains on the remaining groups. These fold models are throwaways — the committed production model is trained on all data separately.

Metrics are averaged over the folds. MAP treats grades >= 2.0 as relevant.

## Results

| Metric | LightGBM | Overlap baseline | Random baseline |
|---|---|---|---|
| ndcg@5 | 0.5827 | 0.5833 | 0.1597 |
| ndcg@10 | 0.5797 | 0.5833 | 0.2177 |
| map | 0.3750 | 0.3750 | 0.1589 |

LightGBM ndcg@5 lift over the overlap baseline: **-0.0006**.

## Limitations

- Query groups are a handful of **synthetic** user profiles, not real users.
- Postings are templated fixtures, not live market data.
- Labels are **weak/pseudo** (heuristic), so absolute numbers are indicative, not authoritative; the meaningful signal is lift over baselines.
- The holdout is small (few groups); treat metrics as a sanity check.

## Next steps (real-data upgrade)

- Ingest real Egyptian postings (Wuzzuf/Bayt) via `Backend/apps/jobs/ingest/csv_loader.py` / `wuzzuf.py`, then `manage.py export_jobs_for_ranker --real-only` and `manage.py train_job_ranker --real-only`.
- Build a small human-labeled gold set and re-run evaluation against it.
