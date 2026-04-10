"""
RAG Retriever for Career Advisory

Retrieves relevant context from knowledge base for LLM generation.
"""

from typing import List, Dict, Any, Optional
from . import vector_store


def retrieve_context(
    query: str,
    top_k: int = 5,
    min_score: float = 0.3,
    category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context for a query.
    
    Args:
        query: User's question
        top_k: Maximum number of documents to retrieve
        min_score: Minimum similarity score threshold
        category: Optional category filter (career_path, interview_prep, learning, etc.)
        
    Returns:
        List of relevant documents with content and metadata
    """
    # Build metadata filter if category specified
    filter_metadata = None
    if category:
        filter_metadata = {"category": category}
    
    # Search vector store
    results = vector_store.search(query, top_k=top_k, filter_metadata=filter_metadata)
    
    # Filter by minimum score
    relevant = [r for r in results if r['score'] >= min_score]
    
    return relevant


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
