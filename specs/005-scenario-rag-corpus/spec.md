# Feature Specification: Scenario RAG Corpus for Staged Assessment Question Generation

**Feature Branch**: `005-scenario-rag-corpus`
**Created**: 2026-05-17
**Status**: Draft
**Input**: User description: "Augment staged assessment question generation with a role-aware, schema-aligned scenario corpus retrieved per blueprint from a local vector store, layered on top of the existing static few-shot block, without replacing the deterministic fallback path."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stronger generated questions for every supported role (Priority: P1)

As a learner taking a staged skills assessment for any approved role, I want the generated questions to feel concretely on-topic for my role and subskill so the assessment evidence reflects my actual judgment rather than generic engineering trivia.

**Why this priority**: This is the user-visible payoff. Today the assistant grounds every staged generation only on three inline format examples plus a handful of curated backend fallback scenarios. Frontend, data science, full stack, Android, ML engineer, UI/UX designer, and DevOps assessments fall back to label-templated generic stems whenever the model wavers. The corpus removes that asymmetry across all eight first-class roles.

**Independent Test**: Start a fresh `skills` assessment for `Frontend Developer`, complete stage one, and confirm every generated question begins with a concrete frontend scenario that names a real artifact (component, render, route, fetch, layout) instead of an abstract "engineering decision" stem.

**Acceptance Scenarios**:

1. **Given** a corpus that contains approved scenarios for the learner's role and subskill mix, **When** stage one or stage two is generated, **Then** every produced question begins with a concrete role-appropriate scenario and matches the same schema the platform produces today.
2. **Given** a corpus that contains no approved scenarios for the learner's role, **When** generation runs, **Then** the system still produces a complete, valid staged assessment using the existing static format examples and the deterministic contract-safe fallback, with no broken or partial questions.

---

### User Story 2 - Zero new operational risk during rollout (Priority: P1)

As the team owning the staged assessment runtime, I want the corpus to be enableable per environment, reversible by a single configuration flip, and incapable of breaking generation when the vector store is missing, empty, or unavailable so I can ship and roll back without coordination.

**Why this priority**: The staged flow is a demo-critical path. The hard guarantee that every Gemma call has a deterministic fallback (existing project decision) must hold after this change.

**Independent Test**: Disable the feature in configuration, run the full staged assessment test suite, and confirm prompts, outputs, and cache keys are byte-identical to the pre-change behavior. Re-enable the feature with the vector store directory deleted, run again, and confirm assessments still complete with a single warning log per generation.

**Acceptance Scenarios**:

1. **Given** the feature flag is disabled, **When** stage one or stage two is generated, **Then** the produced prompt, the resulting question payload, and the stage cache key are unchanged from the current behavior.
2. **Given** the feature flag is enabled but the vector store is unreachable or empty, **When** generation runs, **Then** the system logs one warning, continues with the existing static format examples, and still produces a valid staged assessment.
3. **Given** the feature flag is enabled and the corpus is populated, **When** the corpus version is bumped, **Then** stage one cached questions for affected roles are treated as stale and regenerated on next request.

---

### User Story 3 - Authoring loop that prevents corpus quality regressions (Priority: P2)

As the contributor authoring or updating scenarios, I want every scenario to be mechanically validated against the same contract the live assessment enforces, and I want a coverage report that tells me which role × subskill × stage × question-type cells are still missing, so the corpus cannot silently drift below the quality bar set by the existing curated backend scenarios.

**Why this priority**: Corpus quality is the only thing that justifies retrieval. Without an enforced validator and a coverage gate, the corpus will drift toward the lowest-quality contributed entry and degrade generation quality instead of improving it.

**Independent Test**: Add a scenario that violates the contract (for example a multi-select item with only one correct option), run the audit, and confirm the change is rejected with a precise reason. Remove all scenarios for one role and one question type, run the audit, and confirm the missing coverage cell is reported.

**Acceptance Scenarios**:

1. **Given** a proposed new scenario that violates the live question-contract rules, **When** the corpus audit runs, **Then** the audit reports the violation and refuses to mark the scenario as approved.
2. **Given** any role × stage × question-type cell falls below the documented coverage floor, **When** the corpus audit runs, **Then** the audit reports the gap and returns a non-zero status so it can fail continuous integration.

---

### Edge Cases

- What happens when the vector store contains stale documents from a previous corpus version? Documents from a prior version must not be returned at retrieval time, and the audit must surface the version drift so it can be rebuilt cleanly.
- What happens when retrieval returns the same scenario for multiple blueprint slots in a single generation? Only one copy of each retrieved scenario is included in the prompt to avoid wasting context and prompting repetition.
- What happens when a contributor authors a scenario whose `role_key` or `subskill_key` no longer exists in the curated role graph? The audit must reject the scenario at validation time, not at retrieval time, so dead references never reach generation.
- What happens for a legacy `target_career` value that resolves to a supported role but has no role-specific scenarios yet? Generation falls through to the existing static format examples and deterministic fallback path without raising an error.
- What happens when two scenarios for the same role, subskill, and question type are near-duplicates? The audit flags the pair so authors can differentiate or remove one before it dilutes retrieval diversity.

### Data & Privacy Considerations

