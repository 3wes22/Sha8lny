"""Rebuild the assessment_scenarios Chroma index from the version-controlled
``scenario_corpus`` package.

Idempotent. The vector store is treated as a derived index; the authored
scenarios in version control are the source of truth (see
``specs/005-scenario-rag-corpus/data-model.md`` Entity 3).

Usage:
    python manage.py rebuild_scenario_index
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.assessments.scenario_corpus.registry import (
    SCENARIO_CORPUS_VERSION,
    assert_corpus_integrity,
    iter_approved_scenarios,
)
from apps.assessments.scenario_retriever import (
    ScenarioRetriever,
    _COLLECTION_NAME,
)
from apps.core.ai_settings import (
    EMBEDDING_MODEL,
    SCENARIO_VECTOR_DB_PATH,
)


class Command(BaseCommand):
    help = (
        "Rebuild the assessment_scenarios Chroma collection from the version-"
        "controlled scenario corpus. Idempotent and safe to re-run."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write(
            f"Validating corpus integrity (version={SCENARIO_CORPUS_VERSION})..."
        )
        try:
            assert_corpus_integrity()
        except Exception as error:
            raise CommandError(f"Corpus integrity check failed:\n{error}") from error

        approved = list(iter_approved_scenarios())
        self.stdout.write(
            f"Found {len(approved)} approved scenario(s) across all per-role modules."
        )
        if not approved:
            self.stdout.write(self.style.WARNING(
                "Corpus is empty. The collection will be (re)created and left empty."
            ))

        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError as error:
            raise CommandError(
                "chromadb is not installed. Run `pip install -r requirements.txt`."
            ) from error

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise CommandError(
                "sentence-transformers is not installed. Run "
                "`pip install -r requirements.txt`."
            ) from error

        persist_dir = Path(SCENARIO_VECTOR_DB_PATH)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.stdout.write(f"Using vector store path: {persist_dir}")

        client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

        # Chroma >=0.6 returns collection names (strings) from list_collections();
        # older versions returned objects with a .name attribute. Support both.
        existing_collections = {
            c if isinstance(c, str) else c.name
            for c in client.list_collections()
        }
        if _COLLECTION_NAME in existing_collections:
            self.stdout.write(
                f"Wiping existing '{_COLLECTION_NAME}' collection..."
            )
            client.delete_collection(_COLLECTION_NAME)
        collection = client.create_collection(_COLLECTION_NAME)

        if not approved:
            ScenarioRetriever.reset()
            self.stdout.write(self.style.SUCCESS(
                "Created empty 'assessment_scenarios' collection. Nothing ingested."
            ))
            return

        self.stdout.write(
            f"Embedding {len(approved)} scenario(s) with {EMBEDDING_MODEL}..."
        )
        embedder = SentenceTransformer(EMBEDDING_MODEL)

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for scenario in approved:
            doc_id = str(scenario.get("doc_id") or "")
            embedding_text = ScenarioRetriever.build_embedding_text(
                competency=str(scenario.get("competency") or ""),
                question_type=str(scenario.get("question_type") or ""),
                stage=int(scenario.get("stage") or 0),
                scenario_context=str(scenario.get("scenario_context") or ""),
                stem=str(scenario.get("stem") or ""),
            )
            ids.append(doc_id)
            documents.append(embedding_text)
            metadatas.append(
                {
                    "role_key": str(scenario.get("role_key") or ""),
                    "subskill_key": str(scenario.get("subskill_key") or ""),
                    "dimension_key": str(scenario.get("dimension_key") or ""),
                    "question_type": str(scenario.get("question_type") or ""),
                    "stage": int(scenario.get("stage") or 0),
                    "difficulty": int(scenario.get("difficulty") or 0),
                    "corpus_version": str(
                        scenario.get("corpus_version") or SCENARIO_CORPUS_VERSION
                    ),
                    "payload": json.dumps(scenario, ensure_ascii=True),
                }
            )

        embeddings = embedder.encode(documents, normalize_embeddings=True)
        embeddings_list = (
            embeddings.tolist()
            if hasattr(embeddings, "tolist")
            else [list(vec) for vec in embeddings]
        )

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings_list,
            metadatas=metadatas,
        )

        ScenarioRetriever.reset()

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {len(approved)} scenario(s) into {persist_dir} "
                f"(collection '{_COLLECTION_NAME}')."
            )
        )
