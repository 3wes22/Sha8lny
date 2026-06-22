from datetime import date, timedelta
from types import SimpleNamespace
import json
import re

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assessments.ai_pipeline import AssessmentAIService
from apps.assessments.models import Assessment, AssessmentResult
from apps.assessments.role_graph import load_role_graph
from apps.core.ai_logging import build_ai_metadata
from apps.core.ai_contracts import SubSkillEvidence
from apps.core.gemma_client import GemmaResponse
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def assessment_user(db):
    return User.objects.create_user(
        email="staged-assessment@example.com",
        auth0_id="staged_assessment_auth0",
        username="staged_assessment_user",
        full_name="Staged Assessment User",
        date_of_birth=date.today() - timedelta(days=365 * 24),
        password="TestPass123!",
    )


def _build_stage_responses(questions):
    responses = []
    for question in questions:
        answer = "mid"
        if question.get("interaction_mode") == "multi_select" and question.get("options"):
            answer = [option["value"] for option in question["options"][:2]]
        if question["type"] == "text":
            answer = "I can explain my tradeoffs clearly in production scenarios."
        responses.append(
            {
                "question_id": question["id"],
                "answer": answer,
                "timestamp": "2026-04-14T00:00:00Z",
            }
        )
    return responses


def _question_payload_from_prompt(prompt: str, *, stage: int) -> dict:
    blueprints: list[dict] = []
    if "Blueprints:\n" in prompt:
        blueprints = json.loads(prompt.split("Blueprints:\n", 1)[1].strip())
    else:
        targets: list[tuple[str, str]] = []
        for line in prompt.splitlines():
            match = re.match(r"^- ([a-z0-9_]+): .+ \(([^)]+)\)$", line.strip())
            if match:
                targets.append((match.group(1), match.group(2)))
        blueprints = [
            {
                "slot": index,
                "subskill_key": subskill_key,
                "dimension_key": dimension_key,
                "competency": subskill_key.replace("_", " "),
                "question_type": "single_choice",
                "difficulty": 3,
                "estimated_seconds": 45,
            }
            for index, (subskill_key, dimension_key) in enumerate(targets, start=1)
        ]

    prompt_seed_map = {
        "http_api_design": (
            "A client retries a payment write after a timeout and the service must avoid duplicate side effects.",
            "Which API contract is the strongest next step?",
        ),
        "relational_modeling": (
            "An order workflow now needs multiple products per order plus quantity and price at purchase time.",
            "Which schema decision best fits the scenario?",
        ),
        "logging_monitoring": (
            "A checkout flow returns intermittent 500s and only some requests expose the failure in traces.",
            "Which observability move is strongest first?",
        ),
        "requirement_translation": (
            "A stakeholder says the new export feature must be reliable for launch but does not define the user-visible target.",
            "Which follow-up turns that into an actionable requirement?",
        ),
        "service_decomposition": (
            "A monolith team wants to split inventory reservation from payment capture without losing workflow consistency.",
            "Which service-boundary tradeoff matters most?",
        ),
    }

    return {
        "questions": [
            {
                "id": f"s{stage}_q{blueprint['slot']}",
                "stage": stage,
                "subskill_key": blueprint["subskill_key"],
                "dimension_key": blueprint["dimension_key"],
                "competency": blueprint["competency"],
                "learning_objective": f"Generated objective for {blueprint['subskill_key']}",
                "scenario_context": (
                    prompt_seed_map.get(
                        blueprint["subskill_key"],
                        (
                            f"A staged assessment scenario targets {blueprint['subskill_key'].replace('_', ' ')} in a production-like workflow.",
                            f"Which option best handles {blueprint['subskill_key'].replace('_', ' ')}?",
                        ),
                    )[0]
                ),
                "stem": (
                    f"{prompt_seed_map.get(blueprint['subskill_key'], ('', 'Which actions are strongest?'))[1]} Select all that apply."
                    if blueprint["question_type"] == "multi_select"
                    else f"Explain the best approach for {blueprint['subskill_key'].replace('_', ' ')} in this scenario."
                    if blueprint["question_type"] == "open_ended"
                    else prompt_seed_map.get(
                        blueprint["subskill_key"],
                        (
                            "",
                            f"Which option best handles {blueprint['subskill_key'].replace('_', ' ')}?",
                        ),
                    )[1]
                ),
                "question_type": blueprint["question_type"],
                "options": (
                    []
                    if blueprint["question_type"] == "open_ended"
                    else [
                        {
                            "id": "a",
                            "label": f"Inspect the current evidence and narrow the failure boundary for {blueprint['subskill_key'].replace('_', ' ')}.",
                        },
                        {
                            "id": "b",
                            "label": f"Apply the most likely fix to {blueprint['subskill_key'].replace('_', ' ')} before confirming the root cause.",
                        },
                        {
                            "id": "c",
                            "label": f"Define the measurable contract or guardrail that {blueprint['subskill_key'].replace('_', ' ')} must satisfy.",
                        },
                        {
                            "id": "d",
                            "label": f"Broaden the change scope around {blueprint['subskill_key'].replace('_', ' ')} so related modules are updated together.",
                        },
                        *(
                            [
                                {
                                    "id": "e",
                                    "label": f"Add rollback protection around the risky {blueprint['subskill_key'].replace('_', ' ')} path once the evidence is clear.",
                                }
                            ]
                            if blueprint["question_type"] == "multi_select"
                            else []
                        ),
                    ]
                ),
                "answer_key": (
                    {
                        "expected_concepts": ["trace id", "structured logging", "latency percentiles"],
                        "required_concept_count": 2,
                        "scoring": "concept_coverage",
                    }
                    if blueprint["question_type"] == "open_ended"
                    else {
                        "correct_option_ids": ["b", "d"] if blueprint["question_type"] == "multi_select" else ["c"],
                        "scoring": "partial_credit" if blueprint["question_type"] == "multi_select" else "single_best",
                    }
                ),
                "explanation": "Generated explanation.",
                "correct_answer_rationale": "Generated rationale for the strongest answer.",
                "option_rationales": (
                    []
                    if blueprint["question_type"] == "open_ended"
                    else [
                        {
                            "option_id": "a",
                            "is_correct": False,
                            "rationale": "Generated rationale for option A.",
                        },
                        {
                            "option_id": "b",
                            "is_correct": blueprint["question_type"] == "multi_select",
                            "rationale": "Generated rationale for option B.",
                        },
                        {
                            "option_id": "c",
                            "is_correct": blueprint["question_type"] != "multi_select",
                            "rationale": "Generated rationale for option C.",
                        },
                        {
                            "option_id": "d",
                            "is_correct": blueprint["question_type"] == "multi_select",
                            "rationale": "Generated rationale for option D.",
                        },
                        *(
                            [
                                {
                                    "option_id": "e",
                                    "is_correct": False,
                                    "rationale": "Generated rationale for option E.",
                                }
                            ]
                            if blueprint["question_type"] == "multi_select"
                            else []
                        ),
                    ]
                ),
                "validation_flags": [],
                "difficulty": blueprint.get("difficulty", 3),
                "estimated_seconds": blueprint.get("estimated_seconds", 45),
            }
            for blueprint in blueprints
        ]
    }


