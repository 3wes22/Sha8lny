# Phase 1 Data Model: Scenario RAG Corpus

This feature introduces **no new Django models** and **no database migrations**. All data lives in (a) version-controlled Python modules and (b) a derived local Chroma vector store. The "data model" below describes the in-process and on-disk shapes that callers must respect.

## Entity 1: `ScenarioDocument`

The version-controlled source of truth. Defined as a `TypedDict` in `Backend/apps/assessments/scenario_corpus/schema.py`. Authored as plain Python dict literals in per-role modules under `scenario_corpus/`.

### Fields

| Field | Type | Required | Validation | Notes |
|---|---|---|---|---|
| `doc_id` | `str` | yes | unique across corpus; must match `^[a-z0-9_]+\.[a-z0-9_]+\.s[12]\.(single_choice\|multi_select\|open_ended)\.[a-z0-9_-]+$` | Stable identifier. Example: `backend.http_api_design.s1.single_choice.fallback-seed`. |
| `role_key` | `str` | yes | must exist as a key in `apps.assessments.role_graph_data.ROLE_GRAPHS` | Approved 8-role set only. |
| `subskill_key` | `str` | yes | must exist within the `role_key`'s curated `RoleGraph` | Cross-checked against `_subskill_lookup(role_graph)` from `engine.py`. |
| `competency` | `str` | yes | non-empty; equals the `SubSkill.label` for that subskill | Used both in retrieval text and as the few-shot `competency` field. |
| `dimension_key` | `str` | yes | must equal the `dimension` of the matching `SubSkill` in the role graph | Catches authoring drift between role graph and corpus. |
| `stage` | `int` literal `1` or `2` | yes | exactly `1` or `2` | Matches `_stage_question_type_sequence()` semantics. |
| `question_type` | `Literal["single_choice", "multi_select", "open_ended"]` | yes | one of the three values | Matches `_build_stage_question_response_json_schema()` allowed enum. |
| `difficulty` | `int` | yes | `1 <= difficulty <= 5` | Same range as the LLM schema. |
| `estimated_seconds` | `int` | yes | `30 <= estimated_seconds <= 120` | Same range as the LLM schema. |
| `learning_objective` | `str` | yes | non-empty | One-sentence objective. |
| `scenario_context` | `str` | yes | non-empty; 1–2 sentences in production | Must describe a concrete engineering scenario. |
| `stem` | `str` | yes | non-empty; for `multi_select` must end with `"Select all that apply."` | Decision prompt. |
| `options` | `list[ScenarioOption]` | yes | `single_choice`: exactly 4; `multi_select`: exactly 5; `open_ended`: exactly `[]` | Per question-type rules. |
| `answer_key` | `dict` | yes | shape depends on `question_type` (see below) | Same shape as the live LLM schema. |
| `explanation` | `str` | yes | non-empty | Short explanation of the intended answer. |
| `correct_answer_rationale` | `str` | yes | non-empty | Why the correct answer is best. |
| `option_rationales` | `list[ScenarioOptionRationale]` | yes | `len == len(options)` for closed types; `[]` for `open_ended`; exactly one `is_correct=True` for `single_choice`; 2 or 3 `is_correct=True` for `multi_select` | One entry per option. |
| `helper` | `str` | no | non-empty when present | Optional hint, surfaced in UI today. |
| `author` | `str` | yes | non-empty | Author identifier or source string. |
| `license` | `str` | yes | non-empty; `"internal"` for authored content | Track provenance. |
| `review_status` | `Literal["draft", "approved"]` | yes | only `"approved"` documents are ingested by `rebuild_scenario_index` | Drafts stay in version control but never reach retrieval. |
| `created_at` | `str` (`YYYY-MM-DD`) | yes | ISO date string | Used in audit reports. |
| `corpus_version` | `str` | yes | must equal `SCENARIO_CORPUS_VERSION` at validation time | Catches stale documents that predate a version bump. |

### Nested types

```python
class ScenarioOption(TypedDict):
    id: str        # 'a' | 'b' | 'c' | 'd' | 'e'
    label: str     # user-facing option text

class ScenarioOptionRationale(TypedDict):
    option_id: str
    is_correct: bool
    rationale: str
```

### `answer_key` shape per question type

| `question_type` | Required `answer_key` keys | Notes |
|---|---|---|
| `single_choice` | `correct_option_ids: list[str]` (length 1), `scoring: "single_best"` | Same as the LLM schema. |
| `multi_select` | `correct_option_ids: list[str]` (length 2 or 3), `scoring: "partial_credit"` | Same as the LLM schema. |
| `open_ended` | `expected_concepts: list[str]` (length 3), `required_concept_count: int` (in `[1, 5]`), `forbidden_concepts: list[str]` (length 1), `scoring: "concept_coverage"` | Same as the LLM schema. |

### Lifecycle

```
draft  ──(human review + author edits)──▶  approved  ──(rebuild_scenario_index)──▶  indexed
                                                ▲
                                                │  (audit + tests in CI)
                                                ▼
                                            removed from corpus.py file (hard delete in VCS)
```

- `draft` documents are never ingested. They live in author working files for review.
- `approved` documents are the only ones returned by `iter_all_scenarios()` and the only ones the management command ingests.
- Deletion is a plain code change to the per-role module; the next `rebuild_scenario_index` run wipes and re-builds the collection so deleted documents disappear from retrieval.

