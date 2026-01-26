"""Test the vector database"""
import chromadb
from sentence_transformers import SentenceTransformer

# Connect to database
client = chromadb.PersistentClient(path=r"c:\Users\mahmo\Grad\Sha8lny\ai-models\data\vector_db")

print("=" * 50)
print("VECTOR DATABASE TEST")
print("=" * 50)

# List collections
cols = client.list_collections()
print(f"\nCollections: {len(cols)}")

if cols:
    col = client.get_collection("career_knowledge")
    print(f"Documents in 'career_knowledge': {col.count()}")
    
    # Test query
    print("\n" + "-" * 50)
    print("TESTING QUERY")
    print("-" * 50)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query = "What skills do I need to become a backend developer?"
    print(f"Query: {query}")
    
    embedding = model.encode([query]).tolist()
    results = col.query(query_embeddings=embedding, n_results=5)
    
    print(f"\nTop 5 results:")
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        source = meta.get('source', 'unknown')
        category = meta.get('category', 'unknown') 
        print(f"\n{i+1}. [{source}] {category}")
        print(f"   {doc[:150]}...")
else:
    print("No collections found!")
