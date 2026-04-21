# Research: Two-Stage Adaptive Assessment Question Generation

## Sources Reviewed

- `/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/spec.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/.specify/memory/constitution.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/ai_pipeline.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/engine.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/role_graph.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/role_graph_data.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/services.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tasks.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/roadmaps/services.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Frontend/src/lib/api.ts`

## Decision 1: Replace the flat question flow with a two-stage adaptive flow

**Decision**: The skills assessment runs in two stages. Stage one is a broad calibration of exactly 5 questions across the role's core dimensions. Stage two is a targeted set of exactly 5 follow-up questions focused on the user's weakest or most uncertain subskills.

**Rationale**: The existing flat six-question bank cannot differentiate users inside a role. A short calibration followed by a targeted follow-up produces a stronger signal without making users answer a long generic questionnaire.

**Alternatives considered**:

- Keep the flat six-question flow: rejected because it cannot produce the structured roadmap-ready signal the downstream roadmap module needs.
- Use a fully adaptive per-question branching flow: rejected because it would blow past the 3-call LLM budget, add state complexity, and remain hard to test deterministically.

## Decision 2: Keep the staged runtime inside the existing Django modular monolith

**Decision**: All staged-assessment orchestration lives inside `Backend/apps/assessments/` and reuses the existing Celery + Redis cache + Ollama integration. No new runtime service is introduced.

**Rationale**: The product is still an MVP modular monolith. Introducing a separate AI service for one adaptive flow would add deployment surface without solving a constraint we actually have. Deterministic Django service code is the simpler, more testable option.

**Alternatives considered**:

- Extract a dedicated AI microservice: rejected as premature. The existing orchestration already handles caching, Celery, and Ollama cleanly.
- Move orchestration into the `ai-models/` package: rejected because the package is support-only per ADR-001 and must not own runtime behavior.

## Decision 3: Cap the staged flow at 3 LLM calls per completed assessment

**Decision**: Each completed staged assessment calls Gemma at most three times: stage-one generation, stage-two generation, and final evaluation.

**Rationale**: Local Gemma via Ollama is the runtime, and the product relies on zero API cost. A hard call ceiling keeps per-assessment cost predictable, keeps response times bounded, and forces the deterministic fallback path to stay first-class.

**Alternatives considered**:

- Allow up to one Gemma call per question: rejected because it breaks the call budget and creates unbounded generation latency.
- Drop the final evaluation call and keep only the two generation calls: rejected because the final call is where the evaluation narrative is enriched for the user; the structured output is still produced deterministically as a safety net.

## Decision 4: Back every Gemma call with a deterministic fallback

**Decision**: Stage-one generation, stage-two generation, and final evaluation must each produce valid typed output even when Ollama is unavailable or returns invalid content.

**Rationale**: The product must remain demo-safe and completable without a model runtime. A deterministic fallback is also what makes every stage independently testable in CI without mocking Gemma at every layer.

**Alternatives considered**:

- Fail the assessment when Gemma is unavailable: rejected because it makes the feature fragile for local development and for the demo path.
- Use a remote LLM as a fallback: rejected because it violates ADR-001 and reintroduces API cost.

## Decision 5: Model role content as a typed role graph, not as flat question banks

**Decision**: Each supported role is described by a `RoleGraph` with 4 core dimensions × 4 subskills. Each subskill carries `key`, `label`, `dimension`, `target_proficiency`, and optional `prerequisites`. Stage allocation and gap profiling operate over this graph.

**Rationale**: The graph shape lets stage allocation pick distinct targets across dimensions, lets the gap-profile builder rank priority by gap size, and lets the roadmap signal expose prerequisite links. Flat question banks cannot support any of this deterministically.

**Alternatives considered**:

- Store questions directly on roles and skip the graph: rejected because it removes the ability to target stage two and produce roadmap-ready gap data.
- Load role content from an external registry at runtime: rejected as unnecessary runtime surface for the MVP. A single Python module is the simplest safe handoff.

## Decision 6: Make `role_graph_data.py` the single curated-content handoff file

**Decision**: All curated role content lives in `Backend/apps/assessments/role_graph_data.py`, behind a single `ROLE_GRAPHS` mapping and a `CURATED_VERSION` string. Replacing curated content is a one-file change.

