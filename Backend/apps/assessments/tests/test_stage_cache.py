from dataclasses import replace

from django.core.cache import cache

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.core.ai_logging import build_ai_metadata
from apps.core.exceptions import AIServiceError
from apps.core.gemma_client import GemmaResponse


def _stage_one_payload(graph):
    targets = StageAllocator.allocate_stage_one(graph)
    return {"questions": AssessmentAIService._deterministic_questions(graph, targets, stage=1)}


def _messy_stage_payload(graph, *, stage: int):
    targets = StageAllocator.allocate_stage_one(graph)
    return {
        "questions": [
            {
                "id": f"s{stage}_q1",
                "question_text": f"When designing {targets[0].label.lower()}, which tradeoff matters first?",
                "options": [
                    {"value": "low"},
                    {"value": "mid"},
                    {"value": "high"},
                ],
            },
            {
                "id": f"s{stage}_q2",
                "subskill_key": "not_a_real_subskill",
                "question_text": f"What failure mode do you check first in {targets[1].label.lower()}?",
            },
            {
                "id": f"s{stage}_q3",
                "subskill_key": targets[2].key,
                "question_text": f"How would you review a pull request touching {targets[2].label.lower()}?",
            },
            {
                "id": f"s{stage}_q4",
                "subskill_key": targets[2].key,
                "question_text": f"What would make you reject an implementation of {targets[3].label.lower()}?",
            },
            {
                "id": f"s{stage}_q5",
                "subskill_key": targets[4].key,
                "question_text": "",
            },
        ]
    }


def _live_like_stage_payload(graph, *, stage: int):
    targets = StageAllocator.allocate_stage_one(graph)
    return {
        "questions": [
            {
                "id": f"s{stage}_q1",
                "subskill_key": targets[0].key,
                "question_text": (
                    "You need to design an endpoint to handle user profile updates. "
                    "Which HTTP method and URI structure is most appropriate?"
                ),
                "question_type": "multiple_choice",
                "interaction_mode": "text_input",
                "options": [
                    "PUT /users/{id}/profile",
                    "POST /users/update_profile",
                    "PATCH /users/{id}",
                    "GET /users/{id}/profile",
                ],
            },
            {
                "id": f"s{stage}_q2",
                "subskill_key": targets[1].key,
                "question_text": f"What constraint best fits {targets[1].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "text_input",
                "options": [
                    "Foreign Key Constraint",
                    "Unique Constraint",
                    "CHECK Constraint",
                    "Primary Key Constraint",
                ],
            },
            {
                "id": f"s{stage}_q3",
                "subskill_key": targets[2].key,
                "question_text": f"How would you debug a failure in {targets[2].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "text_input",
                "options": ["First", "Second", "Third", "Fourth"],
            },
            {
                "id": f"s{stage}_q4",
                "subskill_key": targets[3].key,
                "question_text": f"What review concern matters most in {targets[3].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "text_input",
                "options": ["A", "B", "C", "D"],
            },
            {
                "id": f"s{stage}_q5",
                "subskill_key": targets[4].key,
                "question_text": f"What tradeoff would you explain for {targets[4].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "text_input",
                "options": ["One", "Two", "Three", "Four"],
            },
        ]
    }