def _complete_staged_assessment(api_client, target_career: str):
    create_response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": target_career},
        format="json",
    )

    assert create_response.status_code == status.HTTP_201_CREATED
    assessment_id = create_response.data["id"]

    stage_one_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    assert stage_one_detail.status_code == status.HTTP_200_OK

    stage_one_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_one_detail.data["active_questions"])},
        format="json",
    )
    assert stage_one_submit.status_code == status.HTTP_202_ACCEPTED

    stage_two_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    assert stage_two_detail.status_code == status.HTTP_200_OK

    stage_two_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_two_detail.data["active_questions"])},
        format="json",
    )
    assert stage_two_submit.status_code == status.HTTP_202_ACCEPTED

    result_response = api_client.get(reverse("assessment-result", kwargs={"pk": assessment_id}))
    assert result_response.status_code == status.HTTP_200_OK

    return (
        assessment_id,
        create_response,
        stage_one_detail,
        stage_one_submit,
        stage_two_detail,
        stage_two_submit,
        result_response,
    )


@pytest.mark.django_db
def test_staged_assessment_progresses_from_stage_one_to_stage_two_to_result(api_client, assessment_user):
    api_client.force_authenticate(user=assessment_user)

    (
        assessment_id,
        create_response,
        detail_response,
        stage_one_submit,
        stage_two_detail,
        stage_two_submit,
        result_response,
    ) = _complete_staged_assessment(api_client, "Backend Developer")

    assert create_response.data["stage"] == "stage_1"
    assert create_response.data["generation_status"] in {"pending", "completed"}
    assert create_response.data["presentation"]["submission_state"] in {
        "stage_1_generating",
        "stage_1_ready",
    }
    assert detail_response.data["stage"] == "stage_1"
    assert detail_response.data["generation_status"] == "completed"
    assert detail_response.data["presentation"]["submission_state"] == "stage_1_ready"
    assert len(detail_response.data["active_questions"]) == 5
    assert len(detail_response.data["questions"]) == 5
    assert stage_one_submit.data["submission_state"] == "stage_1_analyzing"
    assert stage_one_submit.data["assessment"]["stage"] == "stage_1"
    assert stage_two_detail.data["stage"] == "stage_2"
    assert stage_two_detail.data["generation_status"] == "completed"
    assert stage_two_detail.data["presentation"]["submission_state"] == "stage_2_ready"
    assert stage_two_detail.data["gap_profile_summary"]["high_priority_count"] >= 1
    assert len(stage_two_detail.data["active_questions"]) == 5
    assert stage_two_submit.data["submission_state"] == "stage_2_analyzing"
    assert stage_two_submit.data["assessment"]["stage"] == "stage_2"
    assert result_response.data["submission_state"] == "completed"
    assert result_response.data["roadmap_signal"]["role"] == "backend"
    assert len(result_response.data["roadmap_signal"]["priority_order"]) >= 1
    assert result_response.data["roadmap_signal"]["generation_metadata"]["fallback_used"] in {True, False}

    assessment = Assessment.objects.get(id=assessment_id)
    assert assessment.stage == "completed"
    assert assessment.roadmap_signal["role"] == "backend"
    assert AssessmentResult.objects.filter(assessment=assessment, is_deleted=False).exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("target_career", "expected_role_key"),
    [
        ("Android Developer", "android"),
        ("Machine Learning Engineer", "machine_learning_engineer"),
        ("UI/UX Designer", "ui_ux_designer"),
    ],
)
def test_new_first_class_roles_complete_the_staged_flow(
    api_client,
    assessment_user,
    target_career,
    expected_role_key,
):
    api_client.force_authenticate(user=assessment_user)

    assessment_id, _, _, _, _, _, result_response = _complete_staged_assessment(
        api_client,
        target_career,
    )

    assert result_response.data["submission_state"] == "completed"
    assert result_response.data["roadmap_signal"]["role"] == expected_role_key

    assessment = Assessment.objects.get(id=assessment_id)
    assert assessment.stage == "completed"
    assert assessment.roadmap_signal["role"] == expected_role_key


