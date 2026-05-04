"""
Embedding Engine for RAG System.
"""

from typing import List, Union
import numpy as np

from .runtime_settings import get_embedding_model

# Lazy loading to avoid slow imports at module level
_model = None


def get_model():
    """Lazy load the sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(get_embedding_model())
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Run: pip install sentence-transformers"
            )
    return _model


def embed_text(text: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
    """
    Generate embeddings for text input.
    
    Args:
        text: Single string or list of strings to embed
        normalize: If True, normalize vectors to unit length (recommended for cosine similarity)
    
    Returns:
        numpy array of shape (num_texts, 384) for list input
        numpy array of shape (384,) for single string input
    """
    model = get_model()
    
    # Handle single string
    single_input = isinstance(text, str)
    if single_input:
        text = [text]
    
    # Generate embeddings
    embeddings = model.encode(
        text,
        normalize_embeddings=normalize,
        show_progress_bar=len(text) > 100  # Only show progress for large batches
    )
    
    if single_input:
        return embeddings[0]
    
    return embeddings


def embed_documents(documents: List[dict]) -> List[dict]:
    """
    Embed a list of documents with 'content' field.
    
    Args:
        documents: List of dicts with at least 'content' key
        
    Returns:
        Same documents with 'embedding' key added
    """
    contents = [doc['content'] for doc in documents]
    embeddings = embed_text(contents)
    
    for doc, emb in zip(documents, embeddings):
        doc['embedding'] = emb.tolist()
    
    return documents


def cosine_similarity(query_embedding: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between query and documents.
    
    Args:
        query_embedding: Shape (384,)
        doc_embeddings: Shape (num_docs, 384)
        
    Returns:
        Similarity scores of shape (num_docs,)
    """
    # If embeddings are normalized, dot product equals cosine similarity
    return np.dot(doc_embeddings, query_embedding)


# Simple test
if __name__ == "__main__":
    test_texts = [
        "How do I become a software engineer?",
        "What skills do I need for data science?",
        "Recipe for chocolate cake"  # Out of scope for testing
    ]
    
    embeddings = embed_text(test_texts)
    print(f"Generated {len(embeddings)} embeddings of shape {embeddings[0].shape}")
    
    # Test similarity
    query = embed_text("I want to learn programming for a job")
    similarities = cosine_similarity(query, embeddings)
    
    print("\nQuery: 'I want to learn programming for a job'")
    for text, sim in zip(test_texts, similarities):
        print(f"  {sim:.3f} - {text}")
