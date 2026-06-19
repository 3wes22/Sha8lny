"""Chroma-backed course embedding index for roadmap course matching."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from apps.core.ai_settings import COURSE_VECTOR_DB_PATH, EMBEDDING_MODEL


logger = logging.getLogger(__name__)

_COLLECTION_NAME = "courses"


def build_course_embedding_text(course) -> str:
    """Build searchable text for a Course instance."""
    from apps.courses.models import CourseSkill

    skill_names = list(
        CourseSkill.objects.filter(course=course, is_deleted=False)
        .select_related("skill")
        .values_list("skill__name", flat=True)
    )
    parts = [
        str(course.title or "").strip(),
        str(course.description or "").strip(),
        f"level: {course.level or ''}".strip(),
        f"skills: {', '.join(skill_names)}".strip(": "),
    ]
    return "\n".join(part for part in parts if part)


class CourseIndex:
    """Read/write helper for the local courses Chroma collection."""

    _embedder: Any = None
    _client: Any = None
    _collection: Any = None

    @classmethod
    def reset(cls) -> None:
        cls._embedder = None
        cls._client = None
        cls._collection = None

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

        persist_dir = Path(COURSE_VECTOR_DB_PATH)
        persist_dir.mkdir(parents=True, exist_ok=True)
        cls._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        cls._collection = cls._client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return cls._collection

    @classmethod
    def document_count(cls) -> int:
        try:
            return cls._get_collection().count()
        except Exception:
            return 0

    @classmethod
    def rebuild(cls) -> int:
        """Re-index all active courses. Returns indexed count."""
        from apps.courses.models import Course

        collection = cls._get_collection()
        try:
            existing = collection.get()
            if existing and existing.get("ids"):
                collection.delete(ids=existing["ids"])
        except Exception as error:
            logger.warning("Course index clear failed: %s", error)

        courses = Course.objects.filter(is_deleted=False, is_published=True).prefetch_related(
            "course_skills__skill"
        )
        documents: list[str] = []
        metadatas: list[dict[str, str]] = []
        ids: list[str] = []

        for course in courses:
            text = build_course_embedding_text(course)
            if not text.strip():
                continue
            documents.append(text)
            metadatas.append(
                {
                    "course_id": str(course.id),
                    "title": str(course.title or "")[:120],
                    "level": str(course.level or ""),
                }
            )
            ids.append(str(course.id))

        if not documents:
            return 0

        embedder = cls._get_embedder()
        embeddings = embedder.encode(documents, show_progress_bar=False).tolist()
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(ids)

    @classmethod
    def search(cls, query: str, *, top_k: int = 2) -> list[dict[str, Any]]:
        """Return ranked course matches: course_id, score (0-1), title."""
        query = str(query or "").strip()
        if not query:
            return []

        try:
            if cls.document_count() == 0:
                return []
            embedder = cls._get_embedder()
            embedding = embedder.encode([query], show_progress_bar=False).tolist()
            results = cls._get_collection().query(
                query_embeddings=embedding,
                n_results=top_k,
                include=["metadatas", "distances"],
            )
        except Exception as error:
            logger.warning("Course index search failed: %s", error)
            return []

        matches: list[dict[str, Any]] = []
        metadatas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        for metadata, distance in zip(metadatas, distances):
            if not isinstance(metadata, dict):
                continue
            score = max(0.0, min(1.0, 1.0 - float(distance)))
            matches.append(
                {
                    "course_id": metadata.get("course_id"),
                    "title": metadata.get("title", ""),
                    "score": score,
                }
            )
        return matches
