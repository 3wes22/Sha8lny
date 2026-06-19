# Authoring Scenarios for the Assessment Scenario Corpus

This guide is the single contract between content authors and the runtime
retriever. If a scenario passes every check in this guide and
`python manage.py scenario_corpus_audit` returns OK, it is safe to ship.

## What this corpus is and is not

- **Is**: An additive, retrievable few-shot example layer for the LLM
  question generator. Used only when
  `ASSESSMENT_SCENARIO_RAG_ENABLED=true`, and only as a stylistic
  reference inside the prompt.
- **Is not**: A replacement for `BACKEND_FALLBACK_SCENARIOS`. That dict
  is the deterministic safety net for failed LLM generations and is
  unrelated to this corpus.
- **Is not**: A place to dump generic CS quiz questions. Every entry
  must be scenario-shaped and on-topic for one approved role and one
  approved subskill.

## File layout

```
Backend/apps/assessments/scenario_corpus/
├── schema.py              # ScenarioDocument TypedDict + validate_scenario()
├── registry.py            # SCENARIO_CORPUS_VERSION + iter_*()
├── backend.py             # role-keyed authored content
├── frontend.py
├── fullstack.py
├── data_science.py
├── devops.py
├── android.py
├── machine_learning_engineer.py
└── ui_ux_designer.py
```

Edit the role-keyed module you are authoring for. Append new
`ScenarioDocument` dict literals to its module-level `SCENARIOS` list.

## Required fields

Every scenario must declare all of the following. See `schema.py` for the
TypedDict and `specs/005-scenario-rag-corpus/data-model.md` for the full
rule set.

| Field | Rule |
|---|---|
| `doc_id` | Stable, lowercase, matches `<role>.<subskill>.s[12].<question_type>.<slug>`. Unique across the corpus. |
| `role_key` | One of the eight approved roles. Must exist in `ROLE_GRAPHS`. |
| `subskill_key` | Must exist within the role's curated `RoleGraph`. |
| `competency` | Must equal the matching `SubSkill.label` exactly. |
| `dimension_key` | Must equal the matching `SubSkill.dimension`. |
| `stage` | `1` (calibration) or `2` (targeted follow-up). |
| `question_type` | `single_choice` \| `multi_select` \| `open_ended`. |
| `difficulty` | Integer in `[1, 5]`. Stage 1 ≈ 3, Stage 2 ≈ 4. |
| `estimated_seconds` | Integer in `[30, 120]`. |
| `learning_objective` | One sentence describing what the question evaluates. |
| `scenario_context` | One or two sentences describing a concrete engineering scenario. No abstractions. |
| `stem` | The decision prompt. For `multi_select`, must end with `"Select all that apply."`. |
| `options` | `single_choice`: exactly 4; `multi_select`: exactly 5; `open_ended`: empty list. |
| `answer_key` | Shape depends on question_type (see below). |
| `explanation` | Short prose explanation of the intended answer. |
| `correct_answer_rationale` | One sentence on why the correct answer is best. |
| `option_rationales` | One entry per option (closed types). Exactly one `is_correct=True` for `single_choice`; 2 or 3 for `multi_select`. Empty list for `open_ended`. |
| `helper` | Optional one-sentence hint. |
| `author` | Your handle or a source string. |
| `license` | `"internal"` for authored content. |
| `review_status` | `"draft"` while authoring; `"approved"` only after review. |
| `created_at` | `YYYY-MM-DD`. |
| `corpus_version` | Must equal the current `SCENARIO_CORPUS_VERSION` in `registry.py`. |

### answer_key shape by question_type

| `question_type` | Required keys |
|---|---|
| `single_choice` | `correct_option_ids` (list of length 1), `scoring: "single_best"` |
| `multi_select` | `correct_option_ids` (list of length 2 or 3), `scoring: "partial_credit"` |
| `open_ended` | `expected_concepts` (list of length 3), `required_concept_count` (`int` in `[1, 5]`), `forbidden_concepts` (list of length 1), `scoring: "concept_coverage"` |

## Content quality bar

Every scenario must:

1. **Open with a concrete scenario.** Name a system, a failure, a code
   review finding, a requirements conflict. No "Which option is the
   strongest engineering choice?" stems.
2. **Pose a decision, not a definition.** The reader must choose between
   real tradeoffs. Definitions belong in a glossary, not here.
3. **Have plausible distractors.** Every wrong option must be something
   a junior could plausibly pick. No joke or sabotage answers.
4. **Have parallel options.** All options for a closed question must be
   the same shape and length. The reader should not be able to identify
   the correct answer by pattern matching.
5. **Avoid banned low-signal phrases**, including:
   - "Disable logging"
   - "Choose the option that preserves correctness, clarity, and maintainability"
   - "Generic self-rating" stems
