# Quickstart: Two-Stage Adaptive Assessment Question Generation

## 1. Start the stack

### Backend

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate
python manage.py runserver
```

### Frontend

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Frontend
npm install
npm run dev
```

### Local AI runtime

```bash
ollama serve
ollama pull gemma4:e2b
```

### Optional production-like cache / queue services

```bash
redis-server
```

## 2. Core verification commands

### Backend unit and integration checks

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate
pytest apps/assessments/tests/test_role_graph.py
pytest apps/assessments/tests/test_engine.py
pytest apps/assessments/tests/test_stage_cache.py
pytest apps/assessments/tests/test_staged_flow.py
pytest apps/assessments/tests/test_api.py
pytest apps/assessments/tests/test_frontend_contracts.py
pytest apps/roadmaps/tests/test_api.py
python manage.py check
```

### Frontend checks

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Frontend
npm run test:run
npm run build
```

## 3. Manual acceptance walkthrough

### Stage 1 readiness

1. Open `/assessment`.
2. Create a new `skills` assessment for a supported role.
3. Confirm the UI reports stage-one preparation and then shows stage-one questions.
4. Repeat creation for the same role and confirm stage one is served through the cache path when available.

### Stage transition

1. Complete all stage-one questions.
2. Submit the first stage.
3. Confirm the UI switches to an "Analyzing your responses..." transition state.
4. Confirm stage-two questions appear without starting a new assessment.

### Final result

1. Complete all stage-two questions.
2. Submit the second stage.
3. Confirm the result screen shows standard result summaries plus `roadmap_signal`-backed capability output.
4. Confirm roadmap creation can prefer the structured roadmap signal when present.

## 4. Failure and fallback checks

1. Stop Ollama and create a new supported-role assessment.
2. Confirm stage one still becomes available through the deterministic fallback path.
3. Stop Ollama before stage-two generation and confirm the assessment still reaches a usable final result.
4. Confirm failure states do not leave the frontend in a permanent spinner.

## 5. Cache and observability checks

1. Confirm stage-one cache keys are versioned by role key and role-graph version.
2. Confirm cache hits and misses are visible in logs or generation metadata.
3. Confirm each completed staged assessment records no more than three model invocations total:
   - stage 1 generation
   - stage 2 generation
   - final evaluation
4. Confirm fallback usage, validation failures, and trace IDs are stored or exposed for debugging.

## 6. Environment notes

- Development should use `DJANGO_CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache` unless a local Redis cache is available.
- Production keeps Redis-backed cache and single-lane AI queue behavior.
- Model selection stays environment-driven; E2B is the conservative local default and E4B remains the stronger option on 16 GB hardware.

## 7. Verification status

Verified on `2026-04-15` in the local workspace:

- `cd Backend && pytest apps/assessments/tests apps/roadmaps/tests/test_api.py` → `56 passed`
- `cd Backend && python3 manage.py check` → no issues
- `cd Frontend && npm run test:run` → `33 passed`
- `cd Frontend && npm run build` → success

Notes:

- Staged assessment route tests are green.
- One React `act(...)` warning still appears in `Frontend/src/features/assessment/routes/AssessmentSessionPage.test.tsx`.
- Advisory route tests also emit separate `act(...)` warnings outside this staged-assessment feature scope.
