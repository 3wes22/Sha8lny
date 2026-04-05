"""
ChromaDB Vector Store for RAG System

Persistent vector database for career knowledge retrieval.
Stores embeddings and metadata for semantic search.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path
import uuid

# Lazy loading
_client = None
_collection = None

# Default paths
DEFAULT_PERSIST_DIR = Path(__file__).parent.parent.parent / "data" / "vector_db"
COLLECTION_NAME = "career_knowledge"


def get_client(persist_directory: Optional[Path] = None):
    """Get or create ChromaDB client with persistence."""
    global _client
    
    if _client is None:
        try:
            import chromadb
            from chromadb.config import Settings
        except ImportError:
            raise ImportError(
                "chromadb not installed. "
                "Run: pip install chromadb"
            )
        
        persist_dir = persist_directory or DEFAULT_PERSIST_DIR
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        _client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
    
    return _client


def get_collection(name: str = COLLECTION_NAME):
    """Get or create the career knowledge collection."""
    global _collection
    
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=name,
            metadata={"description": "Career guidance knowledge base for Sha8alny advisory"}
        )
    
    return _collection


def add_documents(
    documents: List[str],
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None
) -> List[str]:
    """
    Add documents to the vector store.
    
    Args:
        documents: List of text content to add
        metadatas: Optional metadata for each document
        ids: Optional IDs (auto-generated if not provided)
        
    Returns:
        List of document IDs
    """
    from .embeddings import embed_text
    
    collection = get_collection()
    
    # Generate IDs if not provided
    if ids is None:
        ids = [str(uuid.uuid4()) for _ in documents]
    
    # Generate embeddings
    embeddings = embed_text(documents)
    
    # Add to collection
    collection.add(
        documents=documents,
        embeddings=embeddings.tolist(),
        metadatas=metadatas or [{}] * len(documents),
        ids=ids
    )
    
    return ids


def search(
    query: str,
    top_k: int = 5,
    filter_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for relevant documents.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        filter_metadata: Optional metadata filter
        
    Returns:
        List of results with 'content', 'metadata', 'score', 'id' keys
    """
    from .embeddings import embed_text
    
    collection = get_collection()
    
    # Generate query embedding
    query_embedding = embed_text(query)
    
    # Search
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
        where=filter_metadata
    )
    
    # Format results
    formatted = []
    for i in range(len(results['ids'][0])):
        formatted.append({
            'id': results['ids'][0][i],
            'content': results['documents'][0][i],
            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
            'score': 1 - results['distances'][0][i]  # Convert distance to similarity
        })
    
    return formatted


def delete_documents(ids: List[str]) -> None:
    """Delete documents by ID."""
    collection = get_collection()
    collection.delete(ids=ids)


def get_document_count() -> int:
    """Get total number of documents in collection."""
    collection = get_collection()
    return collection.count()


def clear_collection() -> None:
    """Delete all documents from collection."""
    global _collection
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None


# Simple test
if __name__ == "__main__":
    # Test basic operations
    print("Testing vector store...")
    
    test_docs = [
        "To become a software engineer, start with learning programming fundamentals like Python or JavaScript.",
        "Data science careers require skills in statistics, machine learning, and programming languages like Python or R.",
        "Job interviews for tech roles often include coding challenges and system design questions.",
    ]
    
    test_metadata = [
        {"category": "career_path", "topic": "software_engineering"},
        {"category": "career_path", "topic": "data_science"},
        {"category": "interview_prep", "topic": "general"},
    ]
    
    # Add documents
    ids = add_documents(test_docs, test_metadata)
    print(f"Added {len(ids)} documents")
    
    # Search
    results = search("How do I prepare for coding interviews?", top_k=2)
    print(f"\nSearch results for 'How do I prepare for coding interviews?':")
    for r in results:
        print(f"  Score: {r['score']:.3f} - {r['content'][:60]}...")
    
    print(f"\nTotal documents: {get_document_count()}")
