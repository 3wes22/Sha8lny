"""Scenario corpus for ``role_key = "backend"``.

The v1 seed converts the 10 entries from
``apps.assessments.fallback_scenarios.BACKEND_FALLBACK_SCENARIOS`` into
the typed corpus shape so retrieval has on-topic backend examples on day
one. The fallback dict itself stays in place as the deterministic
contract-safe failure-mode safety net (see
``ai_pipeline._contract_safe_stage_template``); this corpus is the
enrichment path layered on top of the static few-shot block.

Author additional scenarios here following ``AUTHOR_GUIDE.md``.
"""

from __future__ import annotations

from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION
from apps.assessments.scenario_corpus.schema import ScenarioDocument


_SEED_AUTHOR = "internal-seed-from-fallback-scenarios"
_SEED_CREATED_AT = "2026-05-17"


SCENARIOS: list[ScenarioDocument] = [
    {
        "doc_id": "backend.decorators.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "decorators",
        "competency": "Decorators",
        "dimension_key": "python_fundamentals",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess when a decorator preserves function metadata and wraps behavior safely.",
        "scenario_context": (
            "A team adds logging and retry wrappers around Django view callables but breaks "
            "help() output and functools.wraps expectations in tests."
        ),
        "stem": "Which decorator pattern best preserves the wrapped callable's metadata and signature?",
        "options": [
            {"id": "a", "label": "Use functools.wraps on the inner wrapper before returning it from the decorator factory."},
            {"id": "b", "label": "Stack bare nested functions without copying __name__ or __doc__."},
            {"id": "c", "label": "Replace the target function object with a lambda that drops type hints."},
            {"id": "d", "label": "Apply logging inside the function body only and avoid decorators entirely."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "functools.wraps copies metadata from the wrapped function to the wrapper.",
        "correct_answer_rationale": "Preserving __wrapped__ and metadata keeps introspection and tests stable.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "wraps is the standard way to forward metadata."},
            {"option_id": "b", "is_correct": False, "rationale": "Bare nesting loses metadata."},
            {"option_id": "c", "is_correct": False, "rationale": "Lambdas hide the original signature."},
            {"option_id": "d", "is_correct": False, "rationale": "It avoids the cross-cutting concern the scenario asks about."},
        ],
        "helper": "Choose the option that keeps introspection accurate after wrapping.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.select_related_prefetch.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "select_related_prefetch",
        "competency": "select_related / prefetch_related",
        "dimension_key": "django_orm",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess ORM join strategy for related object access in list endpoints.",
        "scenario_context": (
            "An order list API renders customer name and line items for 200 orders; "
            "django-debug-toolbar shows hundreds of duplicate SQL queries."
        ),
        "stem": "Which ORM change most directly removes the N+1 pattern for this read path?",
        "options": [
            {"id": "a", "label": "Use select_related for foreign keys and prefetch_related for reverse many relations on the queryset."},
            {"id": "b", "label": "Call .iterator() on the queryset so Django skips caching."},
            {"id": "c", "label": "Add only db_index=True on the primary key and keep per-row related fetches."},
            {"id": "d", "label": "Serialize with values() and drop all related fields from the response."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "select_related and prefetch_related batch related loads for list views.",
        "correct_answer_rationale": "The list endpoint needs eager loads aligned to how relations are traversed.",
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It matches FK vs reverse relation fetch patterns."},
            {"option_id": "b", "is_correct": False, "rationale": "iterator reduces memory but not query count."},
            {"option_id": "c", "is_correct": False, "rationale": "Indexing alone does not batch related fetches."},
            {"option_id": "d", "is_correct": False, "rationale": "It removes required response data."},
        ],
        "helper": "Pick the queryset optimization that batches related object loads.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.http_api_design.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "http_api_design",
        "competency": "HTTP API Design",
        "dimension_key": "rest_api_design",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess API idempotency design for write endpoints that may be retried by clients.",
        "scenario_context": (
            "A payment API receives duplicate POST /payments requests after a mobile client times out and retries."
        ),
        "stem": "Which design best prevents a customer from being charged twice while keeping the API predictable?",
        "options": [
            {"id": "a", "label": "Require an idempotency key and return the first successful result for duplicate retries."},
            {"id": "b", "label": "Accept each retry and let the finance team reverse duplicate charges overnight."},
            {"id": "c", "label": "Convert the endpoint to GET so clients can safely retry the request."},
            {"id": "d", "label": "Delay every charge by a few seconds so duplicate requests arrive before processing starts."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "The best design prevents duplicate writes at the API boundary instead of cleaning them up later.",
        "correct_answer_rationale": (
            "Idempotency keys let the service treat client retries as the same logical operation without inventing a non-REST transport trick."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It makes duplicate client retries resolve to one logical charge while preserving a POST write contract."},
            {"option_id": "b", "is_correct": False, "rationale": "It accepts data corruption first and pushes correctness to manual cleanup."},
            {"option_id": "c", "is_correct": False, "rationale": "GET must stay side-effect free and is not appropriate for creating a payment."},
            {"option_id": "d", "is_correct": False, "rationale": "A delay is timing-dependent and still allows duplicates under concurrency or repeated retries."},
        ],
        "helper": "Choose the design that makes duplicate writes deterministic at the API boundary.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.relational_modeling.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "relational_modeling",
        "competency": "Relational Modeling",
        "dimension_key": "database_design",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess normalization and relationship modeling for transactional data.",
        "scenario_context": (
            "An orders table needs to store multiple products per order, plus quantity and unit price at purchase time."
        ),
        "stem": "Which schema design best preserves normalization and queryability?",
        "options": [
            {"id": "a", "label": "Create an OrderItems junction table with foreign keys to Orders and Products plus quantity and unit_price columns."},
            {"id": "b", "label": "Store a comma-separated list of product IDs and prices directly on the Orders row."},
            {"id": "c", "label": "Duplicate the full product record into every order so each query stays single-table."},
            {"id": "d", "label": "Put quantity on Product and infer which order it belongs to from the latest update timestamp."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "A junction table keeps the many-to-many relationship explicit and stores line-item attributes in the right place.",
        "correct_answer_rationale": (
            "The relationship itself carries business data, so it needs a dedicated table rather than denormalized copies."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It models the relationship directly and supports line-item attributes cleanly."},
            {"option_id": "b", "is_correct": False, "rationale": "Lists inside one column break relational integrity and make joins, constraints, and indexing harder."},
            {"option_id": "c", "is_correct": False, "rationale": "Copying product records into orders creates update drift and redundant storage."},
            {"option_id": "d", "is_correct": False, "rationale": "The attribute belongs to the order-product relationship, not to Product globally."},
        ],
        "helper": "Look for the schema that keeps the relationship explicit and preserves integrity.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.logging_monitoring.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "logging_monitoring",
        "competency": "Logging and Monitoring",
        "dimension_key": "debugging_and_observability",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess observability fundamentals for isolating cross-service failures.",
        "scenario_context": (
            "Checkout requests return 500s for 2% of traffic after a dependency deploy, but the application logs show no clear error."
        ),
        "stem": "Which first step gives the fastest evidence about where the failure boundary is?",
        "options": [
            {"id": "a", "label": "Correlate request IDs across traces, dependency logs, and error-rate metrics for the failing path."},
            {"id": "b", "label": "Increase log verbosity across every service before checking whether the failing requests share one dependency boundary."},
            {"id": "c", "label": "Roll back the dependency deploy immediately before confirming that the new version is the failing hop."},
            {"id": "d", "label": "Lower the client timeout first so the caller fails faster while the backend incident is still under investigation."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "The strongest first move preserves evidence and narrows the failing boundary with correlated telemetry.",
        "correct_answer_rationale": (
            "Distributed failures usually need correlated signals, not one log stream or a blind restart."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It aligns the user-visible failure with service-level evidence and isolates the failing hop."},
            {"option_id": "b", "is_correct": False, "rationale": "It broadens noise and cost before narrowing the failure boundary."},
            {"option_id": "c", "is_correct": False, "rationale": "Rollback can be right later, but it does not identify whether this dependency is actually the failing hop."},
            {"option_id": "d", "is_correct": False, "rationale": "It changes user-facing behavior without telling the team which dependency or path is failing."},
        ],
        "helper": "Choose the step that increases evidence before changing the system.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.scalability_patterns.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "scalability_patterns",
        "competency": "Scalability Patterns",
        "dimension_key": "system_design_fundamentals",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess how vague product requests become measurable acceptance criteria.",
        "scenario_context": (
            "A product manager asks for 'fast checkout' before a launch campaign but does not define what users should observe."
        ),
        "stem": "Which acceptance criterion best turns that request into an engineering target?",
        "options": [
            {"id": "a", "label": "Checkout should feel fast to the team during manual testing."},
            {"id": "b", "label": "P95 checkout latency stays below 600 ms for authenticated users at projected launch traffic."},
            {"id": "c", "label": "Engineers should use efficient code patterns wherever possible."},
            {"id": "d", "label": "The database should use fewer resources after the release than before it."},
        ],
        "answer_key": {"correct_option_ids": ["b"], "scoring": "single_best"},
        "explanation": "A usable engineering target needs an observable metric, a threshold, and an operating condition.",
        "correct_answer_rationale": (
            "A latency SLO expresses what the user should experience and under which load profile it must hold."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": False, "rationale": "It is subjective and does not define a measurable target."},
            {"option_id": "b", "is_correct": True, "rationale": "It ties the requirement to a measurable outcome and a traffic assumption."},
            {"option_id": "c", "is_correct": False, "rationale": "It describes implementation intent rather than the observable outcome."},
            {"option_id": "d", "is_correct": False, "rationale": "Resource usage alone does not define whether checkout is fast for users."},
        ],
        "helper": "Pick the criterion a team could monitor in production and use in a launch review.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.service_decomposition.s1.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "service_decomposition",
        "competency": "Service Decomposition",
        "dimension_key": "system_design_fundamentals",
        "stage": 1,
        "question_type": "single_choice",
        "difficulty": 3,
        "estimated_seconds": 50,
        "learning_objective": "Assess microservice boundary decisions using domain cohesion and coupling.",
        "scenario_context": (
            "A monolith team wants to split order fulfillment from account management so different teams can ship independently."
        ),
        "stem": "Which signal most strongly suggests these areas deserve separate services?",
        "options": [
            {"id": "a", "label": "They have separate business workflows, ownership boundaries, and failure modes."},
            {"id": "b", "label": "One module has more lines of code than the rest of the monolith."},
            {"id": "c", "label": "The teams prefer different programming languages for future development."},
            {"id": "d", "label": "The database table names for the two areas sort into different alphabetic groups."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "Strong service boundaries follow business behavior and operational ownership rather than incidental code traits.",
        "correct_answer_rationale": (
            "Business capability boundaries are durable and reduce cross-team coordination more than code-shape heuristics."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It aligns decomposition with cohesive workflows and bounded context ownership."},
            {"option_id": "b", "is_correct": False, "rationale": "Code size is a weak proxy and can be fixed without splitting a service."},
            {"option_id": "c", "is_correct": False, "rationale": "Language preference is an implementation concern, not a domain boundary."},
            {"option_id": "d", "is_correct": False, "rationale": "Table naming has no meaningful relationship to service cohesion."},
        ],
        "helper": "Choose the signal that points to a stable domain boundary, not an incidental code pattern.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.http_api_design.s2.open_ended.fallback-seed",
        "role_key": "backend",
        "subskill_key": "http_api_design",
        "competency": "HTTP API Design",
        "dimension_key": "rest_api_design",
        "stage": 2,
        "question_type": "open_ended",
        "difficulty": 4,
        "estimated_seconds": 90,
        "learning_objective": "Assess deeper API retry handling and result reconciliation for payment writes.",
        "scenario_context": (
            "A payments client retries a POST after a network timeout, and the caller needs to know whether the original charge succeeded."
        ),
        "stem": "Explain how you would design the request/response flow so retries stay safe and observable.",
        "options": [],
        "answer_key": {
            "expected_concepts": [
                "idempotency key",
                "replay prior result",
                "request status lookup or correlation id",
            ],
            "required_concept_count": 2,
            "forbidden_concepts": ["convert the write endpoint to get"],
            "scoring": "concept_coverage",
        },
        "explanation": "A strong answer makes duplicate writes deterministic and keeps retry outcomes inspectable.",
        "correct_answer_rationale": (
            "The best explanation combines idempotent write semantics with a way to surface the state of the original attempt."
        ),
        "option_rationales": [],
        "helper": "Mention the contract between client retries, stored request identity, and observable outcome.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.relational_modeling.s2.multi_select.fallback-seed",
        "role_key": "backend",
        "subskill_key": "relational_modeling",
        "competency": "Relational Modeling",
        "dimension_key": "database_design",
        "stage": 2,
        "question_type": "multi_select",
        "difficulty": 4,
        "estimated_seconds": 70,
        "learning_objective": "Assess database evidence gathering around execution plans, cardinality, and indexing choices.",
        "scenario_context": (
            "A products query on a JSONB attributes column takes four seconds on two million rows, and the team has not inspected the execution plan yet."
        ),
        "stem": "Which next actions are strongest? Select all that apply.",
        "options": [
            {"id": "a", "label": "Capture EXPLAIN ANALYZE output to confirm the scan, row estimates, and join strategy."},
            {"id": "b", "label": "Add an index strategy that matches the filter shape once the plan confirms the hot predicate."},
            {"id": "c", "label": "Assume the ORM is the real issue and refactor unrelated query code before measuring anything."},
            {"id": "d", "label": "Check table cardinality and whether the predicate belongs in a dedicated indexed column."},
            {"id": "e", "label": "Remove the JSONB column entirely before confirming whether the query pattern justifies it."},
        ],
        "answer_key": {
            "correct_option_ids": ["a", "b", "d"],
            "scoring": "partial_credit",
        },
        "explanation": "The strongest path starts with evidence from the plan and then aligns the index or schema choice to the predicate.",
        "correct_answer_rationale": (
            "Query tuning should move from measured plan evidence to targeted index or schema adjustments."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "The execution plan shows whether the bottleneck is scanning, joining, or bad estimates."},
            {"option_id": "b", "is_correct": True, "rationale": "Index choice should match the confirmed predicate and access pattern."},
            {"option_id": "c", "is_correct": False, "rationale": "It changes unrelated layers before confirming the database bottleneck."},
            {"option_id": "d", "is_correct": True, "rationale": "Cardinality and schema shape determine whether an index or schema change will help."},
            {"option_id": "e", "is_correct": False, "rationale": "It over-rotates on a destructive schema change without evidence."},
        ],
        "helper": "Select the actions that move from measured query evidence to a targeted fix.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.logging_monitoring.s2.open_ended.fallback-seed",
        "role_key": "backend",
        "subskill_key": "logging_monitoring",
        "competency": "Logging and Monitoring",
        "dimension_key": "debugging_and_observability",
        "stage": 2,
        "question_type": "open_ended",
        "difficulty": 4,
        "estimated_seconds": 90,
        "learning_objective": "Assess incident diagnosis using logs, metrics, and traces together.",
        "scenario_context": (
            "A request path spans three services and only the edge service reports a spike in 500s, while dependency dashboards look normal."
        ),
        "stem": "Explain how you would narrow the failing boundary and what evidence you would collect first.",
        "options": [],
        "answer_key": {
            "expected_concepts": [
                "trace or correlation id",
                "structured logs",
                "latency or error-rate metrics by hop",
            ],
            "required_concept_count": 2,
            "forbidden_concepts": ["disable logging"],
            "scoring": "concept_coverage",
        },
        "explanation": "A strong answer correlates evidence across services instead of guessing or restarting blindly.",
        "correct_answer_rationale": (
            "The right diagnostic path narrows the boundary with correlation identifiers and per-hop telemetry."
        ),
        "option_rationales": [],
        "helper": "Name the identifiers, signals, and service boundaries you would inspect first.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.scalability_patterns.s2.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "scalability_patterns",
        "competency": "Scalability Patterns",
        "dimension_key": "system_design_fundamentals",
        "stage": 2,
        "question_type": "single_choice",
        "difficulty": 4,
        "estimated_seconds": 60,
        "learning_objective": "Assess how requirements become shared success criteria before design work hardens.",
        "scenario_context": (
            "A stakeholder says a new export feature must be 'reliable' for launch, but support and product teams disagree on what failures matter most."
        ),
        "stem": "What is the strongest next step?",
        "options": [
            {"id": "a", "label": "Define the user-visible success criteria, failure budget, and operating conditions with the stakeholders before implementation continues."},
            {"id": "b", "label": "Let engineering pick a reliability target alone so the team can move faster."},
            {"id": "c", "label": "Ship first and use the number of support tickets to decide what reliable should have meant."},
            {"id": "d", "label": "Promise five-nines availability without discussing the traffic profile or failure modes."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "The team needs a shared definition of the user-visible target before choosing architecture or SLOs.",
        "correct_answer_rationale": (
            "The requirement is ambiguous, so the strongest move is to align on failure modes and measurable outcomes first."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It turns vague intent into shared operating criteria the design can satisfy."},
            {"option_id": "b", "is_correct": False, "rationale": "It risks optimizing for the wrong outcome because stakeholders have not aligned."},
            {"option_id": "c", "is_correct": False, "rationale": "It uses customer pain as the requirements process."},
            {"option_id": "d", "is_correct": False, "rationale": "It commits to a number without the context needed to make it meaningful."},
        ],
        "helper": "Choose the step that resolves ambiguity before the team locks in an implementation.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
    {
        "doc_id": "backend.service_decomposition.s2.single_choice.fallback-seed",
        "role_key": "backend",
        "subskill_key": "service_decomposition",
        "competency": "Service Decomposition",
        "dimension_key": "system_design_fundamentals",
        "stage": 2,
        "question_type": "single_choice",
        "difficulty": 4,
        "estimated_seconds": 60,
        "learning_objective": "Assess microservice tradeoffs around boundaries, consistency, and compensation.",
        "scenario_context": (
            "A checkout team wants to split inventory reservation into its own service, but the current flow relies on a shared database transaction with payment capture."
        ),
        "stem": "Which tradeoff should drive the design discussion first?",
        "options": [
            {"id": "a", "label": "How the workflow will preserve consistency, compensation, and ownership once the transaction becomes cross-service."},
            {"id": "b", "label": "Which service can accumulate the most lines of code without becoming hard to navigate."},
            {"id": "c", "label": "Whether the new service can use a different programming language than payment capture."},
            {"id": "d", "label": "How to make deployment diagrams look simpler during architecture review."},
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "explanation": "The primary tradeoff is how the workflow behaves when one local transaction becomes a distributed coordination problem.",
        "correct_answer_rationale": (
            "Service boundaries matter most when they change the consistency model and operational ownership."
        ),
        "option_rationales": [
            {"option_id": "a", "is_correct": True, "rationale": "It focuses the conversation on the real architectural consequence of the split."},
            {"option_id": "b", "is_correct": False, "rationale": "Code size is secondary to workflow semantics and failure handling."},
            {"option_id": "c", "is_correct": False, "rationale": "Language choice is an implementation detail, not the first-order tradeoff here."},
            {"option_id": "d", "is_correct": False, "rationale": "Presentation simplicity does not resolve the coordination problem introduced by the split."},
        ],
        "helper": "Choose the tradeoff that changes the workflow semantics, not just the code organization.",
        "author": _SEED_AUTHOR,
        "license": "internal",
        "review_status": "approved",
        "created_at": _SEED_CREATED_AT,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
]