def _repaired_live_stage_payload(graph, *, stage: int):
    targets = StageAllocator.allocate_stage_one(graph)
    return {
        "questions": [
            {
                "id": f"s{stage}_q1",
                "subskill_key": targets[0].key,
                "question_text": (
                    "You need to design an endpoint to handle user profile updates. "
                    "Which HTTP method and URI structure is most appropriate?"
                ),
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "POST /users/update_profile", "score": 1},
                    {"value": "mid", "label": "PUT /users/{id}/profile", "score": 3},
                    {"value": "high", "label": "PATCH /users/{id}", "score": 5},
                ],
                "answer_key": {"correct_option_ids": ["high"], "scoring": "single_best"},
            },
            {
                "id": f"s{stage}_q2",
                "subskill_key": targets[1].key,
                "question_text": f"What constraint best fits {targets[1].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "Primary Key Constraint", "score": 1},
                    {"value": "mid", "label": "Foreign Key Constraint", "score": 3},
                    {"value": "high", "label": "CHECK Constraint", "score": 5},
                ],
                "answer_key": {"correct_option_ids": ["high"], "scoring": "single_best"},
            },
            {
                "id": f"s{stage}_q3",
                "subskill_key": targets[2].key,
                "question_text": f"Which first diagnostic step is strongest when debugging a failure in {targets[2].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "Restart the failing service and retry traffic", "score": 1},
                    {"value": "mid", "label": "Check recent logs, metrics, and dependency health", "score": 3},
                    {"value": "high", "label": "Trace the full request path and isolate the failing boundary", "score": 5},
                ],
                "answer_key": {"correct_option_ids": ["high"], "scoring": "single_best"},
            },
            {
                "id": f"s{stage}_q4",
                "subskill_key": targets[3].key,
                "question_text": f"What review concern matters most in {targets[3].label.lower()}?",
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "Naming only", "score": 1},
                    {"value": "mid", "label": "Basic correctness and tests", "score": 3},
                    {"value": "high", "label": "Concurrency, failure modes, and rollback safety", "score": 5},
                ],
                "answer_key": {"correct_option_ids": ["high"], "scoring": "single_best"},
            },
            {
                "id": f"s{stage}_q5",
                "subskill_key": targets[4].key,
                "question_text": f"Which tradeoff matters most when reviewing {targets[4].label.lower()} decisions?",
                "question_type": "multiple_choice",
                "interaction_mode": "single_select",
                "options": [
                    {"value": "low", "label": "One", "score": 1},
                    {"value": "mid", "label": "Two", "score": 3},
                    {"value": "high", "label": "Three", "score": 5},
                ],
                "answer_key": {"correct_option_ids": ["high"], "scoring": "single_best"},
            },
        ]
    }


