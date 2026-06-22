# Data Sources & Citations

Provenance, version, license, and geographic scope for every external dataset the
platform depends on. Kept honest on purpose: where a source is restrictive,
US-centric, or synthetic, that is stated rather than glossed.

| Source | Version | License | Retrieved | Geographic scope | Used for |
|---|---|---|---|---|---|
| O*NET Database | 30.1 | CC BY 4.0 (attribution required) | local copy in repo | United States | Skills/tasks taxonomy reference; **backend-role-only** milestone crosswalk PoC |
| roadmap.sh content | repo snapshot | **Proprietary — personal use only, redistribution prohibited** | local copy in repo | Global | Source of learning-path *structure* for roadmap generation |
| Coursera course catalog (`azrai99/coursera-course-dataset`) | HF snapshot | Apache-2.0 (attribution) | `ai-models/data/courses/` | Global | Real course **metadata** for roadmap course recommendation (1,886 career-relevant of 6,645) |
| `jobs_egypt_tech.csv` | v1 (internal) | Internal/synthetic | hand-authored | Egypt (synthetic) | Job-ranker training/eval fixtures |
| Real Egyptian job postings | — | _TBD_ | _not yet acquired_ | Egypt | **Future work**: real-data job-ranker training + gold-set evaluation |

---

## O*NET 30.1

- **Publisher:** O*NET program, sponsored by the U.S. Department of Labor,
  Employment & Training Administration (USDOL/ETA).
- **License:** Creative Commons Attribution 4.0 (CC BY 4.0). Attribution is
  required: "This page includes information from O*NET … used under the CC BY 4.0
  license. O*NET is a trademark of USDOL/ETA."
- **Local copy:** `ai-models/data/onet_data/db_30_1_text/`.
- **How we use it:** as a skills/tasks **taxonomy reference**. The crosswalk in
  `Backend/apps/roadmaps/onet_mapper.py` maps a small set of backend-developer
  milestone keywords (10 mappings) to O*NET element IDs. It is a **proof of
  concept for the backend role only** — every other role returns no O*NET links.
- **Concede:** O*NET is **US-centric**. It is a taxonomy anchor, not Egyptian
  labor-market data.

## roadmap.sh

- **Publisher:** roadmap.sh — Copyright © 2017–present, Kamran Ahmed.
- **License:** **Restrictive / proprietary.** Per
  `ai-models/data/roadmap-sh-data/license`, the content is "for personal use" and
  may **not** be republished or redistributed in any form without prior consent.
  The exception covers read-only GitHub forks made for contributing to the project.
- **How we use it:** the roadmap *structure* (phases / topics / ordering) is the
  basis for generated learning paths, retrieved via semantic search.
- ⚠️ **Compliance risk (known issue):** a vendored copy of this content currently
  lives in the repository (`ai-models/data/roadmap-sh-data/src/...`). Redistributing
  it conflicts with the license above. Before any public release or publication:
  fetch the content at runtime instead of vendoring it, obtain explicit consent
  from the author, or replace it with an openly licensed alternative (e.g. an
  MIT/CC-BY curated skills graph). Treat the current copy as development-only.
- **Concede:** roadmap.sh paths are **global/generic**, not Egypt-specific.

## Job postings (`jobs_egypt_tech.csv`)

- **Provenance:** hand-authored synthetic fixtures
  (`Backend/apps/jobs/ingest/fixtures/jobs_egypt_tech.csv`, ~60 rows). Company names
  are real Egyptian employers but the postings/descriptions are templated, not
  scraped live listings.
- **How we use it:** the only data behind the current LightGBM job ranker. Training
  labels are **weak supervision** (pseudo-labels), and the ranker is evaluated by
  leave-one-group-out NDCG/MAP vs. baselines (see
  `ai-models/models/custom/EVAL_REPORT.md`).
- **Concede:** this is **not real market data**. It exists to demonstrate the
  pipeline and evaluation methodology end-to-end.

## Future: real Egyptian job postings

- **Plan:** ingest a real Wuzzuf/Bayt dataset (Kaggle dump or a permitted scrape)
  via `Backend/apps/jobs/ingest/csv_loader.py` / `wuzzuf.py`, then re-export with
  `manage.py export_jobs_for_ranker --real-only` and retrain with
  `manage.py train_job_ranker --real-only`. Pair it with a small human-labeled gold
  evaluation set. License, version, and retrieval date must be recorded **here**
  before any such dataset is committed or used.