**Rationale**: Curated content is owned by a different partner from the runtime code. A single stable handoff file lets infrastructure and content evolve in parallel without either team blocking the other, and makes the handoff easy to review.

**Alternatives considered**:

- Keep curated content in JSON or YAML files under `data/`: rejected because it forces a runtime loader + schema validator for no practical benefit while role count is small.
- Split curated content across one file per role: rejected because it multiplies merge-conflict surface and makes the handoff contract harder to enforce.

## Decision 7: Validate role graphs at load time with explicit failures

**Decision**: The role-graph loader rejects graphs that are missing dimensions, have subskill counts or weights out of range, or reference unknown prerequisites. Invalid content is a loud failure, not a silent downgrade.

**Rationale**: Silent fallback on invalid curated data would hide bad content behind runtime behavior, and stage targeting plus roadmap signals would quietly drift. Loud failure surfaces the problem at the earliest possible point.

**Alternatives considered**:

- Tolerate malformed graphs and fall back to defaults: rejected because it degrades the assessment invisibly.
- Validate only in tests, not at load time: rejected because it can't catch curated-content breakage in staging or production.

## Decision 8: Bind stage-one cache keys to `{role_key, CURATED_VERSION}`

**Decision**: Stage-one generated questions are cached per `(role_key, CURATED_VERSION)` pair. Bumping `CURATED_VERSION` invalidates cached stage-one output automatically.

**Rationale**: Curated content changes the semantic meaning of stage-one questions even when the role key is stable. Without a version-bound key, users would keep receiving stage-one questions generated against old graph content after an update.

**Alternatives considered**:

- Use `role_key` alone as the cache key: rejected because semantic updates would go unnoticed.
- Disable caching and regenerate every time: rejected because it burns the stage-one call budget without improving output quality.

## Decision 9: Emit a structured `roadmap_signal` for downstream consumers

**Decision**: Completed staged assessments expose a typed `RoadmapSignal` with sub-skill evidence, ordered priorities, prerequisite links, and confidence metadata. The roadmap module prefers this signal when generating a roadmap, and falls back to legacy score-based inputs only for pre-migration assessments.

**Rationale**: The entire purpose of staging the assessment is to produce stronger roadmap-ready input. Leaving the roadmap module to re-derive gaps from prose or raw scores would undo the benefit.

**Alternatives considered**:

- Keep the existing broad-score output and let roadmaps recompute gaps: rejected because it duplicates work and keeps roadmap quality unchanged.
- Make `roadmap_signal` an optional bolt-on rather than the preferred input: rejected because the roadmap module would keep relying on the weaker signal in practice.

## Decision 10: Ship a typed frontend `AssessmentSubmissionState` union before API changes

**Decision**: The frontend `AssessmentSubmissionState` union in `Frontend/src/lib/api.ts` is defined alongside the staged API contract and must stay in sync with backend payloads. Contract tests exercise the payload shape end to end.

**Rationale**: The frontend assessment flow depends on unambiguous stage transitions. Letting the frontend types catch up later would knowingly normalize contract drift and produce ambiguous UI states during rollout.

**Alternatives considered**:

- Reuse untyped `status` strings on the frontend: rejected because the stage transitions are the feature, not a side effect.
- Defer the frontend contract until after backend stabilization: rejected because it produces shipping gaps where the frontend cannot render the staged flow correctly.

## Decision 11: Preserve legacy non-staged assessments

**Decision**: The staged behavior is gated by an `is_staged` check on the assessment record. Pre-migration assessments continue to complete and render through their original flow, and the roadmap module keeps its legacy fallback for those records.

**Rationale**: Rolling out the staged flow must not block users whose assessments were created before the migration. The compatibility path is small and avoids a data migration.

**Alternatives considered**:

- Force-migrate legacy assessments: rejected because it rewrites historical user data and creates extra failure surface with no product benefit.
- Drop legacy assessments entirely: rejected for the same reason.

## Decision 12: No unresolved planning clarifications remain

**Decision**: The plan can proceed without marking any remaining `NEEDS CLARIFICATION` items.

**Rationale**: The feature spec, ADR-001, role-graph shape, cache and budget decisions, staged API contract, and roadmap-signal contract together fully specify the work. Any remaining questions are implementation details covered by the task breakdown.