def _observed_live_stage_payload(graph, *, stage: int):
    targets = StageAllocator.allocate_stage_one(graph)
    return {
        "questions": [
            {
                "id": f"s{stage}_q1",
                "subskill_key": targets[0].key,
                "question_text": (
                    "A microservice needs to expose user profile data. Should the API use "
                    "a GET request with a query parameter (e.g., `/users?id=123`) or a "
                    "path parameter (e.g., `/users/123`) to retrieve a specific user "
                    "profile? Justify your choice based on REST principles."
                ),
                "question_type": "Multiple Choice",
                "interaction_mode": "Single Select",
                "options": [
                    {
                        "value": "GET /users?id=123",
                        "label": "Query Parameter",
                        "score": 3,
                    },
                    {
                        "value": "GET /users/123",
                        "label": "Path Parameter",
                        "score": 5,
                    },
                    {
                        "value": "POST /users/lookup",
                        "label": "POST Request",
                        "score": 1,
                    },
                ],
                "difficulty": "mid",
                "estimated_seconds": 45,
                "helper": "Focus on resource identification and RESTful URI design.",
            },
            {
                "id": f"s{stage}_q2",
                "subskill_key": targets[1].key,
                "question_text": (
                    "You are designing a schema for an e-commerce system involving "
                    "products, orders, and customers. Which relationship type is most "
                    "appropriate for linking 'Orders' to 'Products' if a single order "
                    "can contain multiple products, and a single product can be in "
                    "multiple orders?"
                ),
                "question_type": "Multiple Choice",
                "interaction_mode": "Single Select",
                "options": [
                    {
                        "value": "One-to-Many (Order to Product)",
                        "label": "One-to-Many",
                        "score": 3,
                    },
                    {
                        "value": "Many-to-Many (via Junction Table)",
                        "label": "Many-to-Many",
                        "score": 5,
                    },
                    {
                        "value": "One-to-One",
                        "label": "One-to-One",
                        "score": 1,
                    },
                ],
                "difficulty": "mid",
                "estimated_seconds": 40,
                "helper": "Identify the need for an associative entity (junction table) to resolve the M:M relationship.",
            },
            {
                "id": f"s{stage}_q3",
                "subskill_key": targets[2].key,
                "question_text": (
                    "A critical backend service experiences intermittent 500 errors. "
                    "You implement structured logging (JSON format) and metrics "
                    "(latency, error rate). Which metric is most crucial for "
                    "diagnosing intermittent service failures and identifying "
                    "bottlenecks in a distributed system?"
                ),
                "question_type": "Multiple Choice",
                "interaction_mode": "Single Select",
                "options": [
                    {
                        "value": "CPU Utilization Percentage",
                        "label": "CPU Utilization Percentage",
                        "score": 3,
                    },
                    {
                        "value": "Request Latency Percentiles (P95/P99)",
                        "label": "Request Latency Percentiles (P95/P99)",
                        "score": 5,
                    },
                    {
                        "value": "Total Log Line Count",
                        "label": "Total Log Line Count",
                        "score": 1,
                    },
                ],
                "difficulty": "high",
                "estimated_seconds": 60,
                "helper": "Focus on user experience and system health indicators rather than raw resource usage.",
            },
            {
                "id": f"s{stage}_q4",
                "subskill_key": targets[3].key,
                "question_text": (
                    "A product manager requests an API endpoint that returns all customer "
                    "details, including sensitive PII (Personally Identifiable "
                    "Information). How should you translate this requirement into a "
                    "secure and compliant API design, considering data minimization principles?"
                ),
                "question_type": "Multiple Choice",
                "interaction_mode": "Single Select",
                "options": [
                    {
                        "value": "Return all PII directly via the API.",
                        "label": "Return all PII directly via the API.",
                        "score": 1,
                    },
                    {
                        "value": "Return only necessary, non-sensitive fields, requiring separate calls for sensitive data.",
                        "label": "Return only necessary, non-sensitive fields, requiring separate calls for sensitive data.",
                        "score": 5,
                    },
                    {
                        "value": "Return PII encrypted, but allow the client to request decryption keys.",
                        "label": "Return PII encrypted, but allow the client to request decryption keys.",
                        "score": 3,
                    },
                ],
                "difficulty": "high",
                "estimated_seconds": 50,
                "helper": "Emphasize security, privacy, and the principle of least privilege.",
            },
            {
                "id": f"s{stage}_q5",
                "subskill_key": targets[4].key,
                "question_text": (
                    "When decomposing a monolithic application into microservices, "
                    "which criterion should primarily guide the boundary definition "
                    "between services to ensure high cohesion and low coupling?"
                ),
                "question_type": "Multiple Choice",
                "interaction_mode": "Single Select",
                "options": [
                    {
                        "value": "Shared Database Schema",
                        "label": "Shared Database Schema",
                        "score": 1,
                    },
                    {
                        "value": "Business Capability (Bounded Context)",
                        "label": "Business Capability (Bounded Context)",
                        "score": 5,
                    },
                    {
                        "value": "Codebase Size",
                        "label": "Codebase Size",
                        "score": 3,
                    },
                ],
                "difficulty": "mid",
                "estimated_seconds": 45,
                "helper": "Focus on domain-driven design principles for service boundaries.",
            },
        ]
    }


