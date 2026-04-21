# Feature Specification: Assessment Role Baseline Expansion

**Feature Branch**: `[004-assessment-role-expansion]`  
**Created**: 2026-04-21  
**Status**: Draft  
**Input**: User description: "Expand the staged assessment baseline beyond six roles without breaking legacy assessments, while keeping the runtime role graph contract curated and explicit."

## User Scenarios & Testing

### User Story 1 - Start staged assessments for the broader product role catalog (Priority: P1)

As a learner choosing a target role, I want the assessment picker and backend role resolution to support the same tech-role catalog already exposed by the product so I am not silently routed into the wrong assessment graph.

**Why this priority**: The current product already exposes more roadmap roles than the assessment layer supports, creating a mismatch between user intent and staged assessment behavior.

**Independent Test**: Start new `skills` assessments for `Android Developer`, `Machine Learning Engineer`, and `UI/UX Designer`, and confirm each one resolves to its own first-class staged assessment graph.

**Acceptance Scenarios**:

1. **Given** a user starts a `skills` assessment for `Android Developer`, **When** the assessment is created, **Then** the staged flow resolves to the `android` role graph instead of the old `mobile` role key.
2. **Given** a user starts a `skills` assessment for `Machine Learning Engineer` or `UI/UX Designer`, **When** the assessment is created, **Then** the staged flow resolves to `machine_learning_engineer` or `ui_ux_designer` respectively and returns valid staged questions.

### User Story 2 - Preserve legacy compatibility while expanding role support (Priority: P1)

As a maintainer shipping the broader role baseline, I want legacy freeform target-career inputs and historical assessments to remain readable and completable so role expansion does not silently rewrite older assessment meaning.

**Why this priority**: Broadening role resolution can break legacy cache semantics, stored results, and historical completion guarantees if old aliases are re-routed too aggressively.

**Independent Test**: Create or simulate assessments using legacy titles such as `Machine Learning`, `ML`, and `Mobile Developer`, and confirm they still resolve to the intended compatibility role keys after the expansion.

**Acceptance Scenarios**:

1. **Given** a legacy target career containing `machine learning` or `ml`, **When** role resolution runs, **Then** it continues to resolve to `data_science` instead of silently switching to `machine_learning_engineer`.
2. **Given** a legacy target career containing `Mobile Developer`, `Android Developer`, or `iOS`, **When** role resolution runs, **Then** it resolves to `android`, while historical results remain readable without data migration.

### User Story 3 - Keep curated runtime role graphs explicit and cache-safe (Priority: P2)

As a teammate responsible for runtime behavior, I want the approved assessment baseline to stay curated in the runtime dataclass format so new roles can be added without coupling the staged engine to mined raw inventory files.

**Why this priority**: The staged assessment runtime depends on deterministic graph structure, version-bound caches, and explicit validation. Raw mined inventory is useful input, but it is not a safe runtime contract.

**Independent Test**: Load every approved role graph through `load_role_graph(...)`, verify cache invalidation happens on `CURATED_VERSION` changes, and confirm missing approved roles fail explicitly.

**Acceptance Scenarios**:

1. **Given** the approved eight-role baseline, **When** loader validation runs, **Then** all eight curated runtime graphs load successfully and any missing graph raises an explicit validation error.
2. **Given** `CURATED_VERSION` changes, **When** stage-one generation runs again, **Then** previously cached stage-one questions are invalidated for all affected roles as expected.

### Edge Cases

- What happens when the approved runtime role inventory changes before the new graphs exist?
- How does the system handle historical assessments whose stored metadata still references `mobile` or pre-expansion recommendation payloads?
- What happens when a user enters a freeform title such as `Machine Learning` that is related to, but not identical to, a new first-class role?
- How does the system behave when the frontend picker label is valid product copy but the backend alias mapping drifts from it?

## Requirements

### Functional Requirements

- **FR-001**: System MUST expand the staged assessment runtime baseline from six to eight first-class supported roles: `backend`, `frontend`, `fullstack`, `data_science`, `devops`, `android`, `machine_learning_engineer`, and `ui_ux_designer`.
- **FR-002**: System MUST add curated runtime role graphs for `android`, `machine_learning_engineer`, and `ui_ux_designer` before flipping the supported-role inventory.
- **FR-003**: System MUST keep the runtime role-graph contract in `Backend/apps/assessments/role_graph_data.py`; mined inventory from `origin/feature/skill-graph` remains offline input only.
- **FR-004**: System MUST keep the current staged graph shape for this wave: exactly 4 dimensions and exactly 4 subskills per dimension for every approved runtime role.
- **FR-005**: System MUST preserve legacy compatibility by keeping generic `machine learning` and `ml` aliases mapped to `data_science`, and generic `ui` mapped to `frontend`.
- **FR-006**: System MUST resolve `Android Developer`, `Android`, `Mobile Developer`, `mobile`, and `iOS` to `android`, while treating `mobile` as alias-only rather than a first-class runtime role key.
- **FR-007**: System MUST update adjacent-career and learning-path heuristics to operate on resolved role keys rather than fragile raw substring branches.
- **FR-008**: System MUST keep the API contract unchanged for this wave: `target_career` remains a string input and no historical assessment JSON is migrated.
- **FR-009**: System MUST bump `CURATED_VERSION` when the expanded baseline lands and treat the resulting global stage-one cache miss as expected invalidation, not a regression.
- **FR-010**: System MUST align the assessment frontend picker with the approved product-facing role labels so every picker label resolves to an approved runtime role key.

### Key Entities

- **Approved Runtime Role**: A first-class assessment role key that must exist in `SUPPORTED_ROLES` and in the curated `ROLE_GRAPHS` mapping.
- **Legacy Alias**: A freeform `target_career` label that remains accepted for compatibility but resolves to one of the approved runtime role keys.
- **Offline Candidate Inventory**: The mined role and skill inventory from `origin/feature/skill-graph`, used as authoring input rather than runtime truth.

## Success Criteria

- **SC-001**: Loader validation passes for all eight approved runtime roles and fails explicitly if any approved role graph is missing.
- **SC-002**: New staged assessments for `Android Developer`, `Machine Learning Engineer`, and `UI/UX Designer` complete successfully and emit their own first-class runtime role keys.
- **SC-003**: Legacy alias resolution remains stable for `Machine Learning`, `ML`, and `Mobile Developer` according to the documented compatibility rules.
- **SC-004**: Frontend assessment picker labels all resolve to approved runtime role keys and no longer expose the old six-role-only catalog.
- **SC-005**: Cache invalidation tests prove that bumping `CURATED_VERSION` invalidates stage-one cache entries as expected after the baseline expansion.

## Assumptions

- This wave intentionally creates a new spec track under `specs/004-assessment-role-expansion/` rather than editing completed 002 task history in place.
- The runtime team now owns reducing partner/mined inventory into assessment-grade curated runtime graphs for the three new roles.
- Per-role versioning, historical JSON backfills, and broader non-tech role expansion are out of scope for this wave.
