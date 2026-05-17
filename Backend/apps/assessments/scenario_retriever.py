"""Runtime retriever for the assessment scenario corpus.

Read-only, single-process retrieval against the local Chroma collection
``assessment_scenarios`` at ``apps.core.ai_settings.SCENARIO_VECTOR_DB_PATH``.
Class-level lazy singletons for both the embedder and the collection keep
worker boot fast; the first retrieval call pays the model load cost.

Contract: ``specs/005-scenario-rag-corpus/contracts/retriever_interface.md``.

Every failure path returns ``[]`` and emits one structured ``WARNING`` log.
Retrieval MUST NEVER raise into ``ai_pipeline._build_stage_prompt`` so the
deterministic fallback path remains the single source of generation safety.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from apps.assessments.scenario_corpus.registry import SCENARIO_CORPUS_VERSION
from apps.assessments.scenario_corpus.schema import (
    ScenarioDocument,
    validate_scenario,
)
from apps.core.ai_settings import (
    ASSESSMENT_SCENARIO_RAG_ENABLED,
    EMBEDDING_MODEL,
    SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT,
    SCENARIO_RAG_TOP_K,
    SCENARIO_VECTOR_DB_PATH,
)


logger = logging.getLogger(__name__)


_COLLECTION_NAME = "assessment_scenarios"


class ScenarioRetriever:
    """Read-only Chroma + sentence-transformers retriever.

    Public API:
        - ``retrieve_for_blueprint(*, role_key, blueprint, stage, top_k=1)``
        - ``build_embedding_text(*, competency, question_type, stage, scenario_context, stem)``
        - ``reset()`` (test-only helper to drop cached singletons between tests)
    """

    _embedder: Any = None
    _client: Any = None
    _collection: Any = None
    _failure_logged_for_call: bool = False

    # -- Lazy singletons -----------------------------------------------------

    @classmethod
    def _get_embedder(cls):
        if cls._embedder is None:
            from sentence_transformers import SentenceTransformer

            cls._embedder = SentenceTransformer(EMBEDDING_MODEL)
        return cls._embedder

    @classmethod
    def _get_collection(cls):
        if cls._collection is not None:
            return cls._collection

        import chromadb
        from chromadb.config import Settings

        persist_dir = Path(SCENARIO_VECTOR_DB_PATH)
        persist_dir.mkdir(parents=True, exist_ok=True)
        cls._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        cls._collection = cls._client.get_or_create_collection(_COLLECTION_NAME)
        return cls._collection

    @classmethod
    def reset(cls) -> None:
        """Drop cached singletons. Intended for test setups that point
        ``SCENARIO_VECTOR_DB_PATH`` at a temp directory."""
        cls._embedder = None
        cls._client = None
        cls._collection = None

    # -- Embedding text contract --------------------------------------------

    @staticmethod
    def build_embedding_text(
        *,
        competency: str,
        question_type: str,
        stage: int,
        scenario_context: str,
        stem: str,
    ) -> str:
        """Build the canonical retrieval text used both at ingest and at query time.

        Matches Decision 5 in ``research.md``:
            "{competency} | {question_type} | stage {stage}\n{scenario_context}\n{stem}"
        """
        return (
            f"{competency} | {question_type} | stage {stage}\n"
            f"{scenario_context}\n"
            f"{stem}"
        )

    # -- Retrieval -----------------------------------------------------------

    @classmethod
    def retrieve_for_blueprint(
        cls,
        *,
        role_key: str,
        blueprint: dict[str, Any],
        stage: int,
        top_k: int = SCENARIO_RAG_TOP_K,
    ) -> list[ScenarioDocument]:
        """Return up to ``top_k`` scenarios matching (role, question_type, stage).

        See ``contracts/retriever_interface.md``. Returns ``[]`` on any failure.
        Never raises.
        """
        if not ASSESSMENT_SCENARIO_RAG_ENABLED:
            return []

        question_type = str(blueprint.get("question_type") or "").strip()
        subskill_key = str(blueprint.get("subskill_key") or "").strip()
        competency = str(blueprint.get("competency") or "").strip()

        if not question_type or stage not in (1, 2) or not role_key:
            return []

        capped_top_k = max(1, min(int(top_k), SCENARIO_RAG_MAX_EXAMPLES_PER_PROMPT))

        try:
            collection = cls._get_collection()
            embedder = cls._get_embedder()

            query_text = cls.build_embedding_text(
                competency=competency or subskill_key,
                question_type=question_type,
                stage=stage,
                scenario_context=str(blueprint.get("focus") or ""),
                stem=subskill_key,
            )
            query_embedding = embedder.encode(
                [query_text],
                normalize_embeddings=True,
            )
            # Chroma expects a list of lists for query_embeddings; encode returns
            # numpy arrays so coerce defensively.
            embedding_list = (
                query_embedding.tolist()
                if hasattr(query_embedding, "tolist")
                else list(query_embedding)
            )

            results = collection.query(
                query_embeddings=embedding_list,
                n_results=capped_top_k,
                where={
                    "$and": [
                        {"role_key": role_key},
                        {"question_type": question_type},
                        {"stage": stage},
                    ]
                },
            )
        except Exception as error:
            cls._emit_failure_log(role_key=role_key, stage=stage, error=error)
            return []

        documents: list[ScenarioDocument] = []
        top_doc_id: str | None = None
        top_score: float | None = None

        metadatas_batches = results.get("metadatas") or [[]]
        distances_batches = results.get("distances") or [[]]
        metadatas = metadatas_batches[0] if metadatas_batches else []
        distances = distances_batches[0] if distances_batches else []

        for index, metadata in enumerate(metadatas):
            if not isinstance(metadata, dict):
                continue
            payload_json = metadata.get("payload")
            if not isinstance(payload_json, str):
                continue
            try:
                payload = json.loads(payload_json)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            if validate_scenario(payload):  # validation errors → skip
                continue
            documents.append(payload)
            if index == 0:
                top_doc_id = str(payload.get("doc_id") or "") or None
                if index < len(distances) and distances[index] is not None:
                    try:
                        top_score = float(1.0 - float(distances[index]))
                    except (TypeError, ValueError):
                        top_score = None

        logger.info(
            "scenario_retrieval",
            extra={
                "event": "scenario_retrieval",
                "role_key": role_key,
                "subskill_key": subskill_key,
                "question_type": question_type,
                "stage": stage,
                "results_count": len(documents),
                "top_doc_id": top_doc_id,
                "top_score": top_score,
                "corpus_version": SCENARIO_CORPUS_VERSION,
            },
        )
        return documents

    # -- Internal helpers ----------------------------------------------------

    @classmethod
    def _emit_failure_log(cls, *, role_key: str, stage: int, error: Exception) -> None:
        logger.warning(
            "scenario_retrieval_failed",
            extra={
                "event": "scenario_retrieval_failed",
                "role_key": role_key,
                "stage": stage,
                "error_type": type(error).__name__,
                "corpus_version": SCENARIO_CORPUS_VERSION,
            },
        )
