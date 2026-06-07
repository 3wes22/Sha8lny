# Job ranker methodology (C7)

## Model

- **Algorithm:** LightGBM `lambdarank` (`job_ranker.lgb` under `ai-models/models/custom/`)
- **Features:** `skill_embedding_cosine`, `required_skill_overlap_ratio`, `experience_level_delta`, `job_freshness_score`, `location_match`
- **Embeddings:** `all-MiniLM-L6-v2` (same family as RAG)

## Training data (pseudo-labels)

Training does **not** use the same overlap score as the only label. For each of 8 synthetic skill profiles, all jobs in the export receive relevance grades 0–3 based on:

1. Required-skill overlap quartile within that profile’s job set
2. Title keyword boost (`backend`, `frontend`, `data`, etc.)

Manual evaluation pairs for thesis anti-circularity: export a held-out CSV and compare ranker order vs overlap-only (see `ai-models/data/job_ranker_training.json`).

## Runtime

- `JobService.match_jobs_for_user` sorts with the ranker when the model file exists.
- **Displayed `match_score`** remains required-skill overlap % (interpretable).
- **Order** follows the learned ranker score.
- **Career level filter** (`experience_matching.py`): jobs above the user’s band are excluded (e.g. entry users do not see senior/lead postings). Level is inferred from active roadmap template, assessment score, or skill proficiency.

## Retrain

```bash
cd Backend
python manage.py ingest_jobs_csv
python manage.py train_job_ranker --real-only
```

## Limitations

- Pseudo-labels, not human relevance judgments at scale
- One-time Wuzzuf snapshot (`platform_metadata.scraped_at`), not daily scraping