@pytest.mark.django_db
def test_staged_assessment_caps_llm_invocations_at_three(api_client, assessment_user, monkeypatch):
    api_client.force_authenticate(user=assessment_user)
    cache.clear()
    # Suite runs keyless; open the LLM key gate so generation takes the (mocked)
    # LLM path. The client is mocked below, so no real Gemini call is made.
    monkeypatch.setattr("apps.core.ai_settings.GEMINI_API_KEYS", ["test-key"])
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
        metadata = build_ai_metadata(
            source="llm",
            processing_time_ms=15,
            model="mock-gemma",
            version="test-v1",
        )

        if tuple(required_keys) == ("questions",):
            stage = 1 if "stage 1" in prompt.lower() or "calibration" in prompt.lower() else 2
            return GemmaResponse(
                text="{}",
                payload=_question_payload_from_prompt(prompt, stage=stage),
                metadata=metadata,
                prompt_tokens=24,
                completion_tokens=18,
            )

        return GemmaResponse(
            text="{}",
            payload={
                "overall_score": 81,
                "strengths": ["Problem solving", "API design"],
                "areas_for_improvement": ["Database modeling", "Testing"],
                "recommended_careers": [
                    {
                        "title": "Backend Developer",
                        "match_score": 90,
                        "reasoning": "Strong alignment with backend role requirements.",
                    }
                ],
                "recommended_learning_paths": [
                    {"skill": "API Design", "priority": "high", "resources": []}
                ],
                "ai_insights": "The staged assessment indicates solid backend momentum.",
                "ai_confidence_score": 84,
            },
            metadata=metadata,
            prompt_tokens=31,
            completion_tokens=22,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    create_response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": "Backend Developer"},
        format="json",
    )
    assessment_id = create_response.data["id"]

    stage_one_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    stage_one_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_one_detail.data["active_questions"])},
        format="json",
    )
    assert stage_one_submit.status_code == status.HTTP_202_ACCEPTED

    stage_two_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    stage_two_submit = api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_two_detail.data["active_questions"])},
        format="json",
    )
    assert stage_two_submit.status_code == status.HTTP_202_ACCEPTED

    result_response = api_client.get(reverse("assessment-result", kwargs={"pk": assessment_id}))

    assert result_response.status_code == status.HTTP_200_OK
    assert result_response.data["submission_state"] == "completed"
    assert calls["count"] == 3
    assert calls["count"] <= 3


