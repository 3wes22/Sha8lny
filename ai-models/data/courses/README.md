# Coursera Career-Course Catalog

A cleaned, role-tagged catalog of real Coursera courses used by the Roadmap
module to recommend courses per milestone. Replaces the prior hand-authored
demo courses with a real, attributable dataset.

## Files
- `coursera_career_courses.json` — the cleaned catalog (1,886 courses).
- `build_course_catalog.py` — the reproducible cleaning + role-tagging script
  (input: the raw HF dataset CSV; output: this JSON).

## Source & license
- **Dataset:** [`azrai99/coursera-course-dataset`](https://huggingface.co/datasets/azrai99/coursera-course-dataset)
  (Hugging Face), 6,645 Coursera course records.
- **License:** Apache-2.0 (permits use/redistribution with attribution).
- We use course **metadata** (title, public URL, skills, level, rating) for
  recommendation — not course content. Links resolve to public coursera.org pages.

## Cleaning pipeline (`build_course_catalog.py`)
1. Keep rows with a title and a real `coursera.org` URL; dedupe by URL.
2. Parse the stringified `Skills` lists; drop malformed sentence-like entries.
3. Parse numeric fields (`rating`, `num_reviews`, `enrolled`, satisfaction).
4. Normalize `Level` → `beginner` / `intermediate` / `advanced` / `all_levels`.
5. Trim the verbose module-by-module descriptions to an embedding-ready blurb.
6. **High-precision role tagging from title + curated skills only** (not the
   noisy description, which produced false positives like
   "Nuclear fuel management" → backend). Drop courses matching no role.

## Resulting catalog (6,645 raw → 1,886 career-relevant)

| Role | Courses |  | Field coverage |  |
|---|--:|---|---|--:|
| data_science | 710 | | has curated skills | 89% |
| machine_learning_engineer | 500 | | has rating | 76% |
| devops | 498 | | avg rating | 4.56 |
| backend | 239 | | avg skills/course | 4.2 |
| frontend | 128 | | beginner | 946 |
| ui_ux_designer | 123 | | intermediate | 740 |
| android | 36 | | advanced | 83 |
| fullstack | 26 | | unlabeled level | 117 |

A course may map to several roles. **Known skew:** Coursera over-indexes on
data/ML/cloud, so `android`, `fullstack`, and `frontend` are thinner — a second
source (e.g. a Udemy web/mobile dataset) would balance these in future work.

## Record schema
`title, url, organization, instructor, level, skills[], description,
rating, num_reviews, enrolled, satisfaction_rate, roles[], provider`

## Reproduce
```bash
# from the dataset's HF page, download coursera_course_2024.csv as coursera_raw.csv, then:
python build_course_catalog.py   # writes coursera_clean.{json,csv}
```

## Loaded into the app via
`python manage.py ingest_courses` (Backend) — upserts into the `Course`
catalog under a "Coursera" platform and rebuilds the embedding index when
available; roadmap course-matching falls back to deterministic skill/role/level
ranking when the vector store is absent.
