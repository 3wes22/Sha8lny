# Feature Specification: Two-Stage Adaptive Assessment Question Generation

**Feature Branch**: `[002-ai-rag-experiment]`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "Finish question generation phase by replacing the current flat per-role assessment bank with a two-stage adaptive skills assessment that produces stronger roadmap-ready signals under tight compute and budget constraints, while decoupling infrastructure work from curated role graph content through a single handoff file."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive targeted follow-up questions after an initial calibration (Priority: P1)

As a learner choosing a target role, I want the assessment to start with a short broad calibration and then continue with targeted follow-up questions so the system can measure my level more accurately without making me answer a long generic questionnaire.

**Why this priority**: The feature only delivers value if question generation becomes more adaptive and produces a stronger assessment signal than the current flat six-question bank.

**Independent Test**: Can be fully tested by creating a new skills assessment for a supported role, completing the first stage, observing targeted second-stage questions, and confirming the full assessment completes without manual intervention.

**Acceptance Scenarios**:

1. **Given** a user starts a new skills assessment for a supported role, **When** the assessment is prepared, **Then** the system presents an initial calibration stage with questions aligned to that role.
2. **Given** a user completes the calibration stage, **When** their first-stage answers are processed, **Then** the system presents a second stage targeted at weak or uncertain skill areas rather than repeating the same broad question set for all users.

---

### User Story 2 - Produce roadmap-ready capability data instead of only broad scores (Priority: P2)

As a roadmap generation workflow, I want assessment results to include structured gap data for subskills, priorities, prerequisites, and confidence so I can generate personalized learning paths without reinterpreting raw answers each time.

**Why this priority**: The assessment phase exists to improve downstream roadmap quality. If the output remains only broad scores and prose, the roadmap engine still lacks precise input.

**Independent Test**: Can be fully tested by completing a new staged assessment and verifying that the final result exposes structured skill-gap data that can be consumed directly by the roadmap module.

**Acceptance Scenarios**:

1. **Given** a completed staged skills assessment, **When** the result is requested, **Then** the response includes structured subskill evidence, ordered priorities, prerequisite links, and confidence metadata.
2. **Given** the roadmap module receives the completed assessment result, **When** it inspects the assessment output, **Then** it can identify the highest-priority gaps without needing to infer them from free-form notes.

---

### User Story 3 - Evolve role content independently from workflow code (Priority: P3)

As a teammate curating role-specific skill data, I want to update the role graph in one dedicated location using a stable contract so infrastructure work can proceed now and curated content can drop in later without refactoring the rest of the feature.

**Why this priority**: The delivery plan depends on parallel work. If the workflow is tightly coupled to unfinished curated data, the whole feature stalls.

**Independent Test**: Can be tested by using structurally valid stub role data during implementation, then replacing that data with curated content in the single handoff file and confirming the assessment flow continues to work without code changes elsewhere.

**Acceptance Scenarios**:

1. **Given** the system is implemented against stub role graph entries, **When** curated data replaces the stub entries in the handoff file, **Then** the staged assessment flow continues to work without touching other source files.
2. **Given** a role graph entry is invalid or incomplete, **When** the system loads it, **Then** the failure is explicit and does not silently produce broken assessment behavior.

### Edge Cases

- What happens when the second-stage question generation fails after the user completes the first stage?
- How does the system behave for supported roles whose curated graph content has not yet replaced the stub data?
- What happens when a user has an assessment created before this migration and returns after the new staged flow ships?
- How does the system behave when the cache is unavailable or a stage-one cache entry is stale after a role-graph version change?
- What happens when a user abandons the process after stage one and later resumes the same assessment?

### Data & Privacy Considerations

