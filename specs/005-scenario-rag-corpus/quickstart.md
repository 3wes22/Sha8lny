# Quickstart: Scenario RAG Corpus

This is the minimum path to land the v1 wiring locally, validate it, and turn the feature on in your dev environment. Production rollout follows the staged plan in `plan.md`.

## Prerequisites

- Working `Backend/` dev environment per repo README (venv activated, migrations applied).
- `Backend/requirements.txt` already lists `chromadb>=0.5,<1.0` and `sentence-transformers>=2.2,<3.0`. If you ran `pip install -r requirements.txt` recently, you have what you need. No new deps.
- On first use, `sentence-transformers` will download `all-MiniLM-L6-v2` (~80 MB) to your Hugging Face cache. One time only.

## 1. Switch to the feature branch

```bash
git checkout 005-scenario-rag-corpus
```

## 2. Verify the corpus loads and validates

```bash
cd Backend
source venv/bin/activate
python manage.py check
```

`apps.assessments.apps.AssessmentsConfig.ready()` calls `assert_corpus_integrity()` on app load. A passing `check` means:

- Every approved `ScenarioDocument` in `scenario_corpus/*.py` passes `validate_scenario()`.
- Every `doc_id` is unique.
- Every `role_key` / `subskill_key` exists in `role_graph_data.ROLE_GRAPHS`.
- Every document's `corpus_version` matches `SCENARIO_CORPUS_VERSION`.

If any of the above fail, `manage.py` exits non-zero with an explicit reason. Fix the offending scenario before continuing.

## 3. Build the vector index

```bash
python manage.py rebuild_scenario_index
```

Expected output (paraphrased):

```
Validating corpus integrity (version=scenario-v1)...
Embedding 10 approved scenarios with all-MiniLM-L6-v2...
Wiping existing assessment_scenarios collection...
Indexed 10 scenarios into <BASE_DIR>/data/scenario_vector_db/.
```

The 10 documents are the converted seed from `BACKEND_FALLBACK_SCENARIOS`. They live under `role_key="backend"`.

The command is idempotent. Re-run it any time `scenario_corpus/*.py` changes.

## 4. Inspect coverage

```bash
python manage.py scenario_corpus_audit
```

Expected output (excerpt):

```
Coverage report (corpus_version=scenario-v1)
  backend
    stage 1 single_choice: 5/5 stage-1 subskills covered, 5 docs        OK
    stage 2 single_choice: 2/16 subskills covered, 2 docs                BELOW FLOOR (need >=2 per subskill across all 16)
    stage 2 multi_select : 1/16 subskills covered, 1 docs                BELOW FLOOR (need >=1 per subskill)
    stage 2 open_ended   : 2/16 subskills covered, 2 docs                BELOW FLOOR (need >=1 per subskill)
  frontend     : 0 docs                                                  BELOW FLOOR (corpus not yet authored)
  ... (other roles)
```

The audit exit code is non-zero whenever any cell is below the documented floor. This is **expected** in v1: only the seed slice is approved. The non-zero exit gates CI for full-corpus PRs, not for v1.

## 5. Run the new tests

```bash
pytest apps/assessments/tests/test_scenario_corpus.py -v
pytest apps/assessments/tests/test_scenario_retriever.py -v
pytest apps/assessments/tests/test_staged_flow.py -v
```

All tests should pass with the feature flag both off and on.

## 6. Turn the flag on in your local environment

Edit your `Backend/.env`:

```env
ASSESSMENT_SCENARIO_RAG_ENABLED=true
```

Restart the dev server:

```bash
python manage.py runserver
```

## 7. Smoke-test the staged flow

In another shell, start an assessment and trigger stage one. Tail the dev server logs and look for `scenario_retrieval` events:

```
INFO scenario_retrieval role_key=backend subskill_key=http_api_design question_type=single_choice stage=1 results_count=1 top_doc_id=backend.http_api_design.s1.single_choice.fallback-seed corpus_version=scenario-v1
```

If you see `scenario_retrieval_failed` instead, read the `error_type` field. The staged assessment will still complete — retrieval failure is non-fatal by contract.

## 8. Rollback

Flip the flag in `.env`:

```env
ASSESSMENT_SCENARIO_RAG_ENABLED=false
```

Restart the dev server. Prompt content and behavior return to byte-identical pre-feature behavior. No code revert needed, no data migration.

## 9. Adding new scenarios (author loop)

1. Open the per-role module under `Backend/apps/assessments/scenario_corpus/<role>.py`.
2. Append a new `ScenarioDocument` literal to the module-level `SCENARIOS` list. Set `review_status="draft"` while drafting.
3. When ready: set `review_status="approved"` and update `created_at`.
4. Run `python manage.py scenario_corpus_audit` and resolve any flags.
5. Run `python manage.py rebuild_scenario_index`.
6. Run the tests in step 5.
7. If you added enough scenarios to make a meaningful content change, bump `SCENARIO_CORPUS_VERSION` in `scenario_corpus/registry.py` (e.g. `scenario-v1` → `scenario-v2`). This invalidates the stage-one cache for affected roles automatically.

## Common issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `manage.py check` fails with `ScenarioDocument validation error: dimension_key mismatch` | The `dimension_key` you authored does not match the role graph for that subskill. | Look up the right dimension in `role_graph_data.ROLE_GRAPHS[<role_key>]` and fix. |
| `rebuild_scenario_index` raises `chromadb.errors.NoIndexException` | Collection was deleted out from under a stale client. | `rm -rf data/scenario_vector_db/` and re-run the command. |
| `scenario_retrieval_failed` with `error_type=ImportError` | `sentence-transformers` is not installed. | `pip install -r Backend/requirements.txt` from your venv. |
| Stage-one questions look the same as before despite the flag being on | The flag is on but the cached stage-one entries predate it. | Bump `SCENARIO_CORPUS_VERSION` or `python manage.py shell -c "from django.core.cache import cache; cache.clear()"`. |
