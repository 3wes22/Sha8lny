# Internal Contract: `ScenarioRetriever`

This document defines the runtime interface that `Backend/apps/assessments/ai_pipeline.py` consumes for scenario retrieval. The class is an internal Backend dependency, not exposed over HTTP. Callers may depend only on the methods and behaviors listed here.

## Module location

`Backend/apps/assessments/scenario_retriever.py`

## Class: `ScenarioRetriever`

A class with class-level lazy singletons for the embedder and the Chroma collection. Not instantiated; callers use class methods only.

### Method: `retrieve_for_blueprint`

```python
@classmethod
def retrieve_for_blueprint(
    cls,
    *,
    role_key: str,
    blueprint: dict,
    stage: int,
    top_k: int = 1,
) -> list[dict]:
    ...
```

**Inputs**

| Argument | Type | Source / contract |
|---|---|---|
| `role_key` | `str` | The current `role_graph.role_key` (e.g. `"backend"`). Resolved upstream via `apps.assessments.role_graph.resolve_role_key`. |
| `blueprint` | `dict` | A single entry from `apps.assessments.ai_pipeline._build_stage_blueprints()`. Must contain at minimum `subskill_key`, `competency`, `question_type`, and `focus`. |
| `stage` | `int` literal `1` or `2` | The stage the assistant is generating questions for. |
| `top_k` | `int` | Maximum number of documents to return for this blueprint. Default `1`. Capped at `5` regardless of caller value. |

**Outputs**

`list[dict]` where each `dict` is a fully validated `ScenarioDocument` (as defined in `data-model.md`). The list may be empty.

**Behavior guarantees**

1. **Filtering**: results are restricted to `metadata.role_key == role_key`, `metadata.question_type == blueprint["question_type"]`, and `metadata.stage == stage`. No cross-role or cross-type contamination is possible.
2. **Ranking**: top-`k` cosine similarity within the filtered subset, computed by Chroma using `all-MiniLM-L6-v2` embeddings.
3. **Empty result on failure**: any of the following return `[]` and emit one structured warning log:
   - The feature flag `ASSESSMENT_SCENARIO_RAG_ENABLED` is `False`.
   - `SCENARIO_VECTOR_DB_PATH` does not exist or is unreadable.
   - The collection `assessment_scenarios` does not exist or is empty.
   - The embedder fails to load.
   - Chroma raises any exception during `query()`.
   - The JSON decoded from `metadata.payload` fails validation against `ScenarioDocument`.
4. **No mutation**: the method is read-only. It never writes to the collection, never modifies its inputs, never raises.
5. **No new outbound network calls** at request time.

**Logging contract**

On every call where `ASSESSMENT_SCENARIO_RAG_ENABLED` is `True`, exactly one log event is emitted at `INFO`:

```python
logger.info(
    "scenario_retrieval",
    extra={
        "event": "scenario_retrieval",
        "role_key": role_key,
        "subskill_key": blueprint["subskill_key"],
        "question_type": blueprint["question_type"],
        "stage": stage,
        "results_count": int,
        "top_doc_id": str | None,
        "top_score": float | None,
        "corpus_version": SCENARIO_CORPUS_VERSION,
    },
)
```

On the failure path, exactly one log event is emitted at `WARNING` per generation (not per blueprint, to avoid log spam during outages):

```python
logger.warning(
    "scenario_retrieval_failed",
    extra={
        "event": "scenario_retrieval_failed",
        "role_key": role_key,
        "stage": stage,
        "error_type": type(error).__name__,
    },
)
```

## Settings dependencies (read-only)

The retriever consumes the following settings from `apps.core.ai_settings`. None are modified at runtime.

| Setting | Default | Purpose |
|---|---|---|
| `ASSESSMENT_SCENARIO_RAG_ENABLED` | `False` | Global on/off switch. When `False`, `retrieve_for_blueprint` returns `[]` immediately without touching Chroma or the embedder. |
| `SCENARIO_VECTOR_DB_PATH` | `<BASE_DIR>/data/scenario_vector_db` | On-disk Chroma persistent directory. Isolated from existing `CHROMA_PERSIST_DIR`. |
| `EMBEDDING_MODEL` | `"all-MiniLM-L6-v2"` | Already exists in `ai_settings.py`. Reused. |
| `SCENARIO_RAG_TOP_K` | `1` | Default `top_k` used by `_build_retrieved_examples_block()` in `ai_pipeline.py`. |
| `SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT` | `5` | Global cap enforced when assembling the per-prompt examples block. |

## Splice point in `ai_pipeline._build_stage_prompt()`

The retriever is invoked from a new class method `AssessmentAIService._build_retrieved_examples_block()` and the result is spliced into the existing prompt construction as:

```python
return (
    f"...existing content up to STAGE_QUESTION_FEW_SHOT_EXAMPLES...\n"
    f"{STAGE_QUESTION_FEW_SHOT_EXAMPLES}\n"
    f"{cls._build_retrieved_examples_block(role_graph=role_graph, blueprints=blueprints, stage=stage)}"
    f"Blueprints:\n{json.dumps(blueprints, ensure_ascii=True)}"
)
```

When `_build_retrieved_examples_block()` returns the empty string (flag off, or no results, or any failure), the resulting prompt is **byte-identical** to the pre-feature prompt. This identity property is verified by a regression test in `Backend/apps/assessments/tests/test_staged_flow.py`.

## Stability guarantees

- This contract is internal to `apps.assessments`. Breaking changes are allowed within the app boundary, but `_build_stage_prompt()` and `_stage_one_cache_key()` are the only callers expected.
- The `metadata.payload` JSON shape is governed by the `ScenarioDocument` JSON schema in `contracts/scenario_document.schema.json`. Any new field added to `ScenarioDocument` must be backward-compatible with already-ingested rows or accompanied by a `SCENARIO_CORPUS_VERSION` bump and a full index rebuild.
