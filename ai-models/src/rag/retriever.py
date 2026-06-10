"""
RAG Retriever for Career Advisory

Retrieves relevant context from knowledge base for LLM generation.
"""

import logging
from typing import List, Dict, Any, Optional

from . import vector_store
from . import reranker
from .hybrid_search import HybridIndex, rrf_fuse

logger = logging.getLogger(__name__)

# Candidate pool fetched from each ranker before fusion
CANDIDATE_POOL = 20

_hybrid_index: Optional[HybridIndex] = None
_hybrid_index_failed = False


def _get_hybrid_index() -> Optional[HybridIndex]:
    """Lazily build the BM25 index over the collection; None on any failure.

    One-time per-process cost (tokenizing the collection). Failure or a
    missing rank_bm25 dependency degrades retrieval to dense-only — same
    fault-tolerance contract the advisory module already relies on.
    """
    global _hybrid_index, _hybrid_index_failed
    if _hybrid_index is not None or _hybrid_index_failed:
        return _hybrid_index
    try:
        index = HybridIndex(list(vector_store.iter_all_documents()))
        _hybrid_index = index if index.available else None
        if _hybrid_index is None:
            _hybrid_index_failed = True
    except Exception as error:
        logger.warning("Hybrid index build failed; dense-only retrieval: %s", error)
        _hybrid_index_failed = True
    return _hybrid_index


# Source quality_tier (set at build time, see DATASET_REGISTRY.md) -> base
# confidence. A weak joint-relevance signal (negative cross-encoder logit)
# downgrades one level.
_TIER_BY_QUALITY = {
    "official": "HIGH",
    "curated": "HIGH",
    "established": "MEDIUM",
    "dev_fallback": "LOW",
}
_DOWNGRADE = {"HIGH": "MEDIUM", "MEDIUM": "LOW", "LOW": "LOW"}


def _confidence_tier(doc: Dict[str, Any]) -> str:
    metadata = doc.get("metadata") or {}
    tier = _TIER_BY_QUALITY.get(metadata.get("quality_tier"), "LOW")
    rerank_score = doc.get("rerank_score")
    if rerank_score is not None and rerank_score < 0:
        tier = _DOWNGRADE[tier]
    return tier


def _build_where(category: Optional[str], filters: Optional[Dict[str, Any]]):
    """Combine filters into a Chroma where clause ($and for multiple keys)."""
    combined: Dict[str, Any] = dict(filters or {})
    if category:
        combined["category"] = category
    if not combined:
        return None
    if len(combined) == 1:
        return combined
    return {"$and": [{key: value} for key, value in combined.items()]}


def retrieve_context(
    query: str,
    top_k: int = 5,
    min_score: float = 0.3,
    category: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context for a query.

    Hybrid path (default): dense + BM25 candidates fused with reciprocal
    rank fusion; ranking is relative, so no absolute score threshold is
    applied (the old min_score cutoff against cosine scores silently
    starved the advisor of context — see eval_results/retrieval/).

    Dense-only fallback (BM25 index unavailable, or category filter in
    use — the BM25 index is collection-wide): legacy behavior, including
    the min_score threshold.

    Args:
        query: User's question
        top_k: Maximum number of documents to retrieve
        min_score: Similarity threshold (dense-only fallback path)
        category: Optional category filter (career_path, interview_prep, ...)
        filters: Optional metadata equality filters, e.g. {"source": "roadmap.sh"}

    Returns:
        List of relevant documents with content, metadata, and a
        confidence_tier (HIGH/MEDIUM/LOW) derived from source quality
        and re-ranking strength.
    """
    filter_metadata = _build_where(category, filters)

    hybrid = None if filter_metadata else _get_hybrid_index()
    if hybrid is None:
        results = vector_store.search(query, top_k=top_k, filter_metadata=filter_metadata)
        results = [r for r in results if r['score'] >= min_score]
        for doc in results:
            doc["confidence_tier"] = _confidence_tier(doc)
        return results

    dense = vector_store.search(query, top_k=CANDIDATE_POOL)
    bm25 = hybrid.search(query, top_k=CANDIDATE_POOL)

    fused = rrf_fuse([
        [doc["id"] for doc in dense],
        [doc_id for doc_id, _ in bm25],
    ])
    # keep the full fused pool as rerank candidates; the cross-encoder
    # picks the final top_k (passthrough truncation when disabled)
    candidate_ids = [doc_id for doc_id, _ in fused]
    fused_scores = dict(fused)

    dense_by_id = {doc["id"]: doc for doc in dense}
    missing = [doc_id for doc_id in candidate_ids if doc_id not in dense_by_id]
    fetched_by_id = {doc["id"]: doc for doc in vector_store.get_by_ids(missing)}

    candidates = []
    for doc_id in candidate_ids:
        doc = dense_by_id.get(doc_id) or fetched_by_id.get(doc_id)
        if doc is None:
            continue
        doc = dict(doc)
        doc["score"] = fused_scores[doc_id]
        doc["retrieval"] = "hybrid_rrf"
        candidates.append(doc)

    results = reranker.rerank(query, candidates, top_k=top_k)
    for doc in results:
        doc["confidence_tier"] = _confidence_tier(doc)
    return results


def format_context_for_llm(documents: List[Dict[str, Any]]) -> str:
    """
    Format retrieved documents into context string for LLM prompt.
    
    Args:
        documents: List of retrieved documents
        
    Returns:
        Formatted context string
    """
    if not documents:
        return "No specific context available."
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        category = doc.get('metadata', {}).get('category', 'general')
        topic = doc.get('metadata', {}).get('topic', '')
        
        source_info = f"[{category}"
        if topic:
            source_info += f": {topic}"
        source_info += "]"
        
        context_parts.append(f"{i}. {source_info}\n{doc['content']}")
    
    return "\n\n".join(context_parts)


def get_relevant_context(query: str, max_tokens: int = 1500) -> str:
    """
    Get formatted context for a query, respecting token limits.
    
    Args:
        query: User's question
        max_tokens: Approximate maximum tokens for context
        
    Returns:
        Formatted context string
    """
    # Retrieve more documents than needed, then truncate
    documents = retrieve_context(query, top_k=8)
    
    # Format and truncate to approximate token limit (rough estimate: 4 chars per token)
    context = format_context_for_llm(documents)
    
    max_chars = max_tokens * 4
    if len(context) > max_chars:
        context = context[:max_chars] + "..."
    
    return context


# Simple test
if __name__ == "__main__":
    # This test requires documents to be seeded first
    print("Testing retriever...")
    
    query = "How do I transition to a tech career?"
    context = get_relevant_context(query)
    
    print(f"Query: {query}")
    print(f"\nRetrieved context:\n{context}")