- The corpus contains only authored educational scenarios. No learner-submitted answers, profile data, or personally identifiable information is ever ingested, embedded, or stored in the vector store.
- The retrieval step adds no new outbound network dependency: embedding and vector search both run inside the existing backend process using locally hosted assets. No new external provider is introduced and no learner data leaves the backend during retrieval.
- The feature does not change how AI-generated questions are produced, scored, or stored downstream; it only enriches the prompt context. Existing fallback guarantees remain unchanged.
- No new secrets, credentials, or third-party API keys are required.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST treat the scenario corpus as an additive prompt-enrichment layer that runs after the existing static format examples and never replaces the deterministic contract-safe fallback path.
- **FR-002**: System MUST allow the corpus to be enabled or disabled per environment by a single configuration switch, with `disabled` as the default after this feature lands and behavior identical to pre-feature behavior when disabled.
- **FR-003**: System MUST tolerate a missing, empty, unreachable, or corrupt vector store at generation time by logging a single warning and continuing with the existing static format examples; generation MUST NOT fail because retrieval failed.
- **FR-004**: System MUST filter retrieved scenarios at minimum by `role_key`, `question_type`, and `stage` so a retrieved example is always shaped for the slot the assistant is being asked to produce.
- **FR-005**: System MUST cap the number of retrieved scenarios injected into any single generation prompt so prompt size stays predictable and within the existing model context budget.
- **FR-006**: System MUST deduplicate retrieved scenarios within a single generation prompt so the same scenario never appears in more than one few-shot slot of the same call.
- **FR-007**: System MUST version the corpus with a single explicit version identifier and MUST invalidate any cached stage-one questions whose generation predates a version bump, the same way the existing curated role graph version invalidates them today.
- **FR-008**: System MUST validate every scenario against the same question-contract rules used at generation time before that scenario becomes retrievable, and MUST reject scenarios that fail validation.
- **FR-009**: System MUST reject scenarios whose `role_key` or `subskill_key` does not exist in the approved curated role graph, so the corpus cannot drift away from the canonical role inventory.
- **FR-010**: System MUST provide an authoring report that lists, per role and per stage and per question type, how many approved scenarios exist and which coverage cells fall below the documented floor; the report MUST return a non-zero status when any cell is below the floor so continuous integration can fail on gaps.
- **FR-011**: System MUST surface a near-duplicate detector that flags scenarios within the same role, subskill, and question type whose retrievable representations are too similar to add diversity value.
- **FR-012**: System MUST keep all curated authored scenarios in version control as the source of truth, with the vector store treated as a derived index that can be rebuilt at any time without losing curated content.
- **FR-013**: System MUST keep authored scenarios separate from the existing deterministic fallback dictionary used by the contract-safe path so changes to the corpus cannot regress the failure-mode safety net.
- **FR-014**: System MUST instrument retrieval with structured logging that records, per generation, which role, subskill, stage, and question type triggered retrieval and whether any scenarios were returned, so the team can observe hit-rate and roll back early if retrieval starts harming generation quality.

### Key Entities

- **Authored Scenario**: A reviewed, approved educational scenario containing the role key, subskill key, stage, question type, scenario context, question stem, options or expected concepts depending on question type, answer key, per-option rationales, and provenance fields such as author, license, and review status. Source of truth lives in version control.
- **Corpus Version**: A single short identifier that names the currently published set of approved scenarios. Bumping the identifier invalidates dependent caches and signals that the derived vector index must be rebuilt.
- **Vector Index**: A derived, rebuildable representation of approved scenarios stored locally that the generation runtime queries at prompt-build time. It carries no source of truth on its own; the authored scenarios in version control do.
- **Coverage Cell**: A logical bucket defined by the tuple of role, stage, and question type. Each cell has a documented minimum scenario count that the corpus audit enforces.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After rollout, the proportion of staged generations that fall back to the deterministic contract-safe questions for any reason does not increase relative to the pre-rollout baseline, measured over a representative one-week window per environment.
- **SC-002**: For every approved role, every supported stage, and every supported question type, retrieval returns at least one role-correct scenario for any blueprint produced by current allocation logic, verified by the smoke-retrieval test, once that role's coverage cells reach the documented floor.
- **SC-003**: Disabling the feature flag returns prompt content, generation output, and cache keys to a byte-identical match with pre-feature behavior, verified by a contract-style integration test that the team can re-run on demand.
- **SC-004**: The corpus audit fails any change set that introduces a contract-invalid scenario or that drops any coverage cell below the documented floor, with no manual review required to catch such regressions.
- **SC-005**: Rollback to the pre-feature behavior in any environment requires only a single configuration change and no code revert, data migration, or cache surgery.

## Assumptions

- The approved role inventory remains the eight first-class roles already enumerated by the curated role graph after the 004 baseline expansion (`backend`, `frontend`, `fullstack`, `data_science`, `devops`, `android`, `machine_learning_engineer`, `ui_ux_designer`). Any role beyond that set is out of scope for v1.
- The current staged generation prompt contract, including the required output schema and the deterministic contract-safe fallback dictionary, remains the canonical baseline. This feature must not loosen, replace, or rewrite either of those.
- The runtime continues to be the existing modular Django backend; no new microservice, no new outbound API dependency, and no new managed vector store is introduced by this feature.
- Existing AI runtime settings (chroma persist location, embedding model name) live in the existing backend settings module; this feature extends that module with a small number of new scenario-specific settings rather than creating a parallel settings system.
- The embedding model used for retrieval is the same locally hosted sentence-transformer family already referenced by the project's RAG support package; this feature does not introduce a new model.
- Bulk-imported third-party question content (such as quiz-style banks) may be used as authoring source material but is never auto-promoted into the corpus; only authored, validated, and approved scenarios enter the retrievable corpus.
- Authoring throughput is governed by humans, not by this feature. The corpus is expected to grow role by role and to ship in waves; the wiring must work correctly with a partially populated corpus.
- Per-user personalization of retrieval, LLM-based reranking, and any change to the three-LLM-call-per-assessment ceiling are explicitly out of scope for v1.
