# Research: Two-Stage Adaptive Assessment Question Generation

## Sources Reviewed

- `/Users/mohamed3wes/Downloads/Grad-Project/specs/002-ai-rag-experiment/spec.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/.specify/memory/constitution.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/docs/product/ADR-001-LOCAL-GEMMA-ARCHITECTURE.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/docs/product/GEMMA_ARCHITECTURE_ADOPTION_PLAN.md`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/models.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/views.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/tasks.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/assessments/ai_pipeline.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/core/ai_contracts.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/apps/core/ai_settings.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/config/settings/base.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Backend/config/settings/development.py`
- `/Users/mohamed3wes/Downloads/Grad-Project/Frontend/src/lib/api.ts`

## Decision 1: Build against a role-graph loader contract with stub data

**Decision**: Introduce a dedicated role-graph contract module plus a single loader entry point and keep all initial content in a stub data file that can later be replaced by curated entries.

**Rationale**: The feature depends on role-specific skill structure, but curated content is being prepared separately. A loader contract unblocks engine, task, serializer, and frontend work immediately while keeping future handoff isolated to one file.

**Alternatives considered**:

- Hard-code role structures inside the assessment engine: rejected because it couples workflow code to unfinished content.
- Delay planning until curated role data is complete: rejected because it blocks unrelated infrastructure work.

## Decision 2: Keep production orchestration in `Backend/` and treat `ai-models/` as support only

**Decision**: All production assessment orchestration, validation, persistence, tasks, and API contracts remain in `Backend/apps/assessments/` and `Backend/apps/core/`.

**Rationale**: The accepted architecture documents already define `Backend/` as the production runtime and `ai-models/` as support code for experiments and offline work. This keeps module ownership explicit and avoids reviving a second runtime path.

**Alternatives considered**:

- Put staged generation logic into `ai-models/` and call it from Django: rejected because it creates an unnecessary runtime split.
- Split assessment generation into a new service: rejected because it violates the simplicity and modular-monolith rules for current scope.

## Decision 3: Ship the first version for `skills` assessments only

**Decision**: Limit the staged rollout to the `skills` assessment type and keep other assessment types on their current behavior.

**Rationale**: The current roadmap dependency and quality goals are tied to skills assessment. Expanding to interests, personality, and learning-style flows now would multiply state, prompt, and scoring complexity before the core path is reliable.

**Alternatives considered**:

- Build a generic engine for all assessment types immediately: rejected because it increases scope and weakens focus on roadmap quality.
- Keep the current flat skills flow until all assessment types are redesigned together: rejected because it delays the most valuable improvement.

## Decision 4: Use a two-stage adaptive flow with exactly two bounded model-backed generation calls

**Decision**: New staged assessments use five calibration questions in stage one and five targeted follow-up questions in stage two, with one bounded generation call per stage.

**Rationale**: This matches the user’s desired assessment shape, preserves low compute cost, and creates room for deterministic analysis between stages without introducing a slow per-question loop.

**Alternatives considered**:

- Keep the current flat six-question set: rejected because it does not produce enough signal for roadmap quality.
- Generate questions one-by-one adaptively: rejected because repeated model latency and orchestration complexity exceed current hardware and budget constraints.

## Decision 5: Let deterministic scoring own the mid-stage decision point

**Decision**: The transition from stage one to stage two is driven by deterministic scoring, confidence calculation, and priority ranking, not by another free-form model decision.

**Rationale**: The architecture goal is to avoid a thin LLM wrapper. Deterministic allocation between stages makes the system explainable, testable, and stable under limited compute.

**Alternatives considered**:

- Let the model decide which subskills to probe next: rejected because the reasoning becomes harder to test and cheaper fallbacks become weaker.
- Predefine the same stage-two questions for everyone: rejected because it loses the value of adaptive targeting.

## Decision 6: Preserve legacy assessments during rollout

**Decision**: Keep the old single-stage assessment path readable and completable for pre-migration records, while routing all newly created skills assessments to the staged flow.

**Rationale**: The existing API and frontend already expose active assessment records. A hard cut risks stranding in-progress users or breaking old result retrieval paths.

**Alternatives considered**:

- Hard-cut all assessments to the new staged path immediately: rejected because it risks backward-compatibility failures with persisted records.
- Maintain two fully equal long-term flows: rejected because it adds ongoing maintenance overhead.

## Decision 7: Use Django cache framework with Redis in base/production and LocMem in development

**Decision**: Keep Django cache as the abstraction layer, use Redis where already configured in base and production, and change development from `DummyCache` to `LocMemCache` so stage-one cache behavior can be exercised locally without extra infrastructure.

**Rationale**: The repository already configures Redis cache in base and production, but development currently disables caching entirely with `DummyCache`. Stage-one caching is a first-class feature requirement, so local development needs a real cache backend even if it remains process-local.

**Alternatives considered**:

- Keep `DummyCache` in development: rejected because stage-one cache behavior cannot be tested meaningfully.
- Add a file-based cache fallback: rejected because the project already has a cleaner framework-level path through Redis and LocMem.

## Decision 8: Make `RoadmapSignal` a first-class assessment output

**Decision**: The final staged assessment result will include a structured roadmap signal alongside legacy summary fields.

**Rationale**: Roadmap generation currently derives priority skills from broad assessment summaries. Introducing a first-class roadmap signal allows the roadmap module to consume precise evidence and priorities while preserving compatibility with current result consumers during transition.

**Alternatives considered**:

- Keep roadmap generation reading only broad scores and prose: rejected because it preserves the main quality bottleneck.
- Move roadmap signal generation fully into the roadmap module: rejected because it duplicates interpretation logic and couples roadmap quality to raw-answer parsing.

## Decision 9: Keep model selection environment-driven and align it to ADR-001

**Decision**: Keep `OLLAMA_MODEL` environment-driven, align planning and documentation to ADR-001, and avoid coupling the feature to a single Gemma size. The feature must work with E2B as the conservative default and E4B as the preferred option on 16 GB machines.

**Rationale**: Repository documents are inconsistent today: some docs and README files say E4B is standard, while `ai_settings.py` defaults to E2B and ADR-001 explicitly allows both. The staged assessment feature should depend on bounded generation and strong validation, not on one model size being mandatory.

**Alternatives considered**:

- Force E4B as the only supported target: rejected because it unnecessarily narrows deployability on weaker local machines.
- Leave the mismatch undocumented: rejected because it creates repeated confusion in implementation and testing.

## Decision 10: Validate both question-generation stages strictly and fall back deterministically

**Decision**: Both stage-one and stage-two generation paths must validate structure, target alignment, difficulty spread, and required fields before persisting questions.

**Rationale**: The current assessment AI pipeline already uses structured generation plus fallback. Extending that pattern to staged generation preserves reliability and avoids storing malformed or low-signal questions.

**Alternatives considered**:

- Trust model output if it parses as JSON: rejected because structural validity alone does not guarantee useful assessment questions.
- Fail the assessment when generated questions are invalid: rejected because the accepted AI architecture requires deterministic fallbacks for demo-safe operation.
