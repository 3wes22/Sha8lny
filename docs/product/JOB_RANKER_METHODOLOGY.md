# Job ranker methodology (C7)

## Model

- **Algorithm:** LightGBM `lambdarank` when a local `job_ranker.lgb` is present.
- **Committed artifact status:** the current repository commits evaluation artifacts
  (`job_ranker_eval.json`, `EVAL_REPORT.md`) but **does not commit** the binary
  `job_ranker.lgb`; runtime falls back to skill-overlap ordering when that file
  is absent.
- **Features:** `skill_embedding_cosine`, `required_skill_overlap_ratio`, `experience_level_delta`, `job_freshness_score`, `location_match`
- **Embeddings:** `all-MiniLM-L6-v2` (same family as RAG)

## Training data (pseudo-labels)

Training does **not** use the same overlap score as the only label. For each of 8 synthetic skill profiles, all jobs in the export receive relevance grades 0–3 based on:

1. Required-skill overlap quartile within that profile’s job set
2. Title keyword boost (`backend`, `frontend`, `data`, etc.)

Manual evaluation pairs for thesis anti-circularity: export a held-out CSV and compare ranker order vs overlap-only (see `ai-models/data/job_ranker_training.json`).

## Runtime

- `JobService.match_jobs_for_user` sorts with the ranker when the model file exists.
- If the model file is missing or ranking fails, the endpoint falls back to
  required-skill-overlap ordering.
- **Displayed `match_score`** remains required-skill overlap % (interpretable).
- **Order** follows the learned ranker score only in model-present runs.
- **Career level filter** (`experience_matching.py`): jobs above the user’s band are excluded (e.g. entry users do not see senior/lead postings). Level is inferred from active roadmap template, assessment score, or skill proficiency.

## Retrain / produce local model

```bash
cd Backend
python manage.py ingest_jobs_csv
python manage.py train_job_ranker --real-only
```

## Limitations

- Pseudo-labels, not human relevance judgments at scale
- Synthetic fixture postings in the current repo, not defended live market data
- No committed `job_ranker.lgb` binary in the current repository
- Real Egyptian postings and model retraining are documented operator steps