### Validation rules (implemented by `validate_scenario(doc) -> list[str]`)

The function returns a list of error messages. Empty list means valid. The full rule set:

1. All required fields present and non-empty (per "Required" column above).
2. `role_key` exists in `ROLE_GRAPHS`.
3. `subskill_key` exists within that role's `RoleGraph`.
4. `dimension_key` equals the matching `SubSkill.dimension`.
5. `competency` equals the matching `SubSkill.label` exactly.
6. `corpus_version == SCENARIO_CORPUS_VERSION`.
7. `question_type` rules:
   - `single_choice`: `len(options) == 4`, exactly one `option_rationales[*].is_correct == True`, `answer_key.correct_option_ids` has length 1 and that ID exists in `options`, `answer_key.scoring == "single_best"`.
   - `multi_select`: `len(options) == 5`, `stem` ends with `"Select all that apply."`, 2 or 3 entries in `option_rationales` are `is_correct=True`, `answer_key.correct_option_ids` has length 2 or 3, all listed IDs exist in `options`, `answer_key.scoring == "partial_credit"`.
   - `open_ended`: `options == []`, `option_rationales == []`, `answer_key.expected_concepts` has length 3, `answer_key.required_concept_count` in `[1, 5]`, `answer_key.forbidden_concepts` has length 1, `answer_key.scoring == "concept_coverage"`.
8. The document, when reshaped to look like the live question payload, passes `apps.core.ai_validation.build_stage_validation_flags(question)` with zero flags.
9. `difficulty` in `[1, 5]` and `estimated_seconds` in `[30, 120]`.
10. `doc_id` matches the regex above and is unique within `iter_all_scenarios()`.

## Entity 2: `SCENARIO_CORPUS_VERSION`

A single module-level string constant in `Backend/apps/assessments/scenario_corpus/registry.py`.

- Initial value: `"scenario-v1"`.
- Bumped by hand any time the approved corpus content changes meaningfully (added scenarios, edited scenario text, removed scenarios).
- Read by:
  - `validate_scenario()` (rule 6 above) — every document must declare it.
  - `AssessmentAIService._stage_one_cache_key()` — appended to the cache key suffix so stage-one cached questions invalidate on bump.
  - `rebuild_scenario_index` — wipes the collection and re-ingests when invoked.
  - `scenario_corpus_audit` — printed at the top of the coverage report.

## Entity 3: `assessment_scenarios` Chroma collection

A derived, rebuildable index living in `SCENARIO_VECTOR_DB_PATH`. Carries no source of truth; can be deleted and rebuilt from `iter_all_scenarios()` at any time.

### Per-document Chroma record

| Chroma field | Source | Notes |
|---|---|---|
| `id` | `ScenarioDocument.doc_id` | Stable across rebuilds. |
| `document` | `f"{competency} \| {question_type} \| stage {stage}\n{scenario_context}\n{stem}"` | Embedding text. |
| `embedding` | `all-MiniLM-L6-v2` normalized vector (384 dim) | Computed at index time. |
| `metadata.role_key` | `ScenarioDocument.role_key` | Used in `where` filter. |
| `metadata.subskill_key` | `ScenarioDocument.subskill_key` | Available to consumers. |
| `metadata.dimension_key` | `ScenarioDocument.dimension_key` | Available to consumers. |
| `metadata.question_type` | `ScenarioDocument.question_type` | Used in `where` filter. |
| `metadata.stage` | `ScenarioDocument.stage` | Used in `where` filter. |
| `metadata.difficulty` | `ScenarioDocument.difficulty` | Available to consumers. |
| `metadata.corpus_version` | `ScenarioDocument.corpus_version` | Used to detect stale ingest. |
| `metadata.payload` | `json.dumps(ScenarioDocument)` | Full document; retrieval returns this and parses it. |

### Lifecycle

- Created on first call to `ScenarioRetriever._get_collection()` (`get_or_create_collection("assessment_scenarios")`).
- Rebuilt by `python manage.py rebuild_scenario_index`: wipes all docs in the collection, then re-adds every `approved` scenario from `iter_all_scenarios()`. Idempotent.
- Wiped manually by deleting `SCENARIO_VECTOR_DB_PATH` if needed; next ingest recreates it.
- Never written to at request time. Retrieval is read-only.

## Cross-entity invariants

- For every `ScenarioDocument` in `iter_all_scenarios()` with `review_status == "approved"`, the live `build_stage_validation_flags()` returns `[]` when called on the equivalent question payload. Enforced by `validate_scenario` rule 8 and by `tests/test_scenario_corpus.py::test_every_scenario_validates`.
- For every approved scenario, after `rebuild_scenario_index` runs, querying the collection with `where={"$and": [{"role_key": doc.role_key}, {"question_type": doc.question_type}, {"stage": doc.stage}]}` returns at least one document whose `metadata.payload` (parsed) has the same `doc_id`. Enforced by the smoke retrieval test.
- For every blueprint produced by `_build_stage_blueprints()` across all 8 role graphs in stage 1 and stage 2, the filter `(role_key, question_type, stage)` resolves to at least one document once that role's coverage cells reach the documented floor. Enforced by `tests/test_scenario_corpus.py::test_coverage_floor_per_role_stage_question_type` and by the audit CI gate.
