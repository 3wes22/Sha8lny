# Graduation Demo Runbook

This runbook keeps the evaluator story focused on the core product loop:

`assessment -> roadmap -> progress -> advisory`

## Demo Accounts

- New user: `demo.new@sha8alny.local` / `DemoPass123!`
- Returning user: `demo.progress@sha8alny.local` / `DemoPass123!`

The new user account is intentionally empty. The returning user is pre-seeded with:

- a completed backend assessment
- an active roadmap
- completed milestones and completed courses
- a current milestone in progress
- visible learning-hours and streak data

## Local Startup

### 1. Backend

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 manage.py migrate
python3 manage.py seed_graduation_demo --reset
python3 manage.py seed_courses
python3 manage.py rebuild_course_index
cd ../ai-models && python -m rag.seeder && cd ../Backend
python3 manage.py seed_jobs --clear --count 24
python3 manage.py extract_job_skills --limit 24
python3 manage.py ai_smoke
python3 manage.py runserver
```

Always run all commands in order after any reset — skipping `rebuild_course_index` or `rag.seeder` will produce zero course matches or ungrounded advisory responses.

### 2. Frontend

```bash
cd Frontend
npm install
npm run dev
```

The frontend points to `http://localhost:8000/api/v1` by default. Only set `VITE_API_BASE_URL` if the backend is running somewhere else.

## Hosted Demo Mode

The default runtime is hosted Gemini.

Use these settings in `Backend/.env`:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

This is the recommended mode for the evaluator demo because it matches the current backend default path.

## Local AI Fallback

If hosted inference is unavailable, switch to Ollama:

```env
AI_PROVIDER=ollama
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=gemma4:e2b
```

The product should still stay usable if the AI runtime is unavailable:

- assessment and roadmap generation expose controlled failure states
- advisory shows a fallback assistant message instead of a broken blank surface

## Demo Script

### Path A: New User

1. Sign in as `demo.new@sha8alny.local`.
2. Open the assessment flow.
3. Complete the staged questions.
4. Show the generated assessment result.
5. Generate a roadmap and activate it.
6. Land on the dashboard and show the first next action.
7. Open advisory and ask what to focus on next.

### Path B: Returning User

1. Sign in as `demo.progress@sha8alny.local`.
2. Open the dashboard first.
3. Point out:
   - active roadmap
   - current phase
   - completed milestones
   - completed courses
   - streak and logged learning hours
   - next action
4. Open the roadmap view and show the active milestone.
5. Open advisory and ask for the next backend career move.
6. Open jobs as a supporting surface if needed.

## Reset Between Rehearsals

Use this command before each fresh demo pass:

```bash
cd Backend
source venv/bin/activate
python3 manage.py seed_graduation_demo --reset
python3 manage.py seed_courses
python3 manage.py rebuild_course_index
cd ../ai-models && python -m rag.seeder && cd ../Backend
python3 manage.py seed_jobs --clear --count 24
python3 manage.py extract_job_skills --limit 24
python3 manage.py ai_smoke
```

Always run all eight commands in order after any reset — skipping `rebuild_course_index` or `rag.seeder` will produce zero course matches or ungrounded advisory responses.

## Notes

- **Demo language:** English-only demo; advisory KB is English. Arabic input should redirect gracefully, not crash.
- **AI runtime:** Hosted Gemini (`AI_PROVIDER=gemini`) is the default; deterministic fallbacks protect every AI feature if the API is unavailable.

## Verification

Recommended graduation-slice verification commands:

```bash
cd Backend
python3 manage.py check
pytest apps/assessments/ apps/roadmaps/ apps/advisory/ apps/jobs/ apps/core/tests.py apps/courses/tests/ apps/integration/tests/ apps/users/tests/test_demo_seed.py
```

```bash
cd Frontend
npm run test:run
```

## Demo Hardening

### Offline path (verified — dead `GEMINI_API_KEY`, no Chroma volume)

