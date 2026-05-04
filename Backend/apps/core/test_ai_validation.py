from apps.assessments.ai_pipeline import _target_map
from apps.assessments.engine import StageAllocator
from apps.assessments.role_graph import load_role_graph
from apps.core.ai_validation import sanitize_stage_question_payload


def _backend_targets():
    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    return graph, targets, _target_map(graph, targets, stage=1)


def test_sanitize_stage_question_payload_flags_duplicate_stems_and_repeated_option_patterns():
    _, targets, allowed_targets = _backend_targets()

    raw_questions = [
        {
            "id": "s1_q1",
            "subskill_key": targets[0].key,
            "competency": targets[0].label,
            "learning_objective": "Choose the safest payment retry design.",
            "scenario_context": "A payment API receives duplicate client retries after a timeout.",
            "stem": "Which design best prevents a customer from being charged twice?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Require an idempotency key and replay the first successful result."},
                {"id": "b", "label": "Accept both requests and let finance reconcile duplicates overnight."},
                {"id": "c", "label": "Retry the charge immediately until the gateway confirms success."},
                {"id": "d", "label": "Store the request in cache without validating the request payload."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "The endpoint needs a deterministic deduplication mechanism at write time.",
        },
        {
            "id": "s1_q2",
            "subskill_key": targets[1].key,
            "competency": targets[1].label,
            "learning_objective": "Choose the safest payment retry design.",
            "scenario_context": "A payment API sees the same client retry after the caller times out.",
            "stem": "Which design best prevents a customer from being charged twice on a duplicate retry?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Require an idempotency key and replay the first successful result."},
                {"id": "b", "label": "Accept both requests and let finance reconcile duplicates overnight."},
                {"id": "c", "label": "Retry the charge immediately until the gateway confirms success."},
                {"id": "d", "label": "Store the request in cache without validating the request payload."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "The endpoint needs a deterministic deduplication mechanism at write time.",
        },
        {
            "id": "s1_q3",
            "subskill_key": targets[2].key,
            "competency": targets[2].label,
            "learning_objective": "Choose the strongest first observability action.",
            "scenario_context": "A checkout service shows intermittent 500s while the caller only sees rising latency.",
            "stem": "Which first step gives the fastest evidence about where the failure boundary is?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Correlate trace IDs with structured logs across the request path."},
                {"id": "b", "label": "Increase the autoscaling threshold before examining the incident."},
                {"id": "c", "label": "Add a cache layer in front of every dependency immediately."},
                {"id": "d", "label": "Lower application timeouts without checking dependency behavior."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "The first step should narrow the failure boundary with evidence.",
        },
        {
            "id": "s1_q4",
            "subskill_key": targets[3].key,
            "competency": targets[3].label,
            "learning_objective": "Translate requirements into measurable service behavior.",
            "scenario_context": "A PM asks for 'fast checkout' without defining what users should observe.",
            "stem": "Which acceptance criterion best turns that request into an engineering target?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Checkout feels fast to the team during manual testing."},
                {"id": "b", "label": "The team agrees to optimize later after the feature ships."},
                {"id": "c", "label": "P95 checkout latency stays under 600 ms for authenticated users at target traffic."},
                {"id": "d", "label": "The database CPU graph looks calmer after deployment."},
            ],
            "answer_key": {"correct_option_ids": ["c"], "scoring": "single_best"},
            "explanation": "Acceptance criteria should be observable, measurable, and tied to user-facing behavior.",
        },
        {
            "id": "s1_q5",
            "subskill_key": targets[4].key,
            "competency": targets[4].label,
            "learning_objective": "Choose the strongest boundary for an early service split.",
            "scenario_context": "A monolith team wants to split order fulfillment from account management.",
            "stem": "Which signal most strongly suggests these areas deserve separate services?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "They use different code formatting preferences."},
                {"id": "b", "label": "They have separate business workflows and ownership boundaries."},
                {"id": "c", "label": "One package has more files than the rest of the repository."},
                {"id": "d", "label": "One team wants to rewrite its part in a different language."},
            ],
            "answer_key": {"correct_option_ids": ["b"], "scoring": "single_best"},
            "explanation": "Ownership and workflow boundaries are stronger signals than incidental code structure.",
        },
    ]

    questions = sanitize_stage_question_payload(
        raw_questions,
        stage=1,
        allowed_targets=allowed_targets,
    )

    assert "duplicate_question_stem" not in questions[0]["validation_flags"]
    assert "duplicate_question_stem" in questions[1]["validation_flags"]
    assert "repeated_option_pattern" in questions[1]["validation_flags"]


