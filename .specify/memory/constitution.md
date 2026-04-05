<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Added I. Modular Monolith Boundaries
- Added II. Contract-First Interfaces
- Added III. Testable Business Logic
- Added IV. Responsible AI & Data Protection
- Added V. Operational Visibility & Simplicity
Added sections:
- Delivery Constraints
- Workflow & Quality Gates
Removed sections:
- None
Templates requiring updates:
- ✅ updated .specify/templates/plan-template.md
- ✅ updated .specify/templates/spec-template.md
- ✅ updated .specify/templates/tasks-template.md
- ⚠ pending .specify/templates/commands/*.md (directory not present in this repository)
Follow-up TODOs:
- None
-->
# Sha8lny Constitution

## Core Principles

### I. Modular Monolith Boundaries
All product changes MUST preserve the repository's modular-monolith architecture.
Backend capabilities MUST live in the appropriate Django app under `Backend/apps/`,
shared behavior MUST be promoted only when at least two modules require it, and
cross-module coupling MUST occur through explicit services, serializers, or model
contracts rather than ad hoc duplication. Frontend work MUST keep page-level flows,
reusable components, and API access separated so features remain independently
maintainable.

Rationale: The project already relies on clear module ownership across backend,
frontend, and AI layers. Preserving those boundaries keeps the graduation project
deliverable coherent while avoiding premature microservice complexity.

### II. Contract-First Interfaces
Every externally visible behavior MUST be specified as a user story plus measurable
acceptance criteria before implementation. API changes MUST define request and
response shapes, affected routes, validation rules, and typed frontend integration
points. Schema, payload, or prompt-contract changes MUST be reflected in the
relevant spec, plan, and task artifacts before implementation begins.

Rationale: Sha8lny spans Django APIs, a typed React frontend, and AI-assisted flows.
Contract drift is one of the fastest ways to break integration across those layers.

### III. Testable Business Logic
Changes to business logic MUST include automated verification at the layer where the
behavior lives. Backend features MUST add or update pytest coverage for services,
models, or APIs that changed. Frontend behavioral changes MUST add automated tests
when a test harness exists; where it does not, the plan MUST record the required
build verification and manual acceptance path. Critical paths involving
authentication, data integrity, assessment scoring, or roadmap generation MUST not
ship without regression coverage. The team SHOULD maintain at least 80% coverage for
business logic and treat gaps in critical paths as release blockers.

Rationale: The repository already treats testing as a quality baseline. Making it a
constitutional rule prevents feature delivery from outrunning verification.

### IV. Responsible AI & Data Protection
AI-assisted features MUST document their model dependency, fallback behavior, user
data inputs, and cost/privacy constraints before implementation. Features handling
personal, assessment, or career data MUST minimize stored sensitive data, avoid
hard-coding secrets, and use environment-based configuration for credentials and
provider access. Any feature that can operate with a local or deterministic fallback
SHOULD define that fallback explicitly for demo and degraded-mode operation.

Rationale: Sha8lny processes sensitive user profile and assessment information while
mixing local and hosted AI options. Governance must keep privacy and operational
costs explicit.

### V. Operational Visibility & Simplicity
New backend workflows MUST emit structured logs at critical failure and state-change
points, and plans MUST identify monitoring or debugging signals needed for rollout.
Every proposal MUST prefer the simplest design that satisfies current MVP needs;
additional infrastructure, abstractions, or services require written justification in
the implementation plan. Features that add background jobs, external integrations, or
asynchronous processing MUST define error handling and recovery behavior.

Rationale: MVP delivery depends on being able to diagnose failures quickly without
accumulating architecture that the team cannot operate confidently.

## Delivery Constraints

- Primary stack decisions are fixed unless a plan explicitly justifies deviation:
  Django REST Framework for backend APIs, React + TypeScript for frontend, and
  PostgreSQL-oriented data modeling with SQLite acceptable only for local
  development.
- All credentials, provider keys, and environment-specific endpoints MUST be sourced
  from environment configuration and MUST NOT be committed to the repository.
- User-facing flows MUST remain deployable as thin vertical slices: each prioritized
  user story must have an independent test path and a clear MVP value statement.
- Changes affecting AI models, scraped job data, or external content sources MUST
  document refresh assumptions, failure modes, and local/demo-safe operation.

## Workflow & Quality Gates

1. Specification gate: `spec.md` MUST define prioritized user stories, measurable
   acceptance scenarios, edge cases, functional requirements, and any data/privacy
   implications before planning starts.
2. Planning gate: `plan.md` MUST pass the Constitution Check by confirming module
   ownership, interface contracts, required tests, AI/data protections, and
   observability expectations before implementation tasks are generated.
3. Task gate: `tasks.md` MUST map work to user stories, include verification tasks
   for changed behavior, and surface logging, security, or integration work when the
   feature requires it.
4. Implementation gate: contributors MUST update tests and validation steps in the
   same change set as the feature unless the plan explicitly documents a temporary,
   approved gap.
5. Review gate: pull requests and internal reviews MUST verify constitutional
   compliance, especially around modular boundaries, privacy handling, and regression
   coverage.

## Governance

This constitution overrides conflicting local planning habits for all work created
through the spec-kit flow in this repository.

- Amendments MUST be documented in `.specify/memory/constitution.md` and include an
  updated Sync Impact Report describing downstream template changes.
- Versioning policy follows semantic versioning for governance:
  MAJOR for incompatible principle removals or redefinitions, MINOR for new
  principles or materially expanded guidance, PATCH for clarifications that do not
  change expected behavior.
- Compliance review is mandatory during planning, task generation, implementation,
  and review. Any exception MUST be recorded in `plan.md` under Complexity Tracking
  with a concrete justification and a simpler rejected alternative.
- If a template or guidance file diverges from this constitution, the constitution is
  authoritative and the dependent artifact MUST be updated promptly.

**Version**: 1.0.0 | **Ratified**: 2026-04-04 | **Last Amended**: 2026-04-04
