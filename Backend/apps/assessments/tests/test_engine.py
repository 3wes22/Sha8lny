from apps.assessments.engine import (
    AnswerScorer,
    GapProfileBuilder,
    Stage2Allocator,
    StageAllocator,
)
from apps.assessments.role_graph import load_role_graph


def test_stage_allocator_returns_five_distinct_targets():
    graph = load_role_graph("backend")

    targets = StageAllocator.allocate_stage_one(graph)

    assert len(targets) == 5
    assert len({target.key for target in targets}) == 5
    assert len({target.dimension for target in targets}) >= 4


def test_gap_profile_builder_prioritizes_large_gaps_and_uncertain_answers():
    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)

    questions = [
        {
            "id": f"s1_q{index + 1}",
            "stage": 1,
            "subskill_key": target.key,
            "dimension_key": target.dimension,
            "question_type": "multiple_choice" if index < 4 else "text",
            "interaction_mode": "single_select" if index < 4 else "text",
            "question_text": f"Question about {target.label}",
            "difficulty": 2 + index,
            "estimated_seconds": 45,
            "options": [
                {"value": "low", "label": "Low", "score": 1},
                {"value": "mid", "label": "Mid", "score": 3},
                {"value": "high", "label": "High", "score": 5},
            ],
        }
        for index, target in enumerate(targets)
    ]
    responses = [
        {"question_id": "s1_q1", "answer": "low"},
        {"question_id": "s1_q2", "answer": "mid"},
        {"question_id": "s1_q3", "answer": "high"},
        {"question_id": "s1_q4", "answer": "low"},
        {"question_id": "s1_q5", "answer": "brief"},
    ]

    evidence = AnswerScorer.score_stage(graph, questions, responses)
    gap_profile = GapProfileBuilder.build(graph, evidence)

    assert gap_profile.role_key == "backend"
    assert len(gap_profile.subskill_evidence) == 5
    assert targets[0].key in gap_profile.high_priority_gaps[:3]
    assert targets[-1].key in gap_profile.high_priority_gaps[:3]
    assert targets[-1].key in gap_profile.uncertain_areas
    assert 0 <= gap_profile.overall_calibration <= 100


def test_stage_two_allocator_includes_priority_gaps_and_uncertain_areas():
    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)
    evidence = [
        {
            "subskill_key": targets[0].key,
            "dimension_key": targets[0].dimension,
            "observed_level": 1.0,
            "target_level": 4,
            "gap": 3.0,
            "confidence": 0.82,
            "evidence_strength": "strong",
        },
        {
            "subskill_key": targets[1].key,
            "dimension_key": targets[1].dimension,
            "observed_level": 2.0,
            "target_level": 4,
            "gap": 2.0,
            "confidence": 0.58,
            "evidence_strength": "weak",
        },
    ]
    gap_profile = GapProfileBuilder.build(graph, evidence)

    stage_two_targets = Stage2Allocator.allocate_stage_two(graph, gap_profile)

    target_keys = [target.key for target in stage_two_targets]
    assert len(stage_two_targets) == 5
    assert targets[0].key in target_keys
    assert targets[1].key in target_keys


def _open_ended_question() -> dict:
    return {
        "id": "s2_q1",
        "stage": 2,
        "subskill_key": "decorators",
        "dimension_key": "python_fundamentals",
        "question_type": "open_ended",
        "stem": "Explain how functools.wraps preserves metadata.",
        "answer_key": {
            "expected_concepts": ["functools.wraps", "metadata", "signature"],
            "required_concept_count": 2,
            "forbidden_concepts": ["inline the logging"],
            "scoring": "concept_coverage",
        },
    }


def test_score_open_ended_uses_keyword_coverage_when_llm_disabled():
    question = _open_ended_question()
    # Default flag is off -> deterministic keyword coverage.
    score, confidence, method = AnswerScorer.score_open_ended(
        question, "functools.wraps copies the metadata and signature across."
    )
    assert method == "keyword_coverage"
    assert 1.0 <= score <= 5.0
    assert confidence > 0


def test_score_open_ended_uses_llm_rubric_when_enabled(monkeypatch):
    import apps.core.ai_settings as ai_settings
    import apps.core.gemma_client as gemma_module

    monkeypatch.setattr(ai_settings, "ASSESSMENT_RUBRIC_LLM_ENABLED", True, raising=False)

    class _FakeResult:
        payload = {"score": 4, "reasoning": "covers the key concepts"}

    class _FakeGemmaClient:
        def __init__(self, *args, **kwargs):
            pass

        def generate_structured(self, *args, **kwargs):
            return _FakeResult()

    monkeypatch.setattr(gemma_module, "GemmaClient", _FakeGemmaClient)

    score, confidence, method = AnswerScorer.score_open_ended(
        _open_ended_question(), "It keeps the wrapper's name and docstring."
    )
    assert method == "llm_rubric"
    assert score == 4.0
    assert confidence == 0.85


