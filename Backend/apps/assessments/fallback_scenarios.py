"""
Curated scenario-based fallback questions for staged backend assessments.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


BACKEND_FALLBACK_SCENARIOS: dict[tuple[int, str, str], dict[str, Any]] = {
    (
        1,
        "http_api_design",
        "single_choice",
    ): {
        "scenario_context": (
            "A payment API receives duplicate POST /payments requests after a mobile client times out and retries."
        ),
        "stem": "Which design best prevents a customer from being charged twice while keeping the API predictable?",
        "question_text": (
            "A payment API receives duplicate POST /payments requests after a mobile client times out and retries. "
            "Which design best prevents a customer from being charged twice while keeping the API predictable?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "Require an idempotency key and return the first successful result for duplicate retries.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "Accept each retry and let the finance team reverse duplicate charges overnight.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Convert the endpoint to GET so clients can safely retry the request.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "Delay every charge by a few seconds so duplicate requests arrive before processing starts.",
            },
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "learning_objective": "Assess API idempotency design for write endpoints that may be retried by clients.",
        "explanation": "The best design prevents duplicate writes at the API boundary instead of cleaning them up later.",
        "correct_answer_rationale": (
            "Idempotency keys let the service treat client retries as the same logical operation without inventing a non-REST transport trick."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It makes duplicate client retries resolve to one logical charge while preserving a POST write contract.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "It accepts data corruption first and pushes correctness to manual cleanup.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "GET must stay side-effect free and is not appropriate for creating a payment.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "A delay is timing-dependent and still allows duplicates under concurrency or repeated retries.",
            },
        ],
        "helper": "Choose the design that makes duplicate writes deterministic at the API boundary.",
    },
    (
        1,
        "relational_modeling",
        "single_choice",
    ): {
        "scenario_context": (
            "An orders table needs to store multiple products per order, plus quantity and unit price at purchase time."
        ),
        "stem": "Which schema design best preserves normalization and queryability?",
        "question_text": (
            "An orders table needs to store multiple products per order, plus quantity and unit price at purchase time. "
            "Which schema design best preserves normalization and queryability?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "Create an OrderItems junction table with foreign keys to Orders and Products plus quantity and unit_price columns.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "Store a comma-separated list of product IDs and prices directly on the Orders row.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Duplicate the full product record into every order so each query stays single-table.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "Put quantity on Product and infer which order it belongs to from the latest update timestamp.",
            },
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "learning_objective": "Assess normalization and relationship modeling for transactional data.",
        "explanation": "A junction table keeps the many-to-many relationship explicit and stores line-item attributes in the right place.",
        "correct_answer_rationale": (
            "The relationship itself carries business data, so it needs a dedicated table rather than denormalized copies."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It models the relationship directly and supports line-item attributes cleanly.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "Lists inside one column break relational integrity and make joins, constraints, and indexing harder.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "Copying product records into orders creates update drift and redundant storage.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "The attribute belongs to the order-product relationship, not to Product globally.",
            },
        ],
        "helper": "Look for the schema that keeps the relationship explicit and preserves integrity.",
    },
    (
        1,
        "logging_monitoring",
        "single_choice",
    ): {
        "scenario_context": (
            "Checkout requests return 500s for 2% of traffic after a dependency deploy, but the application logs show no clear error."
        ),
        "stem": "Which first step gives the fastest evidence about where the failure boundary is?",
        "question_text": (
            "Checkout requests return 500s for 2% of traffic after a dependency deploy, but the application logs show no clear error. "
            "Which first step gives the fastest evidence about where the failure boundary is?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "Correlate request IDs across traces, dependency logs, and error-rate metrics for the failing path.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "Increase log verbosity across every service before checking whether the failing requests share one dependency boundary.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Roll back the dependency deploy immediately before confirming that the new version is the failing hop.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "Lower the client timeout first so the caller fails faster while the backend incident is still under investigation.",
            },
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "learning_objective": "Assess observability fundamentals for isolating cross-service failures.",
        "explanation": "The strongest first move preserves evidence and narrows the failing boundary with correlated telemetry.",
        "correct_answer_rationale": (
            "Distributed failures usually need correlated signals, not one log stream or a blind restart."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It aligns the user-visible failure with service-level evidence and isolates the failing hop.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "It broadens noise and cost before narrowing the failure boundary.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "Rollback can be right later, but it does not identify whether this dependency is actually the failing hop.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "It changes user-facing behavior without telling the team which dependency or path is failing.",
            },
        ],
        "helper": "Choose the step that increases evidence before changing the system.",
    },
    (
        1,
        "requirement_translation",
        "single_choice",
    ): {
        "scenario_context": (
            "A product manager asks for 'fast checkout' before a launch campaign but does not define what users should observe."
        ),
        "stem": "Which acceptance criterion best turns that request into an engineering target?",
        "question_text": (
            "A product manager asks for 'fast checkout' before a launch campaign but does not define what users should observe. "
            "Which acceptance criterion best turns that request into an engineering target?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "Checkout should feel fast to the team during manual testing.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "P95 checkout latency stays below 600 ms for authenticated users at projected launch traffic.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Engineers should use efficient code patterns wherever possible.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "The database should use fewer resources after the release than before it.",
            },
        ],
        "answer_key": {"correct_option_ids": ["b"], "scoring": "single_best"},
        "learning_objective": "Assess how vague product requests become measurable acceptance criteria.",
        "explanation": "A usable engineering target needs an observable metric, a threshold, and an operating condition.",
        "correct_answer_rationale": (
            "A latency SLO expresses what the user should experience and under which load profile it must hold."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": False,
                "rationale": "It is subjective and does not define a measurable target.",
            },
            {
                "option_id": "b",
                "is_correct": True,
                "rationale": "It ties the requirement to a measurable outcome and a traffic assumption.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "It describes implementation intent rather than the observable outcome.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "Resource usage alone does not define whether checkout is fast for users.",
            },
        ],
        "helper": "Pick the criterion a team could monitor in production and use in a launch review.",
    },
    (
        1,
        "service_decomposition",
        "single_choice",
    ): {
        "scenario_context": (
            "A monolith team wants to split order fulfillment from account management so different teams can ship independently."
        ),
        "stem": "Which signal most strongly suggests these areas deserve separate services?",
        "question_text": (
            "A monolith team wants to split order fulfillment from account management so different teams can ship independently. "
            "Which signal most strongly suggests these areas deserve separate services?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "They have separate business workflows, ownership boundaries, and failure modes.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "One module has more lines of code than the rest of the monolith.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "The teams prefer different programming languages for future development.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "The database table names for the two areas sort into different alphabetic groups.",
            },
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "learning_objective": "Assess microservice boundary decisions using domain cohesion and coupling.",
        "explanation": "Strong service boundaries follow business behavior and operational ownership rather than incidental code traits.",
        "correct_answer_rationale": (
            "Business capability boundaries are durable and reduce cross-team coordination more than code-shape heuristics."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It aligns decomposition with cohesive workflows and bounded context ownership.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "Code size is a weak proxy and can be fixed without splitting a service.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "Language preference is an implementation concern, not a domain boundary.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "Table naming has no meaningful relationship to service cohesion.",
            },
        ],
        "helper": "Choose the signal that points to a stable domain boundary, not an incidental code pattern.",
    },
    (
        2,
        "http_api_design",
        "open_ended",
    ): {
        "scenario_context": (
            "A payments client retries a POST after a network timeout, and the caller needs to know whether the original charge succeeded."
        ),
        "stem": "Explain how you would design the request/response flow so retries stay safe and observable.",
        "question_text": (
            "A payments client retries a POST after a network timeout, and the caller needs to know whether the original charge succeeded. "
            "Explain how you would design the request/response flow so retries stay safe and observable."
        ),
        "type": "text",
        "interaction_mode": "text",
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
        "learning_objective": "Assess deeper API retry handling and result reconciliation for payment writes.",
        "explanation": "A strong answer makes duplicate writes deterministic and keeps retry outcomes inspectable.",
        "correct_answer_rationale": (
            "The best explanation combines idempotent write semantics with a way to surface the state of the original attempt."
        ),
        "option_rationales": [],
        "helper": "Mention the contract between client retries, stored request identity, and observable outcome.",
    },
    (
        2,
        "relational_modeling",
        "multi_select",
    ): {
        "scenario_context": (
            "A products query on a JSONB attributes column takes four seconds on two million rows, and the team has not inspected the execution plan yet."
        ),
        "stem": "Which next actions are strongest? Select all that apply.",
        "question_text": (
            "A products query on a JSONB attributes column takes four seconds on two million rows, and the team has not inspected the execution plan yet. "
            "Which next actions are strongest? Select all that apply."
        ),
        "type": "multiple_choice",
        "interaction_mode": "multi_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "Capture EXPLAIN ANALYZE output to confirm the scan, row estimates, and join strategy.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "Add an index strategy that matches the filter shape once the plan confirms the hot predicate.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Assume the ORM is the real issue and refactor unrelated query code before measuring anything.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "Check table cardinality and whether the predicate belongs in a dedicated indexed column.",
            },
            {
                "id": "e",
                "value": "e",
                "label": "Remove the JSONB column entirely before confirming whether the query pattern justifies it.",
            },
        ],
        "answer_key": {
            "correct_option_ids": ["a", "b", "d"],
            "scoring": "partial_credit",
        },
        "learning_objective": "Assess database evidence gathering around execution plans, cardinality, and indexing choices.",
        "explanation": "The strongest path starts with evidence from the plan and then aligns the index or schema choice to the predicate.",
        "correct_answer_rationale": (
            "Query tuning should move from measured plan evidence to targeted index or schema adjustments."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "The execution plan shows whether the bottleneck is scanning, joining, or bad estimates.",
            },
            {
                "option_id": "b",
                "is_correct": True,
                "rationale": "Index choice should match the confirmed predicate and access pattern.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "It changes unrelated layers before confirming the database bottleneck.",
            },
            {
                "option_id": "d",
                "is_correct": True,
                "rationale": "Cardinality and schema shape determine whether an index or schema change will help.",
            },
            {
                "option_id": "e",
                "is_correct": False,
                "rationale": "It over-rotates on a destructive schema change without evidence.",
            },
        ],
        "helper": "Select the actions that move from measured query evidence to a targeted fix.",
    },
    (
        2,
        "logging_monitoring",
        "open_ended",
    ): {
        "scenario_context": (
            "A request path spans three services and only the edge service reports a spike in 500s, while dependency dashboards look normal."
        ),
        "stem": "Explain how you would narrow the failing boundary and what evidence you would collect first.",
        "question_text": (
            "A request path spans three services and only the edge service reports a spike in 500s, while dependency dashboards look normal. "
            "Explain how you would narrow the failing boundary and what evidence you would collect first."
        ),
        "type": "text",
        "interaction_mode": "text",
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
        "learning_objective": "Assess incident diagnosis using logs, metrics, and traces together.",
        "explanation": "A strong answer correlates evidence across services instead of guessing or restarting blindly.",
        "correct_answer_rationale": (
            "The right diagnostic path narrows the boundary with correlation identifiers and per-hop telemetry."
        ),
        "option_rationales": [],
        "helper": "Name the identifiers, signals, and service boundaries you would inspect first.",
    },
    (
        2,
        "requirement_translation",
        "single_choice",
    ): {
        "scenario_context": (
            "A stakeholder says a new export feature must be 'reliable' for launch, but support and product teams disagree on what failures matter most."
        ),
        "stem": "What is the strongest next step?",
        "question_text": (
            "A stakeholder says a new export feature must be 'reliable' for launch, but support and product teams disagree on what failures matter most. "
            "What is the strongest next step?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "Define the user-visible success criteria, failure budget, and operating conditions with the stakeholders before implementation continues.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "Let engineering pick a reliability target alone so the team can move faster.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Ship first and use the number of support tickets to decide what reliable should have meant.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "Promise five-nines availability without discussing the traffic profile or failure modes.",
            },
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "learning_objective": "Assess how requirements become shared success criteria before design work hardens.",
        "explanation": "The team needs a shared definition of the user-visible target before choosing architecture or SLOs.",
        "correct_answer_rationale": (
            "The requirement is ambiguous, so the strongest move is to align on failure modes and measurable outcomes first."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It turns vague intent into shared operating criteria the design can satisfy.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "It risks optimizing for the wrong outcome because stakeholders have not aligned.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "It uses customer pain as the requirements process.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "It commits to a number without the context needed to make it meaningful.",
            },
        ],
        "helper": "Choose the step that resolves ambiguity before the team locks in an implementation.",
    },
    (
        2,
        "service_decomposition",
        "single_choice",
    ): {
        "scenario_context": (
            "A checkout team wants to split inventory reservation into its own service, but the current flow relies on a shared database transaction with payment capture."
        ),
        "stem": "Which tradeoff should drive the design discussion first?",
        "question_text": (
            "A checkout team wants to split inventory reservation into its own service, but the current flow relies on a shared database transaction with payment capture. "
            "Which tradeoff should drive the design discussion first?"
        ),
        "type": "multiple_choice",
        "interaction_mode": "single_select",
        "options": [
            {
                "id": "a",
                "value": "a",
                "label": "How the workflow will preserve consistency, compensation, and ownership once the transaction becomes cross-service.",
            },
            {
                "id": "b",
                "value": "b",
                "label": "Which service can accumulate the most lines of code without becoming hard to navigate.",
            },
            {
                "id": "c",
                "value": "c",
                "label": "Whether the new service can use a different programming language than payment capture.",
            },
            {
                "id": "d",
                "value": "d",
                "label": "How to make deployment diagrams look simpler during architecture review.",
            },
        ],
        "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
        "learning_objective": "Assess microservice tradeoffs around boundaries, consistency, and compensation.",
        "explanation": "The primary tradeoff is how the workflow behaves when one local transaction becomes a distributed coordination problem.",
        "correct_answer_rationale": (
            "Service boundaries matter most when they change the consistency model and operational ownership."
        ),
        "option_rationales": [
            {
                "option_id": "a",
                "is_correct": True,
                "rationale": "It focuses the conversation on the real architectural consequence of the split.",
            },
            {
                "option_id": "b",
                "is_correct": False,
                "rationale": "Code size is secondary to workflow semantics and failure handling.",
            },
            {
                "option_id": "c",
                "is_correct": False,
                "rationale": "Language choice is an implementation detail, not the first-order tradeoff here.",
            },
            {
                "option_id": "d",
                "is_correct": False,
                "rationale": "Presentation simplicity does not resolve the coordination problem introduced by the split.",
            },
        ],
        "helper": "Choose the tradeoff that changes the workflow semantics, not just the code organization.",
    },
}


def get_curated_fallback_scenario(
    *,
    role_key: str,
    subskill_key: str,
    stage: int,
    question_type: str,
) -> dict[str, Any] | None:
    if role_key != "backend":
        return None

    scenario = BACKEND_FALLBACK_SCENARIOS.get((stage, subskill_key, question_type))
    if scenario is None:
        return None
    return deepcopy(scenario)
