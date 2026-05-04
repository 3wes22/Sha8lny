# Baseline Review Gate Contract

## Purpose

This contract defines how the current staged-assessment working tree is reviewed before it can become the new branch baseline.

## 1. Candidate scope

The gate covers the current staged-assessment working tree on branch `002-ai-rag-experiment`, especially:

- role-graph structure and loader validation
- stage-one cache and version semantics
- deterministic fallback and LLM budget behavior
- roadmap-signal output and recommendation semantics
- frontend/backend typed contract alignment
- legacy compatibility and operational visibility

## 2. Required evidence

Baseline review must collect all of the following:

1. Diff inventory showing the exact candidate files under review.
2. Targeted automated verification for role graph, engine behavior, stage cache, staged flow, frontend contract behavior, and roadmap consumption.
3. Contract review against:
   - `assessment-staged-api.md`
   - `role-graph-handoff.md`
   - `roadmap-signal-contract.md`
4. One manual walkthrough of the staged flow plus fallback behavior.
5. A written decision record with rationale and follow-up actions.

## 3. Outcome states

### `accept`

Use when all blocking criteria pass and remaining follow-ups do not make the working tree unsafe as the implementation baseline.

### `revise`

Use when the direction should continue, but the current snapshot has blocking issues that must be fixed before downstream work builds on it.

### `reject`

Use when the working tree should not become baseline because it conflicts with product direction or introduces unacceptable contract, fallback, or compatibility risk.

## 4. Blocking criteria

The gate must not return `accept` if any of these fail:

- supported-role coverage and curated graph validation
- version-bound stage-one cache behavior
- deterministic completion and 3-call assessment budget
- roadmap-signal structural correctness
- frontend/backend contract alignment
- legacy assessment readability during rollout

## 5. Decision record shape

The final review note must capture:

```text
Outcome: accept | revise | reject
Rationale: short narrative
Blocking findings:
- finding 1
- finding 2
Evidence reviewed:
- command or file
- command or file
Follow-up actions:
- action 1
- action 2
Approver: name or team
Date: YYYY-MM-DD
```

## 6. Decision semantics

- `accept` means future implementation on this branch may treat the reviewed behavior as the current baseline.
- `revise` means the branch keeps moving in this direction, but new work must not normalize the current snapshot as baseline yet.
- `reject` means follow-on implementation must not build on this snapshot without a new planning and review decision.