6. **Reference real engineering vocabulary** for the role. Backend:
   idempotency keys, EXPLAIN plans, SLOs. Frontend: hydration, layout
   thrashing, fetch waterfalls. Data science: bias-variance, leakage,
   stratified sampling. And so on.
7. **Match the role graph.** `competency` and `dimension_key` must
   exactly equal what `role_graph_data.ROLE_GRAPHS[<role>]` says for
   that subskill. The validator will reject a mismatch.

## Coverage floor (per role)

- Stage 1 `single_choice`: ≥ 2 per stage-1 allocation subskill (run
  `StageAllocator.allocate_stage_one(graph)` to see the set).
- Stage 2 `single_choice`: ≥ 2 per role subskill (all 16).
- Stage 2 `multi_select`: ≥ 1 per role subskill (all 16).
- Stage 2 `open_ended`: ≥ 1 per role subskill (all 16).

The `scenario_corpus_audit` command computes this matrix and exits
non-zero on any gap. CI gates on its exit code.

## Author loop

1. Open the role module under `scenario_corpus/<role>.py`.
2. Append a new dict literal. Set `review_status="draft"`.
3. Run `python manage.py scenario_corpus_audit`. Fix any validation
   errors it reports. Drafts are skipped by retrieval, so they do not
   block the audit's coverage check, but they DO get validated.
4. When the scenario reads cleanly and is reviewed, flip
   `review_status="approved"` and update `created_at`.
5. Re-run `python manage.py scenario_corpus_audit`. Coverage gaps will
   surface here.
6. Re-run `python manage.py rebuild_scenario_index` to ingest the
   approved scenarios into the local Chroma collection.
7. Run the corpus + retriever tests:
   `pytest apps/assessments/tests/test_scenario_corpus.py apps/assessments/tests/test_scenario_retriever.py -v`
8. If the content change is meaningful enough to affect prompts in
   production, bump `SCENARIO_CORPUS_VERSION` in `registry.py`. This
   invalidates stage-one cached questions automatically.

## Canonical scenario template

Copy this block, then fill in. Every field below is required (with the
exception of `helper`).

```python
{
    "doc_id": "<role>.<subskill>.s<stage>.<question_type>.<slug>",
    "role_key": "<role>",
    "subskill_key": "<subskill>",
    "competency": "<exact SubSkill.label from role_graph_data>",
    "dimension_key": "<exact SubSkill.dimension from role_graph_data>",
    "stage": 1,
    "question_type": "single_choice",
    "difficulty": 3,
    "estimated_seconds": 50,
    "learning_objective": "One sentence: what this question evaluates.",
    "scenario_context": "One or two sentences: name a real artifact and the situation.",
    "stem": "Which design / next step / tradeoff is strongest?",
    "options": [
        {"id": "a", "label": "Concrete option a (correct)."},
        {"id": "b", "label": "Concrete option b (plausible-but-wrong)."},
        {"id": "c", "label": "Concrete option c (plausible-but-wrong)."},
        {"id": "d", "label": "Concrete option d (plausible-but-wrong)."},
    ],
    "answer_key": {"correct_option_ids": ["a"], "scoring": "single_best"},
    "explanation": "Short prose explanation of the intended reasoning.",
    "correct_answer_rationale": "One sentence on why option a is best.",
    "option_rationales": [
        {"option_id": "a", "is_correct": True,  "rationale": "Why a is best."},
        {"option_id": "b", "is_correct": False, "rationale": "Why b is wrong."},
        {"option_id": "c", "is_correct": False, "rationale": "Why c is wrong."},
        {"option_id": "d", "is_correct": False, "rationale": "Why d is wrong."},
    ],
    "helper": "Optional: a one-sentence nudge that does not give away the answer.",
    "author": "<your handle or source string>",
    "license": "internal",
    "review_status": "draft",
    "created_at": "YYYY-MM-DD",
    "corpus_version": SCENARIO_CORPUS_VERSION,
}
```

For `multi_select`: 5 options, end the stem with `Select all that apply.`,
mark 2 or 3 as `is_correct=True`, and set
`"scoring": "partial_credit"`.

For `open_ended`: `options=[]`, `option_rationales=[]`, and the
`answer_key` is:

```python
{
    "expected_concepts": ["concept 1", "concept 2", "concept 3"],
    "required_concept_count": 2,
    "forbidden_concepts": ["one phrase that contradicts a strong answer"],
    "scoring": "concept_coverage",
}
```

## When in doubt

Read the existing seeded scenarios in `backend.py`. They are the
reference quality bar. If you would not be comfortable defending a new
scenario as as strong as one of those, do not promote it from `draft` to
`approved`.
