"""
Optimized RAG Query Script for LM Studio
- Caches embedding model and DB connection
- Better prompt engineering
- Shows retrieved context for debugging
"""

import chromadb
from sentence_transformers import SentenceTransformer
import requests

# Configuration
VECTOR_DB_PATH = r"c:\Users\mahmo\Grad\Sha8lny\ai-models\data\vector_db"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
TOP_K = 3  # Fewer but more relevant docs

# Global cache (loaded once)
_client = None
_collection = None
_embedder = None


def init_rag():
    """Initialize RAG components once"""
    global _client, _collection, _embedder
    
    if _embedder is None:
        print("📚 Loading embedding model (one time)...")
        _embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
    if _collection is None:
        print("📁 Connecting to ChromaDB...")
        _client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        _collection = _client.get_collection("career_knowledge")
        print(f"✅ Ready! {_collection.count()} documents loaded\n")


def query_rag(question: str) -> str:
    """Fast RAG query with smart source selection"""
    
    # Detect question type for source filtering
    question_lower = question.lower()
    learning_keywords = ['become', 'learn', 'roadmap', 'path', 'start', 'beginner', 'how to', 'skills needed', 'from scratch']
    job_keywords = ['work activities', 'job tasks', 'occupation', 'duties', 'responsibilities']
    
    # Choose source based on question type
    source_filter = None
    if any(kw in question_lower for kw in learning_keywords):
        source_filter = {"source": "roadmap.sh"}
        print("📌 Searching roadmap.sh (learning paths)")
    elif any(kw in question_lower for kw in job_keywords):
        source_filter = {"source": "onet"}
        print("📌 Searching O*NET (job data)")
    else:
        print("📌 Searching all sources")
    
    # 1. Get relevant context
    print(f"🔍 Searching...")
    query_embedding = _embedder.encode([question]).tolist()
    
    query_params = {
        "query_embeddings": query_embedding,
        "n_results": TOP_K
    }
    if source_filter:
        query_params["where"] = source_filter
        
    results = _collection.query(**query_params)
    
    # 2. Build focused context
    context_parts = []
    print("\n📖 Retrieved context:")
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        category = meta.get('category', 'general')
        snippet = doc[:200].replace('\n', ' ')
        print(f"  {i+1}. [{category}] {snippet}...")
        context_parts.append(f"[{category}]: {doc}")
    
    context = "\n\n".join(context_parts)
    
    # 3. Build prompt - balanced: use context but avoid hallucination
    system_prompt = """You are Sha8lny, a helpful career advisor.

Your job is to answer career questions using the context provided below.

RULES:
1. USE the context below to answer the question - synthesize and explain the information
2. If the context contains relevant information, provide a helpful answer based on it
3. Only say "I don't know" if the context is completely unrelated to the question
4. For topics outside career/tech (gaming, laptops, etc.), politely redirect to career topics
5. Don't invent specific numbers or statistics not in the context

Context:
{context}"""

    user_prompt = f"""Question: {question}

Provide a helpful answer using the context above."""

    # 4. Send to LM Studio with system prompt
    print("\n🤖 Generating answer...")
    payload = {
        "model": "local-model",
        "messages": [
            {"role": "system", "content": system_prompt.format(context=context)},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,  # Slightly higher for more natural responses
        "max_tokens": 400
    }
    
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.ConnectionError:
        return "❌ LM Studio not running. Start server at localhost:1234"
    except Exception as e:
        return f"❌ Error: {e}"


def main():
    print("=" * 50)
    print("🚀 Sha8lny RAG (Optimized)")
    print("=" * 50 + "\n")
    
    # Load once
    init_rag()
    
    print("Type 'quit' to exit\n")
    
    while True:
        question = input("💬 Question: ").strip()
        if question.lower() in ['quit', 'exit', 'q']:
            break
        if not question:
            continue
            
        answer = query_rag(question)
        print("\n" + "=" * 40)
        print("📝 Answer:")
        print("=" * 40)
        print(answer)
        print()


if __name__ == "__main__":
    main()
