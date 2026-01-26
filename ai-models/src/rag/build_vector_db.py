"""
Vector Database Builder for Sha8lny RAG System
Processes roadmap.sh and O*NET data into ChromaDB embeddings
"""

import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Generator
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Configuration - Using absolute paths
BASE_DIR = Path(r"c:\Users\mahmo\Grad\Sha8lny\ai-models")
DATA_DIR = BASE_DIR / "data"
ROADMAP_DIR = DATA_DIR / "roadmap-sh-data" / "src" / "data"
ONET_DIR = DATA_DIR / "onet_data" / "db_30_1_text"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
CHUNK_SIZE = 500  # characters per chunk
CHUNK_OVERLAP = 50
BATCH_SIZE = 100  # documents per batch for embedding


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks"""
    if len(text) <= chunk_size:
        return [text] if text.strip() else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def process_roadmap_md(file_path: Path) -> List[Dict]:
    """Process a roadmap markdown file into documents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return []
    
    # Extract title from first header
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem
    
    # Get roadmap category from path
    parts = file_path.parts
    roadmap_idx = None
    for i, part in enumerate(parts):
        if part == 'roadmaps':
            roadmap_idx = i
            break
    
    category = parts[roadmap_idx + 1] if roadmap_idx and roadmap_idx + 1 < len(parts) else "general"
    
    # Clean content - remove links in format [@...](...)
    clean_content = re.sub(r'\[@[^\]]+\]\([^)]+\)', '', content)
    clean_content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean_content)
    clean_content = re.sub(r'#+ ', '', clean_content)  # Remove markdown headers
    clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)  # Normalize newlines
    
    # Chunk the content
    chunks = chunk_text(clean_content)
    
    documents = []
    # Create unique hash from full file path to avoid collisions
    path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
    for i, chunk in enumerate(chunks):
        documents.append({
            "id": f"rm_{category}_{path_hash}_{i}",
            "content": chunk,
            "metadata": {
                "source": "roadmap.sh",
                "category": category,
                "title": title,
                "file": file_path.name,
                "chunk_index": i
            }
        })
    
    return documents


def process_onet_file(file_path: Path) -> List[Dict]:
    """Process an O*NET text file into documents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return []
    
    file_name = file_path.stem
    
    # O*NET files are tab-delimited, process as structured data
    lines = content.strip().split('\n')
    if len(lines) < 2:
        return []
    
    headers = lines[0].split('\t')
    documents = []
    
    # For key files, create document per row
    key_files = ['Skills', 'Knowledge', 'Abilities', 'Occupation Data', 
                 'Task Statements', 'Technology Skills', 'Work Activities']
    
    if any(kf in file_name for kf in key_files):
        for i, line in enumerate(lines[1:], 1):
            fields = line.split('\t')
            if len(fields) >= 2:
                # Create readable content from row
                row_content = ' | '.join([f"{h}: {v}" for h, v in zip(headers, fields) if v.strip()])
                
                if len(row_content) > 50:  # Only include substantial content
                    # Use file name hash + row index for unique ID
                    file_hash = hashlib.md5(file_name.encode()).hexdigest()[:6]
                    documents.append({
                        "id": f"on_{file_hash}_{i}",
                        "content": row_content[:1000],  # Limit size
                        "metadata": {
                            "source": "onet",
                            "file": file_path.name,
                            "category": file_name.replace('_', ' '),
                            "row_index": i
                        }
                    })
    
    return documents


def collect_all_documents() -> Generator[Dict, None, None]:
    """Collect all documents from all sources"""
    
    # Process roadmap.sh markdown files
    print("📚 Processing roadmap.sh content...")
    md_files = list(ROADMAP_DIR.rglob("*.md"))
    for file_path in tqdm(md_files, desc="Roadmap files"):
        docs = process_roadmap_md(file_path)
        for doc in docs:
            yield doc
    
    # Process O*NET text files
    print("\n📊 Processing O*NET database...")
    txt_files = list(ONET_DIR.glob("*.txt"))
    for file_path in tqdm(txt_files, desc="O*NET files"):
        docs = process_onet_file(file_path)
        for doc in docs:
            yield doc


def build_vector_database():
    """Build the ChromaDB vector database"""
    
    print("=" * 60)
    print("🚀 Sha8lny RAG Vector Database Builder")
    print("=" * 60)
    
    # Initialize embedding model
    print("\n📥 Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Initialize ChromaDB
    print(f"📁 Initializing ChromaDB at: {VECTOR_DB_DIR}")
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    
    # Delete existing collection if exists
    try:
        client.delete_collection("career_knowledge")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(
        name="career_knowledge",
        metadata={"description": "Sha8lny career knowledge base for RAG"}
    )
    
    # Collect all documents
    print("\n📄 Collecting documents...")
    all_docs = list(collect_all_documents())
    print(f"\n✅ Total documents collected: {len(all_docs)}")
    
    # Process in batches
    print(f"\n🔄 Generating embeddings and storing (batch size: {BATCH_SIZE})...")
    
    for i in tqdm(range(0, len(all_docs), BATCH_SIZE), desc="Batches"):
        batch = all_docs[i:i + BATCH_SIZE]
        
        ids = [doc["id"] for doc in batch]
        contents = [doc["content"] for doc in batch]
        metadatas = [doc["metadata"] for doc in batch]
        
        # Generate embeddings
        embeddings = model.encode(contents, show_progress_bar=False).tolist()
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas
        )
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Vector Database Built Successfully!")
    print("=" * 60)
    print(f"📊 Total documents: {collection.count()}")
    print(f"📁 Database location: {VECTOR_DB_DIR}")
    print(f"📐 Embedding dimension: 384")
    print(f"🔧 Collection: career_knowledge")
    
    # Test query
    print("\n🧪 Testing with sample query...")
    test_query = "What skills do I need to become a backend developer?"
    test_embedding = model.encode([test_query]).tolist()
    results = collection.query(
        query_embeddings=test_embedding,
        n_results=3
    )
    
    print(f"Query: '{test_query}'")
    print("Top 3 results:")
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"  {i+1}. [{meta['source']}] {doc[:100]}...")
    
    return collection


if __name__ == "__main__":
    build_vector_database()
