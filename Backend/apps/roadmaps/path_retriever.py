"""
Retrieve roadmap.sh learning-path chunks from the career_knowledge Chroma collection.

Queries run at roadmap generation time against the same index used by advisory RAG.
Metadata key verified in ``ai-models/src/rag/build_vector_db.py``: ``source=roadmap.sh``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from apps.assessments.role_graph import resolve_role_key
from apps.core.ai_settings import CHROMA_PERSIST_DIR, EMBEDDING_MODEL


logger = logging.getLogger(__name__)

_COLLECTION_NAME = "career_knowledge"
_SOURCE_FILTER = {"source": "roadmap.sh"}

ROLE_TO_ROADMAP_CATEGORY: dict[str, str] = {
    "backend": "backend",
    "frontend": "frontend",
    "data_science": "ai-data-scientist",
    "fullstack": "full-stack",
    "devops": "devops",
    "android": "android",
    "machine_learning_engineer": "ai-engineer",
    "ui_ux_designer": "design-system",
}


def roadmap_sh_url(category: str) -> str:
    """Public roadmap.sh URL for a category slug."""
    slug = (category or "backend").strip().strip("/")
    return f"https://roadmap.sh/{slug}"


class RoadmapPathRetriever:
    """Query Chroma ``career_knowledge`` for roadmap.sh path content."""

    _embedder: Any = None
    _client: Any = None
    _collection: Any = None

    @classmethod
    def reset(cls) -> None:
        """Drop cached singletons (tests only)."""
        cls._embedder = None
        cls._client = None
        cls._collection = None

    @classmethod
    def _get_embedder(cls):
        if cls._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer

                cls._embedder = SentenceTransformer(EMBEDDING_MODEL)
            except Exception as error:
                logger.warning("Unable to load embedding model: %s", error)
                return None
        return cls._embedder

    @classmethod
    def _persist_dir(cls) -> Path:
        if CHROMA_PERSIST_DIR:
            return Path(CHROMA_PERSIST_DIR)
        repo_root = Path(__file__).resolve().parents[3]
        return repo_root / "ai-models" / "data" / "vector_db"

    @classmethod
    def _get_collection(cls):
        if cls._collection is not None:
            return cls._collection

        try:
            import chromadb
            from chromadb.config import Settings
        except Exception as error:
            logger.warning("ChromaDB unavailable for roadmap retrieval: %s", error)
            return None

        persist_dir = cls._persist_dir()
        if not persist_dir.exists():
            logger.warning("Chroma persist dir missing: %s", persist_dir)
            return None

        try:
            cls._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=Settings(anonymized_telemetry=False),
            )
            cls._collection = cls._client.get_collection(_COLLECTION_NAME)
        except Exception as error:
            logger.warning("Unable to open Chroma collection %s: %s", _COLLECTION_NAME, error)
            cls._collection = None
        return cls._collection

    @classmethod
    def _build_query(cls, role_key: str, target_career: str) -> str:
        category = ROLE_TO_ROADMAP_CATEGORY.get(role_key, role_key.replace("_", "-"))
        return (
            f"{target_career} {category} learning path roadmap skills beginner to advanced"
        ).strip()

    @classmethod
    def retrieve_path_chunks(
        cls,
        role_key: str,
        target_career: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Query Chroma career_knowledge filtered by source=roadmap.sh.

        Returns list of {content, source_url, doc_id, metadata}.
        Falls back to [] if collection unreachable — never raises.
        """
        collection = cls._get_collection()
        if collection is None:
            return []

        try:
            if collection.count() == 0:
                logger.warning("Chroma collection %s is empty", _COLLECTION_NAME)
                return []
        except Exception as error:
            logger.warning("Chroma count failed: %s", error)
            return []

        resolved_role = resolve_role_key(target_career) if not role_key else role_key
        query_text = cls._build_query(resolved_role, target_career)

        embedder = cls._get_embedder()
        if embedder is None:
            return []

        try:
            embedding = embedder.encode([query_text]).tolist()
            results = collection.query(
                query_embeddings=embedding,
                n_results=top_k,
                where=_SOURCE_FILTER,
            )
        except Exception as error:
            logger.warning("Roadmap path retrieval failed: %s", error)
            return []

        documents = results.get("documents") or [[]]
        metadatas = results.get("metadatas") or [[]]
        ids = results.get("ids") or [[]]

        chunks: list[dict[str, Any]] = []
        for doc_id, content, metadata in zip(ids[0], documents[0], metadatas[0]):
            if not content or not str(content).strip():
                continue
            meta = metadata if isinstance(metadata, dict) else {}
            category = str(meta.get("category") or ROLE_TO_ROADMAP_CATEGORY.get(resolved_role, "backend"))
            chunks.append(
                {
                    "content": str(content).strip(),
                    "source_url": roadmap_sh_url(category),
                    "doc_id": str(doc_id),
                    "metadata": meta,
                }
            )
        return chunks
