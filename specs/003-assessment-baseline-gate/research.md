# Research: Staged Assessment Baseline Review Gate

## Sources Reviewed

- `/Users/mohamed3wes/Downloads/Grad-Project/specs/003-assessment-baseline-gate/spec.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/.specify/memory/constitution.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/specs/003-assessment-baseline-gate/checklists/role-graph-curation.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/ai_pipeline.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/role_graph.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/role_graph_data.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/services.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tests/test_engine.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tests/test_role_graph.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tests/test_stage_cache.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tests/test_staged_flow.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tests/test_frontend_contracts.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/roadmaps/services.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Frontend/src/lib/api.ts`

## Decision 1: Treat the current working tree as a baseline candidate, not an accepted baseline

**Decision**: The staged-assessment changes currently in the working tree must go through an explicit review gate before the team builds further implementation on top of them.

**Rationale**: The candidate changes multiple high-risk surfaces at once: curated role-graph content, loader validation, cache invalidation behavior, deterministic fallback behavior, roadmap signal semantics, and typed frontend/backend contracts. That is too much coupled behavior to accept implicitly.

**Alternatives considered**:

- Accept the working tree as the new baseline immediately: rejected because contract drift or fallback regressions would become harder to unwind after downstream work starts.
- Reject the working tree without structured review: rejected because the candidate may already represent the strongest product path and should be judged on evidence rather than caution alone.

## Decision 2: Use explicit `accept`, `revise`, and `reject` outcomes

**Decision**: The gate will not force a binary yes/no outcome. It will use `accept`, `revise`, or `reject`.

**Rationale**: Human judgment is required here. `revise` captures the common case where the direction is correct but one or more blockers make the current snapshot unsafe as baseline.

**Alternatives considered**:

- Use only `accept` or `reject`: rejected because it turns bounded blockers into overreactions.
- Use informal narrative feedback only: rejected because the team needs a stable decision they can act on.

## Decision 3: Make the role-graph handoff contract a blocking review surface

**Decision**: The curated role graph in `Backend/apps/assessments/role_graph_data.py` remains the sole runtime handoff file, and the gate must verify that loader behavior still enforces supported-role coverage, graph-key integrity, and explicit validation failures.

**Rationale**: The working tree changes the role-graph shape from earlier stub assumptions to curated `curated-v1` data. If this contract is wrong, stage targeting, cache reuse, roadmap signals, and role recommendations all become unreliable.

**Alternatives considered**:

- Review only question-generation behavior and ignore the curated content structure: rejected because the graph now drives more than question selection.
- Allow silent fallback for invalid graphs: rejected because it would hide bad baseline content behind runtime behavior.

## Decision 4: Make stage-one cache/version semantics a blocking gate

**Decision**: The candidate baseline is only acceptable if stage-one cache keys remain explicitly bound to `{role_key, version}` and curated graph replacement invalidates stale question reuse.

**Rationale**: The working tree changes role-graph contents substantially. If the cache does not respect version boundaries, users can receive questions generated for a different graph shape while the rest of the system assumes new semantics.

**Alternatives considered**:

- Accept cache reuse as long as the role key matches: rejected because role-only keys cannot distinguish semantic graph updates.
- Defer cache review until later implementation: rejected because cache mistakes create misleading baseline confidence.

## Decision 5: Make deterministic fallback and the 3-call budget blocking gates

**Decision**: The gate must explicitly verify that the staged flow still completes with deterministic fallback behavior and preserves the maximum of 3 LLM calls per completed assessment.

**Rationale**: The staged feature only remains operationally viable if it stays within the local-model budget and remains demo-safe when the model or generation path fails.

**Alternatives considered**:

- Review only the happy path and assume fallback is unchanged: rejected because the candidate touches analysis and recommendation behavior.
- Allow more model calls temporarily: rejected because the branch baseline would immediately drift from the feature spec and cost constraints.

## Decision 6: Treat roadmap-signal generation and graph-driven recommendations as one coupled contract

**Decision**: The gate must review `roadmap_signal` output and `recommended_careers` generation together, because both are now influenced by the curated role graph and consumed downstream by roadmap logic.

**Rationale**: The working tree replaces alias-driven recommendations with graph-driven recommendations and keeps roadmap consumers preferring structured `roadmap_signal`. Those two behaviors must remain aligned or the baseline will create contradictory downstream signals.

**Alternatives considered**:

- Review roadmap signal only: rejected because recommendations still affect user-facing and fallback behavior.
- Review recommendations only: rejected because roadmap generation is the primary product value of the staged assessment.

## Decision 7: Use the existing staged API contract and typed frontend union as acceptance targets

**Decision**: The candidate baseline is acceptable only if backend responses continue to match the staged API contract and the frontend `AssessmentSubmissionState` union in `Frontend/src/lib/api.ts`.

**Rationale**: The frontend assessment flow depends on exact stage and submission-state semantics. Undocumented payload drift here would create ambiguous or broken UI transitions even if the backend tests pass in isolation.

**Alternatives considered**:

- Let frontend types catch up later: rejected because baseline adoption would knowingly normalize contract drift.
- Trust API tests without reviewing frontend types: rejected because the typed consumer is part of the contract surface.

## Decision 8: Require targeted automated evidence plus one manual walkthrough before recording a decision

**Decision**: The gate requires targeted backend tests, roadmap-consumer checks, frontend contract review, and a manual walkthrough of creation, stage transition, completion, and fallback behavior.

**Rationale**: No single evidence source is sufficient here. Automated tests catch behavioral regressions, while manual walkthroughs catch transition-state and integration issues that can still be invisible in unit coverage.

**Alternatives considered**:

- Rely on tests only: rejected because the decision includes human judgment over product fit and contract readability.
- Rely on manual review only: rejected because the candidate changes too many deterministic invariants to skip automated evidence.

## Decision 9: No unresolved planning clarifications remain

**Decision**: The plan can proceed without marking any remaining `NEEDS CLARIFICATION` items.

**Rationale**: The combination of feature spec, constitution, current diff, contract tests, and curation checklist is sufficient to define the review gate and its artifacts.

**Alternatives considered**:

- Stop planning until a reviewer pre-commits to a preferred outcome: rejected because the plan’s purpose is to structure that decision.