- The feature processes personal assessment responses, target-career choices, derived skill-gap data, and metadata about model-backed generation; those inputs and derived outputs must remain scoped to the authenticated user.
- The feature continues to rely on local Gemma via Ollama for bounded question generation, with deterministic fallback behavior when the model is unavailable or returns invalid output.
- The feature must not introduce hard-coded credentials; cache, queue, and model configuration remain environment-driven.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the current single flat skills-assessment question flow for new assessments with a staged flow that includes an initial calibration stage followed by a targeted follow-up stage.
- **FR-002**: System MUST support the staged flow for the initial supported roles already recognized by the product: backend, frontend, data science, fullstack, mobile, and devops.
- **FR-003**: System MUST generate first-stage questions from role-specific assessment context and use the user’s first-stage responses to choose second-stage focus areas.
- **FR-004**: System MUST keep assessment output structured enough to describe subskill evidence, confidence, priority order, prerequisite links, and a roadmap-ready summary.
- **FR-005**: System MUST preserve a deterministic fallback path for question generation and final evaluation so the assessment can complete even if model-backed generation fails.
- **FR-006**: System MUST expose clear stage, readiness, processing, failure, and completion states through the assessment API so the frontend can present the flow without guessing state.
- **FR-007**: System MUST allow role-graph data to be maintained behind a single stable loader interface so curated content can replace stub content without refactoring the assessment engine, tasks, serializers, or frontend integration.
- **FR-008**: System MUST retain compatibility for legacy in-progress or historical assessments created before the staged rollout so existing users are not blocked from completing or viewing them.
- **FR-009**: System MUST limit the assessment workflow to a maximum of 3 LLM calls per completed staged assessment: Stage 1 generation (call 1), Stage 2 generation (call 2), and final evaluation (call 3).
- **FR-010**: System MUST define affected API contracts, validation rules, frontend types, cache behavior, and roadmap-consumer expectations before implementation begins.
- **FR-011**: System MUST log or expose enough metadata to distinguish cache hits, fallback usage, generation failures, and final staged assessment completion.
- **FR-012**: System MUST define automated verification for assessment state transitions, deterministic scoring behavior, cache behavior, staged frontend integration, and roadmap-ready output generation.

### Key Entities *(include if feature involves data)*

- **Role Graph**: The role-specific capability map that defines core dimensions, subskills, target proficiency, and prerequisite relationships for a supported role.
- **Stage Question**: A question bound to a stage, role context, dimension, and subskill target that the user answers during the assessment flow.
- **Gap Profile**: The intermediate analysis built after stage one that identifies high-priority gaps, uncertain areas, and overall calibration strength.
- **Roadmap Signal**: The structured final capability output that the roadmap module uses to prioritize learning work.
- **Staged Assessment Session**: The evolving assessment record that tracks current stage, generated questions, submitted responses, generation metadata, and final result readiness.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Staged progression must pass for all supported roles (6/6), Stage 1 must always return exactly 5 questions, and the API must transition through states: pending → stage_1_complete → stage_2_complete.
- **SC-002**: Completed staged assessments expose structured roadmap-ready gap data for every supported role instead of only broad summary scores.
- **SC-003**: The assessment workflow records no more than 3 LLM invocations per completed staged assessment: Stage 1 generation (call 1), Stage 2 generation (call 2), and final evaluation (call 3).
- **SC-004**: If model-backed generation fails at any stage, users still receive a valid assessment flow and final result through the documented fallback path.
- **SC-005**: Replacing stub role-graph content with curated content requires changes in only the designated role-graph data file and no other feature files.
- **SC-006**: Regression coverage is updated for the staged assessment lifecycle, cache behavior, deterministic gap scoring, and frontend stage transitions.

## Assumptions

- Initial delivery scope is limited to the `skills` assessment type; other assessment types remain on their existing flow until a later feature extends them.
- The existing assessment and roadmap modules remain the product surfaces for this work; no separate runtime service is introduced.
- Legacy assessments created before the migration continue to be readable and completable during rollout.
- The current local Gemma architecture remains the AI runtime, with model choice controlled by environment configuration rather than a hard-coded feature-specific dependency.