def test_score_open_ended_falls_back_when_llm_raises(monkeypatch):
    import apps.core.ai_settings as ai_settings
    import apps.core.gemma_client as gemma_module

    monkeypatch.setattr(ai_settings, "ASSESSMENT_RUBRIC_LLM_ENABLED", True, raising=False)

    class _BoomGemmaClient:
        def __init__(self, *args, **kwargs):
            pass

        def generate_structured(self, *args, **kwargs):
            raise RuntimeError("gemini unavailable")

    monkeypatch.setattr(gemma_module, "GemmaClient", _BoomGemmaClient)

    score, _confidence, method = AnswerScorer.score_open_ended(
        _open_ended_question(), "functools.wraps copies metadata and signature."
    )
    # On any LLM failure the deterministic keyword scorer takes over.
    assert method == "keyword_coverage"
    assert 1.0 <= score <= 5.0


def test_score_stage_records_scoring_method_on_open_ended_metadata():
    graph = load_role_graph("backend")
    question = _open_ended_question()
    question["subskill_key"] = StageAllocator.allocate_stage_one(graph)[0].key
    question["dimension_key"] = StageAllocator.allocate_stage_one(graph)[0].dimension
    responses = [{"question_id": "s2_q1", "answer": "functools.wraps copies metadata."}]

    AnswerScorer.score_stage(graph, [question], responses)

    assert question["generation_metadata"]["scoring_method"] == "keyword_coverage"


def test_answer_scorer_uses_answer_keys_for_typed_stage_items():
    graph = load_role_graph("backend")
    targets = StageAllocator.allocate_stage_one(graph)

    questions = [
        {
            "id": "s1_q1",
            "stage": 1,
            "subskill_key": targets[0].key,
            "dimension_key": targets[0].dimension,
            "question_type": "single_choice",
            "type": "multiple_choice",
            "interaction_mode": "single_select",
            "question_text": "Which endpoint shape best matches a partial user update?",
            "options": [
                {"id": "a", "value": "a", "label": "POST /users/update-profile"},
                {"id": "b", "value": "b", "label": "PATCH /users/{id}"},
                {"id": "c", "value": "c", "label": "GET /users/{id}?update=true"},
                {"id": "d", "value": "d", "label": "PUT /profiles/search"},
            ],
            "answer_key": {
                "correct_option_ids": ["b"],
                "scoring": "single_best",
            },
        },
        {
            "id": "s1_q2",
            "stage": 1,
            "subskill_key": targets[1].key,
            "dimension_key": targets[1].dimension,
            "question_type": "multi_select",
            "type": "multiple_choice",
            "interaction_mode": "multi_select",
            "question_text": "Select all schema decisions that preserve a normalized many-to-many relationship.",
            "options": [
                {"id": "a", "value": "a", "label": "OrderItems junction table"},
                {"id": "b", "value": "b", "label": "Duplicate product rows in Orders"},
                {"id": "c", "value": "c", "label": "Foreign keys from OrderItems to Orders and Products"},
                {"id": "d", "value": "d", "label": "Relationship quantity on OrderItems"},
            ],
            "answer_key": {
                "correct_option_ids": ["a", "c", "d"],
                "scoring": "partial_credit",
            },
        },
        {
            "id": "s1_q3",
            "stage": 1,
            "subskill_key": targets[2].key,
            "dimension_key": targets[2].dimension,
            "question_type": "open_ended",
            "type": "text",
            "interaction_mode": "text",
            "question_text": "Explain how you would instrument a distributed request path to diagnose latency spikes.",
            "answer_key": {
                "expected_concepts": [
                    "trace id",
                    "structured logging",
                    "latency percentiles",
                ],
                "required_concept_count": 2,
                "scoring": "concept_coverage",
            },
        },
    ]
    responses = [
        {"question_id": "s1_q1", "answer": "b"},
        {"question_id": "s1_q2", "answer": ["a", "c"]},
        {
            "question_id": "s1_q3",
            "answer": (
                "I would propagate a trace id through every service call, emit structured logging, "
                "and compare latency percentiles to isolate the slow hop."
            ),
        },
    ]

    evidence = AnswerScorer.score_stage(graph, questions, responses)

    assert len(evidence) == 3
    assert evidence[0].observed_level == 5.0
    assert evidence[0].confidence >= 0.85
    assert 3.0 <= evidence[1].observed_level < 5.0
    assert evidence[1].confidence >= 0.8
    assert evidence[2].observed_level >= 4.0
    assert evidence[2].confidence >= 0.7
