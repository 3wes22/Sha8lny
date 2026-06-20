# CLAUDE.md - AI Models

This file reflects the **as-built** AI stack for Sha8lny. Older plans for fully
custom fine-tuned LLaMA/Mistral models are historical planning material only and
must not be defended as implemented work.

## Current Runtime

- **Hosted demo LLM:** Gemini, called from the Django backend through
  `Backend/apps/core/llm_provider.py`.
- **Local fallback:** Ollama/Gemma-compatible provider, also routed through the
  Django backend provider layer.
- **Deterministic fallbacks:** Assessment, roadmap, advisory, and jobs all have
  non-LLM fallback paths so the demo can run without a live API key.
- **No committed fine-tuned LLMs:** There are no LoRA adapters, no LLaMA/Mistral
  base-model downloads, and no production inference path that loads those models.

## What This Directory Contains

```text
ai-models/
├── data/
│   ├── knowledge_base/        # Curated career/RAG documents
│   ├── eval/                  # Retrieval evaluation sets
│   ├── roadmap-sh-data/       # Dev-only roadmap.sh snapshot; license restricted
│   ├── onet_data/             # O*NET reference data
│   └── job_ranker_training.json
├── eval_results/
│   └── retrieval/             # Committed RAG evaluation artifacts
├── models/
│   └── custom/
│       ├── EVAL_REPORT.md
│       └── job_ranker_eval.json
├── scripts/                   # Eval and ranker training scripts
├── src/
│   ├── rag/                   # Chroma, embeddings, hybrid retrieval, reranking
│   ├── recommendations/       # Job ranker feature/ranking helpers
│   ├── llm/                   # Experimental local inference helpers, not Django runtime
│   └── utils/
└── tests/
```

## RAG Pipeline

- Embeddings: `sentence-transformers` (`all-MiniLM-L6-v2` by default).
- Vector DB: ChromaDB persistent collections.
- Retrieval: dense retrieval + BM25 + reciprocal rank fusion.
- Reranking: cross-encoder reranker when dependencies are available.
- Evaluation artifacts live under `ai-models/eval_results/retrieval/` and are
  summarized in `docs/product/EVALUATION_REPORT.md`.

Build/rebuild the advisory vector DB:

```bash
cd ai-models
python -m src.rag.build_vector_db
```

Run retrieval evaluation:

```bash
cd ai-models
python scripts/run_retrieval_eval.py --stage rerank
```

## Job Ranker

The job ranker is a **weak-supervision demonstrator**, not a market-validated
model. Current committed evidence includes:

- `ai-models/models/custom/job_ranker_eval.json`
- `ai-models/models/custom/EVAL_REPORT.md`
- `docs/product/JOB_RANKER_METHODOLOGY.md`

The binary `job_ranker.lgb` is not committed in the current repository. Runtime
ranking should therefore be described as:

1. LightGBM-capable when a trained local model file exists.
2. Skill-overlap fallback when the model file is absent.
3. Evaluated on synthetic fixture jobs with pseudo-labels, not human relevance
   judgments or real labeled Egyptian market data.

Retrain path:

```bash
cd Backend
python manage.py ingest_jobs_csv
python manage.py train_job_ranker --real-only
```

or use the `ai-models/scripts/train_job_ranker.py` workflow documented by the
ranker methodology report.

## Assessment Scenario Corpus

The assessment scenario corpus lives in:

```text
Backend/apps/assessments/scenario_corpus/
```

Scenario retrieval is configured in `Backend/apps/core/ai_settings.py`.
As currently built, `ASSESSMENT_SCENARIO_RAG_ENABLED` defaults to `true`; when a
role/subskill has no approved matching scenario, retrieval safely returns an
empty list and the static prompt/fallback path remains in control.

Useful backend commands:

```bash
cd Backend
python manage.py rebuild_scenario_index
python manage.py scenario_corpus_audit --tier 1
```

## Data Provenance Rules

- `roadmap-sh-data/` is **development fallback only** because its source license
  prohibits redistribution.
- `jobs_egypt_tech.csv` is synthetic fixture data, not evidence of live Wuzzuf
  scraping or real market coverage.
- Real Egyptian job-posting acquisition is an operator step documented in
  `docs/product/DATASET_REGISTRY.md`.
- Any thesis claim about model quality must cite committed eval artifacts and
  state whether labels are synthetic, weak-supervision, or human-reviewed.

## Commands

```bash
cd ai-models
python -m pytest tests
python scripts/run_retrieval_eval.py --stage rerank
```

Backend AI paths are tested from `Backend/`:

```bash
cd Backend
pytest apps/assessments apps/advisory apps/jobs apps/roadmaps
```

## Do Not Claim

- Do not claim fine-tuned LLaMA/Mistral models are implemented.
- Do not claim `job_ranker.lgb` is committed unless it is actually present in
  `ai-models/models/custom/`.
- Do not claim the current job fixtures are real scraped Wuzzuf postings.
- Do not claim expert review or faithfulness evaluation is complete until the
  corresponding completed results are committed.
