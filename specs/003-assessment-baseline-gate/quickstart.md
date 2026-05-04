# Quickstart: Running the Staged Assessment Baseline Review Gate

## 1. Inventory the candidate snapshot

Run these commands from the repository root to confirm what the gate is reviewing.

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project
git status --short --branch
git diff --stat
git diff -- Backend/apps/assessments/ai_pipeline.py Backend/apps/assessments/role_graph.py Backend/apps/assessments/role_graph_data.py Backend/apps/assessments/services.py
git diff -- Backend/apps/assessments/tests/test_engine.py Backend/apps/assessments/tests/test_role_graph.py Backend/apps/assessments/tests/test_stage_cache.py Backend/apps/assessments/tests/test_staged_flow.py
```

## 2. Run blocking backend verification

These checks cover the candidate's highest-risk behavior changes.

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project/Backend
source venv/bin/activate
pytest apps/assessments/tests/test_role_graph.py
pytest apps/assessments/tests/test_engine.py
pytest apps/assessments/tests/test_stage_cache.py
pytest apps/assessments/tests/test_staged_flow.py
pytest apps/assessments/tests/test_frontend_contracts.py
pytest apps/roadmaps/tests/test_api.py
python manage.py check
```

## 3. Review the contract-bearing code paths

Confirm the implementation still matches the planned contract surfaces.

```bash
cd /Users/mohamed3wes/Downloads/Grad-Project
rg -n "load_role_graph|CURATED_VERSION|assessment:stage1|recommended_careers|roadmap_signal|submission_state" Backend/apps/assessments Backend/apps/roadmaps Frontend/src/lib/api.ts
sed -n '1,220p' specs/003-assessment-baseline-gate/contracts/role-graph-handoff.md
sed -n '1,260p' specs/003-assessment-baseline-gate/contracts/assessment-staged-api.md
sed -n '1,220p' specs/003-assessment-baseline-gate/contracts/roadmap-signal-contract.md
sed -n '1,220p' specs/003-assessment-baseline-gate/contracts/baseline-review-gate.md
```

## 4. Manual workflow walkthrough

Use one supported role, then repeat fallback checks with Ollama unavailable.

### Standard staged flow

1. Start the backend and frontend.
2. Create a new `skills` assessment for a supported role.
3. Confirm `POST /assessment/` returns `stage_1` with `presentation.submission_state = stage_1_generating`.
4. Poll the detail endpoint until stage one is ready and confirm exactly 5 active questions.
5. Submit stage one and confirm the API returns `stage_1_analyzing`.
6. Poll the detail endpoint until stage two is ready and confirm exactly 5 active questions plus `gap_profile_summary`.
7. Submit stage two and confirm the result endpoint eventually returns `submission_state = completed` plus `roadmap_signal`.

### Fallback and baseline-safety checks

1. Stop Ollama before stage-one generation and confirm the staged flow still reaches a usable question set.
2. Stop Ollama before stage-two generation or final evaluation and confirm the assessment still reaches completion through deterministic fallback.
3. Confirm the final result still exposes `roadmap_signal.generation_metadata.fallback_used`.
4. Confirm repeated stage-one generation for the same role changes when the role-graph version changes.

## 5. Decision rules

Use the following rules when recording the human baseline decision.

- `accept`: all blocking criteria pass, contracts and code agree, and remaining follow-ups do not undermine the baseline.
- `revise`: the direction is worth keeping, but one or more blocking issues mean the current snapshot is not yet safe to build on.
- `reject`: the candidate conflicts with the product direction or creates unacceptable contract, fallback, or compatibility risk.

## 6. Record the decision

At the end of the gate, capture:

1. The final outcome: `accept`, `revise`, or `reject`.
2. The exact blocking findings, if any.
3. The evidence used to justify the decision.
4. The follow-up work required before more implementation proceeds.

## 7. Verification note

This quickstart defines the required gate. It does not assume the current working tree has already passed the gate.