The product runs end-to-end with no AI key and no vector store; every AI feature
degrades to its deterministic fallback. Verified by the offline full-loop test:

```bash
cd Backend
env -u GEMINI_API_KEY venv/bin/python -m pytest apps/roadmaps/tests/test_full_loop.py -q
# 1 passed — assessment -> roadmap (fallback provenance) -> courses (matched)
#            -> jobs (ranked + explained) -> advisory (citation contract)
```

Observed offline behavior (recorded):
- **Assessment / roadmap:** deterministic, assessment-aware structure; roadmap
  provenance reports `fallback_used=true`, `structure_license_tier=internal`.
- **Courses:** embedding match still links `RoadmapCourse` rows when the course
  index is seeded; otherwise milestones simply show no course (no crash).
- **Jobs:** skill match runs fully offline. If a local `job_ranker.lgb` exists,
  the LightGBM reranker can order results; otherwise the endpoint falls back to
  skill-overlap ordering. `explanation.top_factors` remains present in both
  paths.
- **Advisory:** returns a grounded fallback message; the chat payload still
  carries `retrieved_documents: []` and the `no_retrieval_context` flag, so the
  UI renders the honest "no grounded sources" state instead of breaking.

To force offline mode in a live demo, unset the key for that shell:
`env -u GEMINI_API_KEY python3 manage.py runserver`.

### Fresh-API-key rehearsal checklist (online path)

1. Put a **fresh** `GEMINI_API_KEY` (unused quota) in `Backend/.env`;
   `AI_PROVIDER=gemini`.
2. Run the full reset (eight commands above) **once**.
3. `python3 manage.py ai_smoke` — confirm a real Gemini round-trip succeeds.
4. Warm the advisory BM25 index once before the live demo (first query per
   process pays a one-time ~16s index build): ask one throwaway advisory question.
5. Walk Path A then Path B end-to-end once; confirm advisory shows **Sources**
   with confidence badges on a grounded question.
6. Do **not** run the full test suite after this — it will exhaust the key.

### Quota budget (important)

- The full backend test suite makes enough Gemini calls to **exhaust a key (429s)**.
  Rehearse the demo on a **fresh** key and **never run the suite right before the
  demo**. Run tests quota-safe with `env -u GEMINI_API_KEY` (do **not** set
  `GEMINI_API_KEY=` empty — that breaks 14 assessment stage-cache tests).
- Keep a spare key in reserve; if mid-demo calls start 429-ing, the offline path
  above keeps every surface usable.

## PR6 — Expert review & faithfulness (operator steps)

These complete claims **C3** / **C11** after the code/docs remediation PRs.

### Expert review (human session)

1. Share [`EXPERT_REVIEW_PACKET.md`](EXPERT_REVIEW_PACKET.md) + blank
   [`expert_review_scoring_sheet.csv`](expert_review_scoring_sheet.csv) with three reviewers.
2. Generate engine reference scores on the pilot sample answers (keyword fallback, no API key):

   ```bash
   cd Backend
   env -u GEMINI_API_KEY python manage.py score_expert_review_reference
   ```

3. After reviewers return scores, analyze agreement:

   ```bash
   python ai-models/scripts/analyze_expert_review.py \
     --csv docs/product/expert_review_scoring_sheet.csv \
     --engine docs/product/expert_review_engine_scores.json
   ```

4. Record the JSON summary in [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md) §4.

### Faithfulness (LLM judge, fresh Gemini key)

```bash
cd ai-models
export GEMINI_API_KEY=<fresh-key>
python scripts/eval_faithfulness.py --items data/eval/faithfulness_pilot.json
# cached per item under eval_results/faithfulness/
```

Target: mean faithfulness **> 0.85** on the pilot set; expand to a larger logged
advisory sample before thesis submission.

### Thesis charts (offline, no API)

```bash
python ai-models/scripts/generate_eval_charts.py
# writes docs/thesis/assets/fig-5.2-ranker-ndcg.svg and fig-5.3-retrieval-recall-mrr.svg
```