def _typed_stage_payload(graph, *, stage: int):
    if stage == 1:
        return _stage_one_payload(graph)

    targets = StageAllocator.allocate_stage_one(graph)
    return {
        "questions": [
            {
                "id": f"s{stage}_q1",
                "subskill_key": targets[0].key,
                "question_type": "single_choice",
                "competency": targets[0].label,
                "learning_objective": "Choose the most RESTful update pattern for a single resource.",
                "scenario_context": (
                    "A user profile service needs to support partial updates while preserving "
                    "idempotent retry behavior for clients."
                ),
                "stem": "Which API design is the best choice for partially updating one user profile resource?",
                "options": [
                    {"id": "a", "label": "POST /users/update-profile"},
                    {"id": "b", "label": "PATCH /users/{id}"},
                    {"id": "c", "label": "GET /users/{id}?update=true"},
                    {"id": "d", "label": "PUT /profiles/search"},
                ],
                "answer_key": {
                    "correct_option_ids": ["b"],
                    "scoring": "single_best",
                },
                "explanation": "PATCH is the best fit for partial updates to an existing resource.",
                "correct_answer_rationale": (
                    "PATCH targets a partial update on an existing resource without inventing a custom action."
                ),
                "option_rationales": [
                    {
                        "option_id": "a",
                        "is_correct": False,
                        "rationale": "POST with a verb-style endpoint hides resource semantics and complicates retries.",
                    },
                    {
                        "option_id": "b",
                        "is_correct": True,
                        "rationale": "PATCH expresses a partial resource update and keeps the URI resource-oriented.",
                    },
                    {
                        "option_id": "c",
                        "is_correct": False,
                        "rationale": "GET must not perform mutations.",
                    },
                    {
                        "option_id": "d",
                        "is_correct": False,
                        "rationale": "The endpoint does not identify the resource being updated.",
                    },
                ],
                "difficulty": 3,
                "estimated_seconds": 50,
            },
            {
                "id": f"s{stage}_q2",
                "subskill_key": targets[1].key,
                "question_type": "multi_select",
                "competency": targets[1].label,
                "learning_objective": "Identify the schema elements required for a normalized many-to-many design.",
                "scenario_context": (
                    "An ordering system must track products on each order, including quantity and historical unit price."
                ),
                "stem": "For an orders and products schema, select all that apply.",
                "options": [
                    {"id": "a", "label": "Add an OrderItems junction table"},
                    {"id": "b", "label": "Store every product row directly on Orders"},
                    {"id": "c", "label": "Use foreign keys from OrderItems to Orders and Products"},
                    {"id": "d", "label": "Duplicate product price history across unrelated tables"},
                    {"id": "e", "label": "Add quantity on the OrderItems relationship"},
                ],
                "answer_key": {
                    "correct_option_ids": ["a", "c", "e"],
                    "scoring": "partial_credit",
                },
                "explanation": "A junction table with relationship attributes preserves normalization and data integrity.",
                "correct_answer_rationale": (
                    "The junction table captures the many-to-many relationship while keeping line-item attributes in one place."
                ),
                "option_rationales": [
                    {
                        "option_id": "a",
                        "is_correct": True,
                        "rationale": "A junction table models the relationship explicitly.",
                    },
                    {
                        "option_id": "b",
                        "is_correct": False,
                        "rationale": "Embedding repeated product rows on Orders breaks normalization.",
                    },
                    {
                        "option_id": "c",
                        "is_correct": True,
                        "rationale": "Foreign keys protect referential integrity on both sides of the relationship.",
                    },
                    {
                        "option_id": "d",
                        "is_correct": False,
                        "rationale": "Duplicating price history across unrelated tables creates inconsistent sources of truth.",
                    },
                    {
                        "option_id": "e",
                        "is_correct": True,
                        "rationale": "Quantity belongs on the relationship, not on Product itself.",
                    },
                ],
                "difficulty": 4,
                "estimated_seconds": 70,
            },
            {
                "id": f"s{stage}_q3",
                "subskill_key": targets[2].key,
                "question_type": "open_ended",
                "competency": targets[2].label,
                "learning_objective": "Explain the minimum observability signals needed to isolate a cross-service latency spike.",
                "scenario_context": (
                    "A checkout request intermittently spikes to 5 seconds across three services during peak traffic."
                ),
                "stem": "A checkout request intermittently spikes to 5 seconds across three services. Explain how you would instrument the path to isolate the root cause.",
                "answer_key": {
                    "expected_concepts": [
                        "trace_id propagation",
                        "structured logging",
                        "latency percentiles",
                    ],
                    "required_concept_count": 2,
                    "forbidden_concepts": [
                        "restart everything first",
                    ],
                    "scoring": "concept_coverage",
                },
                "explanation": "A strong answer ties logs, traces, and latency signals together across service boundaries.",
                "correct_answer_rationale": (
                    "The answer should connect request tracing with service-level telemetry instead of focusing on one signal in isolation."
                ),
                "option_rationales": [],
                "difficulty": 4,
                "estimated_seconds": 90,
            },
            {
                "id": f"s{stage}_q4",
                "subskill_key": targets[3].key,
                "question_type": "single_choice",
                "competency": targets[3].label,
                "learning_objective": "Choose the secure design that minimizes unnecessary PII exposure.",
                "scenario_context": (
                    "A PM requests a customer detail endpoint that includes sensitive PII for a dashboard used by several internal teams."
                ),
                "stem": "Which API response design best follows data minimization for sensitive customer details?",
                "options": [
                    {"id": "a", "label": "Return all PII by default to reduce round trips"},
                    {"id": "b", "label": "Return only non-sensitive fields by default and gate sensitive fields behind explicit authorization"},
                    {"id": "c", "label": "Encrypt PII and send the decryption key in the same response"},
                    {"id": "d", "label": "Mirror database columns exactly in every response"},
                ],
                "answer_key": {
                    "correct_option_ids": ["b"],
                    "scoring": "single_best",
                },
                "explanation": "The secure design limits exposure and requires explicit authorization for sensitive data.",
                "correct_answer_rationale": (
                    "Default-safe responses plus explicit authorization reduce unnecessary data exposure."
                ),
                "option_rationales": [
                    {
                        "option_id": "a",
                        "is_correct": False,
                        "rationale": "It optimizes convenience at the expense of least privilege.",
                    },
                    {
                        "option_id": "b",
                        "is_correct": True,
                        "rationale": "It keeps the default payload minimal while allowing audited access when required.",
                    },
                    {
                        "option_id": "c",
                        "is_correct": False,
                        "rationale": "Shipping the decryption key with the payload defeats the protection.",
                    },
                    {
                        "option_id": "d",
                        "is_correct": False,
                        "rationale": "Mirroring storage design to API responses exposes more data than the requirement justifies.",
                    },
                ],
                "difficulty": 4,
                "estimated_seconds": 55,
            },
            {
                "id": f"s{stage}_q5",
                "subskill_key": targets[4].key,
                "question_type": "single_choice",
                "competency": targets[4].label,
                "learning_objective": "Pick the strongest criterion for microservice boundary design.",
                "scenario_context": (
                    "A team is splitting a monolith and wants service boundaries that can evolve without constant cross-team coordination."
                ),
                "stem": "Which primary criterion should guide a first pass at microservice boundaries?",
                "options": [
                    {"id": "a", "label": "Shared deployment frequency"},
                    {"id": "b", "label": "Codebase line count"},
                    {"id": "c", "label": "Business capability and bounded context"},
                    {"id": "d", "label": "Programming language preference"},
                ],
                "answer_key": {
                    "correct_option_ids": ["c"],
                    "scoring": "single_best",
                },
                "explanation": "Bounded contexts align services to stable business capabilities and reduce coupling.",
                "correct_answer_rationale": (
                    "Business capability boundaries keep ownership aligned with domain behavior instead of incidental code structure."
                ),
                "option_rationales": [
                    {
                        "option_id": "a",
                        "is_correct": False,
                        "rationale": "Shared deployment timing is an operational signal, not a durable domain boundary.",
                    },
                    {
                        "option_id": "b",
                        "is_correct": False,
                        "rationale": "Code size says little about coupling or ownership.",
                    },
                    {
                        "option_id": "c",
                        "is_correct": True,
                        "rationale": "Bounded contexts optimize cohesion and reduce cross-service coupling.",
                    },
                    {
                        "option_id": "d",
                        "is_correct": False,
                        "rationale": "Language preference is an implementation detail, not a service-boundary driver.",
                    },
                ],
                "difficulty": 3,
                "estimated_seconds": 45,
            },
        ]
    }