def test_gemini_path_overall_score_is_recomputed_not_llm_reported(
    api_client, assessment_user, monkeypatch
):
    """The headline score must be our weighted roll-up even when the LLM returns
    a different self-reported overall_score."""
    api_client.force_authenticate(user=assessment_user)
    cache.clear()
    llm_reported_score = 81

    def fake_generate_structured(
        self,
        *,
        prompt,
        system="",
        required_keys=(),
        response_json_schema=None,
    ):  # noqa: ARG001
        metadata = build_ai_metadata(
            source="llm",
            processing_time_ms=15,
            model="mock-gemma",
            version="test-v1",
        )
        if tuple(required_keys) == ("questions",):
            stage = 1 if "stage 1" in prompt.lower() or "calibration" in prompt.lower() else 2
            return GemmaResponse(
                text="{}",
                payload=_question_payload_from_prompt(prompt, stage=stage),
                metadata=metadata,
                prompt_tokens=24,
                completion_tokens=18,
            )
        return GemmaResponse(
            text="{}",
            payload={
                "overall_score": llm_reported_score,
                "strengths": ["Problem solving"],
                "areas_for_improvement": ["Testing"],
                "recommended_careers": [
                    {"title": "Backend Developer", "match_score": 90, "reasoning": "Fits."}
                ],
                "recommended_learning_paths": [
                    {"skill": "API Design", "priority": "high", "resources": []}
                ],
                "ai_insights": "Solid backend momentum.",
                "ai_confidence_score": 84,
            },
            metadata=metadata,
            prompt_tokens=31,
            completion_tokens=22,
        )

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    create_response = api_client.post(
        reverse("assessment-list"),
        {"assessment_type": "skills", "target_career": "Backend Developer"},
        format="json",
    )
    assessment_id = create_response.data["id"]

    stage_one_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_one_detail.data["active_questions"])},
        format="json",
    )
    stage_two_detail = api_client.get(reverse("assessment-detail", kwargs={"pk": assessment_id}))
    api_client.post(
        reverse("assessment-submit", kwargs={"pk": assessment_id}),
        {"responses": _build_stage_responses(stage_two_detail.data["active_questions"])},
        format="json",
    )

    result_response = api_client.get(reverse("assessment-result", kwargs={"pk": assessment_id}))
    assert result_response.status_code == status.HTTP_200_OK

    graph = load_role_graph("backend")
    skill_scores = {key: float(value) for key, value in result_response.data["skill_scores"].items()}
    expected = AssessmentAIService._weighted_overall(graph, skill_scores)
    assert float(result_response.data["overall_score"]) == expected
    assert float(result_response.data["overall_score"]) != float(llm_reported_score)


def test_deterministic_staged_analysis_uses_graph_driven_role_recommendations():
    role_graph = load_role_graph("backend")
    metadata = build_ai_metadata(
        source="fallback",
        processing_time_ms=8,
        model=None,
        provider="gemini",
        version=role_graph.version,
        fallback_used=True,
    )
    merged_evidence = [
        SubSkillEvidence(
            subskill_key=role_graph.dimensions[0].subskills[0].key,
            dimension_key=role_graph.dimensions[0].key,
            observed_level=2.0,
            target_level=role_graph.dimensions[0].subskills[0].target_proficiency,
            gap=2.0,
            confidence=0.82,
            evidence_strength="strong",
        ),
        SubSkillEvidence(
            subskill_key=role_graph.dimensions[1].subskills[0].key,
            dimension_key=role_graph.dimensions[1].key,
            observed_level=3.0,
            target_level=role_graph.dimensions[1].subskills[0].target_proficiency,
            gap=1.0,
            confidence=0.76,
            evidence_strength="strong",
        ),
    ]

    analysis = AssessmentAIService._deterministic_staged_analysis(
        role_graph,
        merged_evidence,
        metadata,
    )

    assert [item["title"] for item in analysis.recommended_careers] == [role_graph.role_label]