def test_sanitize_stage_question_payload_flags_obvious_weak_distractors():
    _, targets, allowed_targets = _backend_targets()

    raw_questions = [
        {
            "id": "s1_q1",
            "subskill_key": targets[0].key,
            "competency": targets[0].label,
            "learning_objective": "Choose the strongest debugging step for an API incident.",
            "scenario_context": "A payment endpoint is returning intermittent 500s after a recent deploy.",
            "stem": "Which next step is most likely to isolate the cause without hiding evidence?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Review structured logs and dependency health for the failing request path."},
                {"id": "b", "label": "Disable logging so the service can spend more CPU on request handling."},
                {"id": "c", "label": "Rollback immediately without checking whether the deploy caused the issue."},
                {"id": "d", "label": "Increase retry counts for clients before measuring the failure mode."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "The first step should preserve evidence and narrow the failure boundary.",
        },
        {
            "id": "s1_q2",
            "subskill_key": targets[1].key,
            "competency": targets[1].label,
            "learning_objective": "Choose the correct normalization strategy.",
            "scenario_context": "An order can include multiple products and each product can appear on many orders.",
            "stem": "Which schema design fits that relationship?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Create an OrderItems junction table with foreign keys to Orders and Products."},
                {"id": "b", "label": "Copy every product column directly onto the Orders table."},
                {"id": "c", "label": "Store only the latest product ID on Orders and ignore the rest."},
                {"id": "d", "label": "Replace product references with free-form text descriptions."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "The relationship requires a junction table to stay normalized and queryable.",
        },
        {
            "id": "s1_q3",
            "subskill_key": targets[2].key,
            "competency": targets[2].label,
            "learning_objective": "Choose the strongest observability signal.",
            "scenario_context": "A critical backend call occasionally spikes to 4 seconds across three services.",
            "stem": "Which signal is most useful for locating where the latency accumulates?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "End-to-end trace spans with per-hop latency and request IDs."},
                {"id": "b", "label": "The total number of INFO log lines written per minute."},
                {"id": "c", "label": "The number of open browser tabs on the on-call engineer's laptop."},
                {"id": "d", "label": "The color theme of the monitoring dashboard."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "Trace spans expose where latency accumulates across service boundaries.",
        },
        {
            "id": "s1_q4",
            "subskill_key": targets[3].key,
            "competency": targets[3].label,
            "learning_objective": "Translate product language into measurable criteria.",
            "scenario_context": "A stakeholder says the feature should be 'reliable' before launch.",
            "stem": "Which follow-up turns that into an actionable engineering target?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Define an SLO for success rate and latency over the launch traffic profile."},
                {"id": "b", "label": "Promise to make the code cleaner than the last release."},
                {"id": "c", "label": "Wait to define reliability until the first customer complains."},
                {"id": "d", "label": "Ask the team to use more careful judgment during deployment."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "The requirement needs measurable service-level behavior, not vague intent.",
        },
        {
            "id": "s1_q5",
            "subskill_key": targets[4].key,
            "competency": targets[4].label,
            "learning_objective": "Choose the strongest microservice boundary signal.",
            "scenario_context": "A team is splitting a monolith into independently deployable services.",
            "stem": "Which criterion should guide the first service boundary decision?",
            "question_type": "single_choice",
            "options": [
                {"id": "a", "label": "Business capability ownership and bounded context."},
                {"id": "b", "label": "Which module has the oldest comments."},
                {"id": "c", "label": "Which package has the fewest unit tests today."},
                {"id": "d", "label": "Which team prefers a different programming language."},
            ],
            "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
            "explanation": "Domain ownership is a stronger boundary than incidental code traits.",
        },
    ]

    questions = sanitize_stage_question_payload(
        raw_questions,
        stage=1,
        allowed_targets=allowed_targets,
    )

    assert "weak_distractor_detected" in questions[0]["validation_flags"]