def _without_option_ids(options):
    return [
        {key: value for key, value in option.items() if key != "id"}
        for option in options
    ]


def test_stage_one_generation_uses_cache_for_same_role_and_version(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=_stage_one_payload(graph),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=12,
                model="mock-gemma",
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    first_questions, _ = AssessmentAIService.generate_stage_one("backend", graph)
    second_questions, _ = AssessmentAIService.generate_stage_one("backend", graph)

    assert calls["count"] == 1
    assert first_questions == second_questions


def test_stage_one_generation_invalidates_cache_when_graph_version_changes(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=_stage_one_payload(graph),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=12,
                model="mock-gemma",
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    AssessmentAIService.generate_stage_one("backend", graph)
    AssessmentAIService.generate_stage_one("backend", replace(graph, version="stub-v2"))

    assert calls["count"] == 2


def test_stage_one_generation_does_not_reuse_cached_questions_after_curated_replacement(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    replacement_subskill = replace(
        graph.dimensions[0].subskills[0],
        key="service_contracts",
        label="Service Contracts",
    )
    replacement_dimension = replace(
        graph.dimensions[0],
        subskills=[replacement_subskill, *graph.dimensions[0].subskills[1:]],
    )
    replacement_graph = replace(
        graph,
        version="curated-v3",
        dimensions=[replacement_dimension, *graph.dimensions[1:]],
    )
    payloads = iter([
        _stage_one_payload(graph),
        _stage_one_payload(replacement_graph),
    ])

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=next(payloads),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=12,
                model="mock-gemma",
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    first_questions, _ = AssessmentAIService.generate_stage_one("backend", graph)
    second_questions, _ = AssessmentAIService.generate_stage_one("backend", replacement_graph)

    assert calls["count"] == 2
    assert first_questions[0]["subskill_key"] == graph.dimensions[0].subskills[0].key
    assert second_questions[0]["subskill_key"] == "service_contracts"
    assert first_questions != second_questions


def test_stage_question_prompts_require_structured_non_generic_output():
    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)

    stage_one_prompt = AssessmentAIService._build_stage_one_prompt(graph, targets)
    stage_two_prompt = AssessmentAIService._build_stage_two_prompt(
        graph,
        targets,
        type(
            "GapProfileStub",
            (),
            {
                "high_priority_gaps": [target.key for target in targets[:3]],
                "uncertain_areas": [targets[-1].key],
            },
        )(),
    )

    assert "Return exactly 5 question objects" in stage_one_prompt
    assert "scenario_context" in stage_one_prompt
    assert "correct_answer_rationale" in stage_one_prompt
    assert "option_rationales" in stage_one_prompt
    assert "Every stem MUST begin with a concrete scenario" in stage_one_prompt
    assert "Each distractor must be something a junior developer might plausibly choose" in stage_one_prompt
    assert "Which option is the strongest engineering choice" in stage_one_prompt
    assert "few-shot examples" in stage_one_prompt.lower()
    assert "Do not repeat stage-one wording" in stage_two_prompt
    assert "fundamentals" in stage_one_prompt.lower()
    assert "tradeoff" in stage_two_prompt.lower()


def test_stage_one_generation_sends_response_json_schema(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    observed = {}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        observed["schema"] = response_json_schema
        return GemmaResponse(
            text="{}",
            payload=_typed_stage_payload(graph, stage=1),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=44,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=64,
            completion_tokens=140,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    AssessmentAIService.generate_stage_one("backend", graph)

    schema = observed["schema"]
    assert schema["type"] == "object"
    assert "questions" in schema["required"]
    question_schema = schema["properties"]["questions"]["items"]
    assert question_schema["properties"]["scenario_context"]["type"] == "string"
    assert question_schema["properties"]["correct_answer_rationale"]["type"] == "string"
    assert question_schema["properties"]["option_rationales"]["type"] == "array"
    assert question_schema["properties"]["question_type"]["enum"] == [
        "single_choice",
        "multi_select",
        "open_ended",
    ]


def test_stage_one_generation_normalizes_typed_question_contract(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        return GemmaResponse(
            text="{}",
            payload=_typed_stage_payload(graph, stage=1),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=44,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=64,
            completion_tokens=140,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert metadata.fallback_used is False
    assert questions[0]["question_type"] == "single_choice"
    assert questions[0]["type"] == "multiple_choice"
    assert questions[0]["interaction_mode"] == "single_select"
    assert questions[0]["answer_key"] == {
        "correct_option_ids": ["a"],
        "scoring": "single_best",
    }
    assert questions[0]["scenario_context"].startswith("A payment API receives duplicate POST /payments")
    assert questions[0]["correct_answer_rationale"].startswith("Idempotency keys let the service")
    assert len(questions[0]["option_rationales"]) == 4
    assert questions[0]["validation_flags"] == []
    assert all(question["question_type"] == "single_choice" for question in questions)
    assert all(question["validation_flags"] == [] for question in questions)


def test_stage_one_generation_repairs_partial_llm_payload_instead_of_falling_back(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=(
                _messy_stage_payload(graph, stage=1)
                if calls["count"] == 1
                else _repaired_live_stage_payload(graph, stage=1)
            ),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=18,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=14,
            completion_tokens=19,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)
    targets = StageAllocator.allocate_stage_one(graph)

    assert metadata.fallback_used is False
    assert calls["count"] == 2
    assert [question["subskill_key"] for question in questions] == [target.key for target in targets]
    assert all(question["validation_flags"] == [] for question in questions)
    assert questions[0]["question_text"].startswith("You need to design an endpoint")
    assert questions[1]["question_text"].startswith("What constraint best fits")
    assert questions[3]["question_text"].startswith("What review concern matters most")
    assert questions[4]["question_text"].startswith("Which tradeoff matters most")
    assert _without_option_ids(questions[0]["options"]) == [
        {
            "value": "low",
            "label": "POST /users/update_profile",
            "score": 1,
        },
        {
            "value": "mid",
            "label": "PUT /users/{id}/profile",
            "score": 3,
        },
        {
            "value": "high",
            "label": "PATCH /users/{id}",
            "score": 5,
        },
    ]


def test_stage_one_generation_replaces_invalid_questions_after_failed_repair(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=_messy_stage_payload(graph, stage=1),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=18,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=14,
            completion_tokens=19,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert calls["count"] == 2
    assert metadata.fallback_used is True
    assert metadata.error_code == "invalid_stage_question_contract"
    assert all(question["validation_flags"] == [] for question in questions)
    assert "strongest engineering choice" not in " ".join(
        question["question_text"].lower() for question in questions
    )
    assert questions[0]["question_text"].startswith("A payment API")
    assert any("idempotency" in option["label"].lower() for option in questions[0]["options"])


def test_stage_one_generation_only_replaces_invalid_questions_after_repair(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        payload = _repaired_live_stage_payload(graph, stage=1)
        payload["questions"][2]["question_text"] = (
            f"How would you debug a failure in {payload['questions'][2]['subskill_key']}?"
        )
        return GemmaResponse(
            text="{}",
            payload=payload,
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=18,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=14,
            completion_tokens=19,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert calls["count"] == 2
    assert metadata.fallback_used is True
    assert metadata.error_code == "invalid_stage_question_contract"
    assert questions[0]["question_text"].startswith("You need to design an endpoint")
    assert "strongest engineering choice" not in questions[2]["question_text"].lower()
    assert "logs" in questions[2]["question_text"].lower() or "trace" in questions[2]["question_text"].lower()
    assert all(question["validation_flags"] == [] for question in questions)


def test_stage_one_generation_does_not_cache_fallback_questions(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        if calls["count"] == 1:
            raise AIServiceError("ollama chaos", details={"reason": "chaos"})
        return GemmaResponse(
            text="{}",
            payload=_stage_one_payload(graph),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=10,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    first_questions, first_metadata = AssessmentAIService.generate_stage_one("backend", graph)
    second_questions, second_metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert calls["count"] == 2
    assert first_metadata.fallback_used is True
    assert second_metadata.fallback_used is False
    assert second_metadata.model == "mock-gemma"
    assert first_metadata.source == "fallback"
    assert second_metadata.source == "llm"


def test_stage_one_generation_normalizes_live_like_string_options(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        payload = (
            _live_like_stage_payload(graph, stage=1)
            if calls["count"] == 1
            else _repaired_live_stage_payload(graph, stage=1)
        )
        return GemmaResponse(
            text="{}",
            payload=payload,
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=22,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=20,
            completion_tokens=24,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert metadata.fallback_used is False
    assert calls["count"] == 2
    assert questions[0]["interaction_mode"] == "single_select"
    assert _without_option_ids(questions[0]["options"]) == [
        {
            "value": "low",
            "label": "POST /users/update_profile",
            "score": 1,
        },
        {
            "value": "mid",
            "label": "PUT /users/{id}/profile",
            "score": 3,
        },
        {
            "value": "high",
            "label": "PATCH /users/{id}",
            "score": 5,
        },
    ]


def test_stage_one_generation_repairs_observed_live_payload_before_accepting_it(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=(
                _observed_live_stage_payload(graph, stage=1)
                if calls["count"] == 1
                else _repaired_live_stage_payload(graph, stage=1)
            ),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=58_248,
                model="mock-gemma",
                version=graph.version,
            ),
            prompt_tokens=182,
            completion_tokens=451,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert metadata.fallback_used is False
    assert calls["count"] == 2
    assert questions[0]["question_type"] == "single_choice"
    assert questions[0]["interaction_mode"] == "single_select"
    assert all(question["validation_flags"] == [] for question in questions)
    assert _without_option_ids(questions[0]["options"]) == [
        {
            "value": "low",
            "label": "POST /users/update_profile",
            "score": 1,
        },
        {
            "value": "mid",
            "label": "PUT /users/{id}/profile",
            "score": 3,
        },
        {
            "value": "high",
            "label": "PATCH /users/{id}",
            "score": 5,
        },
    ]


def test_stage_one_generation_uses_extended_timeout_floor(monkeypatch):
    graph = load_role_graph("backend")
    cache.clear()
    observed = {}

    class FakeClient:
        def __init__(self, *args, **kwargs):  # noqa: ANN002, ANN003
            observed["timeout_seconds"] = kwargs.get("timeout_seconds")
            observed["max_output_tokens"] = kwargs.get("max_output_tokens")

        def generate_structured(
            self,
            *,
            prompt,
            system="",
            required_keys=(),
            response_json_schema=None,
        ):  # noqa: ARG002
            return GemmaResponse(
                text="{}",
                payload=_stage_one_payload(graph),
                metadata=build_ai_metadata(
                    source="llm",
                    processing_time_ms=12,
                    model="mock-gemma",
                    version=graph.version,
                ),
                prompt_tokens=12,
                completion_tokens=24,
            )

    monkeypatch.setattr(AssessmentAIService, "client_class", FakeClient)

    questions, metadata = AssessmentAIService.generate_stage_one("backend", graph)

    assert metadata.fallback_used is False
    assert questions
    assert observed["timeout_seconds"] == 115
    assert observed["max_output_tokens"] == 3200



# ---------------------------------------------------------------------------
# Scenario corpus cache invalidation (specs/005-scenario-rag-corpus T022)
# ---------------------------------------------------------------------------


def test_stage_one_cache_key_excludes_scenario_corpus_version_when_flag_off(monkeypatch):
    monkeypatch.setattr(
        "apps.assessments.ai_pipeline.ASSESSMENT_SCENARIO_RAG_ENABLED", False
    )
    key = AssessmentAIService._stage_one_cache_key("backend", "curated-v1")
    assert key.endswith(":curated-v1"), (
        f"With the flag off, cache key should not append the corpus version. Got: {key}"
    )


def test_stage_one_cache_key_includes_scenario_corpus_version_when_flag_on(monkeypatch):
    from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION

    monkeypatch.setattr(
        "apps.assessments.ai_pipeline.ASSESSMENT_SCENARIO_RAG_ENABLED", True
    )
    key = AssessmentAIService._stage_one_cache_key("backend", "curated-v1")
    assert key.endswith(f":curated-v1:{SCENARIO_CORPUS_VERSION}"), (
        f"With the flag on, cache key should append SCENARIO_CORPUS_VERSION. Got: {key}"
    )


def test_stage_one_generation_invalidates_cache_on_scenario_corpus_version_bump(monkeypatch):
    """Bumping SCENARIO_CORPUS_VERSION must produce a different cache key and
    therefore a cache miss on the next stage-one generation."""
    monkeypatch.setattr(
        "apps.assessments.ai_pipeline.ASSESSMENT_SCENARIO_RAG_ENABLED", True
    )
    monkeypatch.setattr(
        "apps.assessments.ai_pipeline.SCENARIO_CORPUS_VERSION", "scenario-v1"
    )

    graph = load_role_graph("backend")
    cache.clear()
    calls = {"count": 0}

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        calls["count"] += 1
        return GemmaResponse(
            text="{}",
            payload=_stage_one_payload(graph),
            metadata=build_ai_metadata(
                source="llm",
                processing_time_ms=12,
                model="mock-gemma",
            ),
            prompt_tokens=10,
            completion_tokens=20,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    AssessmentAIService.generate_stage_one("backend", graph)
    # Same version: should hit the cache.
    AssessmentAIService.generate_stage_one("backend", graph)
    assert calls["count"] == 1

    # Bump corpus version: should miss the cache and regenerate.
    monkeypatch.setattr(
        "apps.assessments.ai_pipeline.SCENARIO_CORPUS_VERSION", "scenario-v2"
    )
    AssessmentAIService.generate_stage_one("backend", graph)
    assert calls["count"] == 2
