# Quickstart: Running the Two-Stage Adaptive Assessment

This runbook exercises the staged skills-assessment flow end to end. It covers automated verification, a full manual walkthrough with Gemma enabled, and a deterministic-fallback walkthrough with Gemma disabled.

## 1. Automated verification

Run these from the repository root. All of them must pass before the staged flow is considered healthy.

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate

# Staged-assessment acceptance suite
pytest apps/assessments/tests/test_role_graph.py \
       apps/assessments/tests/test_engine.py \
       apps/assessments/tests/test_stage_cache.py \
       apps/assessments/tests/test_staged_flow.py \
       apps/assessments/tests/test_frontend_contracts.py

# Roadmap consumer contract
pytest apps/roadmaps/tests/test_api.py

# Django system check
python manage.py check
```

Expected: all tests pass, Django check reports zero issues.

## 2. Start the stack

Open three terminals.

**Terminal 1 — Ollama (optional for Gemma-backed runs):**

```bash
ollama serve
# In another shell once, to cache the model:
ollama pull gemma2:2b  # or whichever model your .env points at
```

**Terminal 2 — Backend:**

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate
python manage.py runserver
```

**Terminal 3 — Frontend:**

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Frontend
npm run dev
```

Access the app at http://localhost:5173.

## 3. Manual walkthrough — Gemma enabled

Perform the following for one supported role first, then repeat for the remaining five (backend, frontend, data science, fullstack, mobile, devops).

1. Log in and open the assessment flow.
2. Create a new `skills` assessment for the chosen role.
3. Confirm `POST /assessment/` returns stage 1 with `presentation.submission_state = stage_1_generating`.
4. Poll the detail endpoint until stage one becomes ready and confirm exactly 5 `active_questions`.
5. Submit stage one. Confirm the API transitions to `submission_state = stage_1_analyzing`.
6. Poll the detail endpoint until stage two becomes ready. Confirm exactly 5 new `active_questions` and a populated `gap_profile_summary`.
7. Submit stage two. Confirm the result endpoint eventually returns `submission_state = completed` plus a typed `roadmap_signal`.
8. In the completed response, verify `roadmap_signal.generation_metadata.fallback_used = false` (Gemma path was used).

**Expected LLM budget**: at most 3 Gemma calls per completed assessment (stage-1 generation, stage-2 generation, final evaluation). Confirm by tailing the backend logs or inspecting `generation_metadata` on the response.

## 4. Manual walkthrough — Gemma disabled (deterministic fallback)

This proves the assessment is demo-safe without a model runtime.

1. Stop the Ollama process (`Ctrl+C` in terminal 1, or `ollama kill`).
2. Reload the frontend and start a new `skills` assessment (try Backend Developer first).
3. Confirm stage one still loads 5 questions (deterministic fallback).
4. Submit stage one and confirm the flow still transitions into stage two with 5 targeted questions.
5. Submit stage two and confirm the result completes with a populated `roadmap_signal`.
6. Verify `roadmap_signal.generation_metadata.fallback_used = true` on at least one generation step.

## 5. Cache and version-bump spot check

1. Start a fresh skills assessment for one role while Ollama is running.
2. Confirm stage-one questions are served and cached.
3. Start a second skills assessment for the same role. Confirm stage-one questions are reused from cache (no additional Gemma call).
4. (When the curated partner ships new content): bump `CURATED_VERSION` in `Backend/apps/assessments/role_graph_data.py`.
5. Start another skills assessment for the same role. Confirm stage-one questions are regenerated (cache invalidated by version bump).

The automated test `test_stage_one_generation_invalidates_cache_when_graph_version_changes` in `apps/assessments/tests/test_stage_cache.py` covers this invariant.

## 6. Frontend contract spot check

On the Session and Results pages:

- `AssessmentSubmissionState` union values exposed by `Frontend/src/lib/api.ts` match the backend `submission_state` strings at every transition.
- The analyzing transition (`AnalyzingTransition.tsx`) appears during both `stage_1_analyzing` and `stage_2_analyzing`.
- The results page surfaces the structured `roadmap_signal` and the roadmap CTA once `submission_state = completed`.

## 7. Roadmap consumer spot check

1. Open a completed staged assessment.
2. Create a roadmap from that assessment.
3. Confirm the roadmap service prefers `roadmap_signal` over legacy score-based input. `apps/roadmaps/tests/test_api.py::TestRoadmapCreationAPI::test_create_ai_roadmap_prefers_structured_roadmap_signal` is the regression gate for this behavior.

## 8. Verification notes

Record the following after each manual walkthrough:

- Date and commit SHA used.
- Roles covered.
- Gemma status (running / stopped).
- Whether `fallback_used` was observed.
- Total Gemma calls per completed assessment (must be ≤ 3).
- Any deviation from the expected transitions above.

The feature is considered in good health when both Gemma-enabled and Gemma-disabled walkthroughs reach `submission_state = completed` with a populated `roadmap_signal` for every supported role.