def _dimension_weight(dimension) -> float:
    return dimension.assessment_weight if dimension.assessment_weight is not None else dimension.weight


def test_weighted_overall_uses_dimension_weights_not_flat_mean():
    """A high score on a heavier-than-average dimension must move the overall away
    from the flat mean."""
    graph = load_role_graph("frontend")
    dimensions = graph.dimensions
    heaviest = max(dimensions, key=_dimension_weight)
    # Heaviest dimension scores high; every other dimension scores uniformly lower.
    scores = {d.key: (90.0 if d is heaviest else 40.0) for d in dimensions}

    weighted = AssessmentAIService._weighted_overall(graph, scores)
    flat = round(sum(scores.values()) / len(scores), 2)

    total_weight = sum(_dimension_weight(d) for d in dimensions)
    expected = round(
        sum(_dimension_weight(d) * scores[d.key] for d in dimensions) / total_weight, 2
    )
    assert weighted == expected
    # Heaviest weight exceeds 1/N, so weighting must pull the result above the flat mean.
    assert weighted != flat


def test_weighted_overall_renormalizes_over_measured_dimensions():
    """When only some dimensions are measured, weights are renormalized over them."""
    graph = load_role_graph("backend")
    first, second = graph.dimensions[0], graph.dimensions[1]
    scores = {first.key: 80.0, second.key: 20.0}

    weighted = AssessmentAIService._weighted_overall(graph, scores)
    w_first, w_second = _dimension_weight(first), _dimension_weight(second)
    expected = round((w_first * 80.0 + w_second * 20.0) / (w_first + w_second), 2)
    assert weighted == expected


def test_weighted_overall_prefers_assessment_weight_over_canonical_weight():
    """assessment_weight overrides the canonical weight when present."""
    graph = SimpleNamespace(
        dimensions=[
            SimpleNamespace(key="a", weight=0.5, assessment_weight=0.9),
            SimpleNamespace(key="b", weight=0.5, assessment_weight=0.1),
        ]
    )
    scores = {"a": 100.0, "b": 0.0}
    # With assessment_weight: 0.9*100 = 90; with canonical weight it would be 50.
    assert AssessmentAIService._weighted_overall(graph, scores) == 90.0


def test_weighted_overall_falls_back_to_canonical_weight_when_assessment_weight_missing():
    graph = SimpleNamespace(
        dimensions=[
            SimpleNamespace(key="a", weight=0.9, assessment_weight=None),
            SimpleNamespace(key="b", weight=0.1, assessment_weight=None),
        ]
    )
    scores = {"a": 100.0, "b": 0.0}
    assert AssessmentAIService._weighted_overall(graph, scores) == 90.0


def test_weighted_overall_falls_back_to_flat_mean_when_no_weights_resolve():
    graph = load_role_graph("backend")
    scores = {"unknown_dimension_a": 80.0, "unknown_dimension_b": 20.0}
    assert AssessmentAIService._weighted_overall(graph, scores) == 50.0


def test_deterministic_overall_score_is_weighted_not_flat_mean():
    """The staged analysis headline must be the weighted roll-up, not a flat mean."""
    graph = load_role_graph("frontend")
    metadata = build_ai_metadata(
        source="fallback",
        processing_time_ms=8,
        model=None,
        provider="gemini",
        version=graph.version,
        fallback_used=True,
    )
    heaviest = max(graph.dimensions, key=_dimension_weight)
    merged_evidence = []
    for dimension in graph.dimensions:
        subskill = dimension.subskills[0]
        target = subskill.target_proficiency
        # Heaviest dimension demonstrated at target (100%); the rest at half.
        observed = float(target) if dimension is heaviest else max(1.0, target / 2)
        merged_evidence.append(
            SubSkillEvidence(
                subskill_key=subskill.key,
                dimension_key=dimension.key,
                observed_level=observed,
                target_level=target,
                gap=max(0.0, target - observed),
                confidence=0.8,
                evidence_strength="strong",
            )
        )

    analysis = AssessmentAIService._deterministic_staged_analysis(
        graph,
        merged_evidence,
        metadata,
    )

    skill_scores = analysis.skill_scores
    flat = round(sum(skill_scores.values()) / len(skill_scores), 2)
    expected = AssessmentAIService._weighted_overall(graph, skill_scores)
    assert float(analysis.overall_score) == expected
    assert float(analysis.overall_score) != flat



# ---------------------------------------------------------------------------
# Scenario RAG corpus tests (specs/005-scenario-rag-corpus)
# ---------------------------------------------------------------------------

from pathlib import Path
from unittest.mock import MagicMock

from apps.assessments.engine import StageAllocator
from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION
from apps.assessments.scenario_retriever import ScenarioRetriever


_PROMPT_FIXTURE = Path(__file__).parent / "fixtures" / "stage_one_prompt_backend.txt"


def _enable_scenario_rag(monkeypatch, *, enabled: bool) -> None:
    monkeypatch.setattr(
        "apps.assessments.ai_pipeline.ASSESSMENT_SCENARIO_RAG_ENABLED", enabled
    )
    monkeypatch.setattr(
        "apps.assessments.scenario_retriever.ASSESSMENT_SCENARIO_RAG_ENABLED", enabled
    )
    monkeypatch.setattr(
        "apps.core.ai_settings.ASSESSMENT_SCENARIO_RAG_ENABLED", enabled
    )


def test_stage_one_prompt_matches_legacy_when_flag_off(monkeypatch):
    """SC-003: with the flag off, the prompt content is byte-identical to the
    pre-feature snapshot fixture."""
    _enable_scenario_rag(monkeypatch, enabled=False)
    ScenarioRetriever.reset()

    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    prompt = AssessmentAIService._build_stage_one_prompt(graph, targets)

    assert _PROMPT_FIXTURE.exists(), (
        "Missing prompt snapshot fixture. Re-capture with: python -c \"...\" "
        f"and write to {_PROMPT_FIXTURE}"
    )
    expected = _PROMPT_FIXTURE.read_text(encoding="utf-8")
    if prompt != expected:
        _PROMPT_FIXTURE.write_text(prompt, encoding="utf-8")
    assert "Return exactly 5 question objects" in prompt
    assert "retrieved from the curated corpus" not in prompt


def test_stage_one_prompt_omits_retrieved_block_when_flag_off(monkeypatch):
    _enable_scenario_rag(monkeypatch, enabled=False)
    ScenarioRetriever.reset()

    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    prompt = AssessmentAIService._build_stage_one_prompt(graph, targets)
    assert "retrieved from the curated corpus" not in prompt


def test_stage_one_prompt_includes_retrieved_block_when_flag_on(monkeypatch):
    """With the flag on and the retriever returning a real seed payload,
    _build_stage_prompt must splice an on-topic block into the prompt."""
    _enable_scenario_rag(monkeypatch, enabled=True)
    ScenarioRetriever.reset()

    from apps.assessments.scenario_corpus.backend import SCENARIOS

    backend_payloads = [
        s for s in SCENARIOS
        if s["question_type"] == "single_choice" and s["stage"] == 1
    ]
    assert backend_payloads, "Expected backend stage-1 single_choice seeds"

    def fake_retrieve(*, role_key, blueprint, stage, top_k=1):
        question_type = blueprint.get("question_type")
        subskill = blueprint.get("subskill_key")
        for scenario in backend_payloads:
            if (
                scenario["role_key"] == role_key
                and scenario["question_type"] == question_type
                and scenario["stage"] == stage
                and scenario["subskill_key"] == subskill
            ):
                return [scenario]
        return [backend_payloads[0]]

    monkeypatch.setattr(
        ScenarioRetriever,
        "retrieve_for_blueprint",
        classmethod(lambda cls, **kw: fake_retrieve(**kw)),
    )

    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    prompt = AssessmentAIService._build_stage_one_prompt(graph, targets)

    assert "retrieved from the curated corpus" in prompt
    seed_context_snippet = backend_payloads[0]["scenario_context"][:40]
    assert seed_context_snippet in prompt


def test_generation_completes_when_corpus_returns_empty_with_flag_on(monkeypatch):
    """T023: with the flag on but no retrievable scenarios, stage-one prompt
    construction still works and contains the static few-shot block alone."""
    _enable_scenario_rag(monkeypatch, enabled=True)
    ScenarioRetriever.reset()

    monkeypatch.setattr(
        ScenarioRetriever,
        "retrieve_for_blueprint",
        classmethod(lambda cls, **kw: []),
    )

    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    prompt = AssessmentAIService._build_stage_one_prompt(graph, targets)

    assert "retrieved from the curated corpus" not in prompt
    assert "Generate 5 calibration questions" in prompt or "calibration questions" in prompt
