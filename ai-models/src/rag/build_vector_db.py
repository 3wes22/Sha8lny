"""
Vector Database Builder for Sha8alny RAG System

Processes three data sources into ChromaDB embeddings:
  1. Knowledge base markdown files  (ai-models/data/knowledge_base/)
  2. Roadmap.sh career roadmaps     (ai-models/data/roadmap-sh-data/)
  3. O*NET occupation database       (ai-models/data/onet_data/)

Usage:
    cd ai-models
    python -m src.rag.build_vector_db
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, Generator, List

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from .runtime_settings import get_chroma_persist_dir, get_embedding_model

# ---------------------------------------------------------------------------
# Configuration — all paths relative to this file's location
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent          # ai-models/
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "knowledge_base"
ROADMAP_DIR = DATA_DIR / "roadmap-sh-data" / "src" / "data"
ONET_DIR = DATA_DIR / "onet_data" / "db_30_1_text"
VECTOR_DB_DIR = DATA_DIR / "vector_db"

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 50
BATCH_SIZE = 100       # documents per batch for embedding


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
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


# ---------------------------------------------------------------------------
# Source 1: Knowledge base markdown
# ---------------------------------------------------------------------------

def process_kb_md(file_path: Path) -> List[Dict]:
    """Process a knowledge-base markdown file into section-level documents."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    documents: List[Dict] = []
    h2_sections = re.split(r"\n## ", content)

    for section in h2_sections:
        if not section.strip():
            continue

        lines = section.split("\n")
        title = lines[0].strip().lstrip("#").strip()
        body = "\n".join(lines[1:]).strip()

        if len(body) < 50:
            continue

        # Sub-split long sections by H3
        if len(body) > 2000:
            h3_parts = re.split(r"\n### ", body)
            for h3 in h3_parts:
                if not h3.strip() or len(h3.strip()) < 50:
                    continue
                h3_lines = h3.split("\n")
                h3_title = h3_lines[0].strip().lstrip("#").strip()
                h3_body = "\n".join(h3_lines[1:]).strip()
                if h3_body:
                    path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                    documents.append({
                        "id": f"kb_{path_hash}_{len(documents)}",
                        "content": f"## {title}\n### {h3_title}\n{h3_body}",
                        "metadata": {
                            "source": "knowledge_base",
                            "category": _categorize(title, h3_title),
                            "section": title,
                            "subsection": h3_title,
                            "file": file_path.name,
                        },
                    })
        else:
            path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
            documents.append({
                "id": f"kb_{path_hash}_{len(documents)}",
                "content": f"## {title}\n{body}",
                "metadata": {
                    "source": "knowledge_base",
                    "category": _categorize(title, ""),
                    "section": title,
                    "file": file_path.name,
                },
            })

    return documents


def _categorize(title: str, subsection: str) -> str:
    """Categorize content based on title keywords."""
    combined = f"{title} {subsection}".lower()
    if any(w in combined for w in ["career", "job", "interview", "resume", "cv", "salary"]):
        return "career_development"
    if any(w in combined for w in ["learn", "course", "study", "path", "roadmap"]):
        return "learning"
    if any(w in combined for w in ["egypt", "cairo", "market", "companies"]):
        return "egyptian_market"
    if any(w in combined for w in ["skill", "assess", "gap", "develop"]):
        return "skill_development"
    return "general"


# ---------------------------------------------------------------------------
# Source 2: Roadmap.sh markdown files
# ---------------------------------------------------------------------------

def process_roadmap_md(file_path: Path) -> List[Dict]:
    """Process a roadmap markdown file into documents."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem

    # Derive category from path
    parts = file_path.parts
    roadmap_idx = None
    for i, part in enumerate(parts):
        if part == "roadmaps":
            roadmap_idx = i
            break
    category = parts[roadmap_idx + 1] if roadmap_idx and roadmap_idx + 1 < len(parts) else "general"

    # Clean content
    clean = re.sub(r"\[@[^\]]+\]\([^)]+\)", "", content)
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
    clean = re.sub(r"#+ ", "", clean)
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    chunks = chunk_text(clean)
    path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]

    return [
        {
            "id": f"rm_{category}_{path_hash}_{i}",
            "content": chunk,
            "metadata": {
                "source": "roadmap.sh",
                "category": category,
                "title": title,
                "file": file_path.name,
                "chunk_index": i,
            },
        }
        for i, chunk in enumerate(chunks)
    ]


# ---------------------------------------------------------------------------
# Source 3: O*NET occupation data
# ---------------------------------------------------------------------------

KEY_ONET_FILES = [
    "Skills", "Knowledge", "Abilities", "Occupation Data",
    "Task Statements", "Technology Skills", "Work Activities",
]


def process_onet_file(file_path: Path) -> List[Dict]:
    """Process an O*NET text file into documents."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    file_name = file_path.stem
    lines = content.strip().split("\n")
    if len(lines) < 2:
        return []

    # Only process key files
    if not any(kf in file_name for kf in KEY_ONET_FILES):
        return []

    headers = lines[0].split("\t")
    documents: List[Dict] = []

    for i, line in enumerate(lines[1:], 1):
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        row_content = " | ".join(
            f"{h}: {v}" for h, v in zip(headers, fields) if v.strip()
        )
        if len(row_content) > 50:
            file_hash = hashlib.md5(file_name.encode()).hexdigest()[:6]
            documents.append({
                "id": f"on_{file_hash}_{i}",
                "content": row_content[:1000],
                "metadata": {
                    "source": "onet",
                    "file": file_path.name,
                    "category": file_name.replace("_", " "),
                    "row_index": i,
                },
            })

    return documents


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

def collect_all_documents() -> Generator[Dict, None, None]:
    """Collect all documents from all available sources."""

    # 1. Knowledge base
    if KB_DIR.exists():
        print("📚 Processing knowledge base documents...")
        md_files = sorted(KB_DIR.glob("*.md"))
        for file_path in tqdm(md_files, desc="Knowledge base"):
            for doc in process_kb_md(file_path):
                yield doc
    else:
        print(f"⚠️  Knowledge base not found at {KB_DIR}, skipping.")

    # 2. Roadmap.sh
    if ROADMAP_DIR.exists():
        print("\n📚 Processing roadmap.sh content...")
        md_files = list(ROADMAP_DIR.rglob("*.md"))
        for file_path in tqdm(md_files, desc="Roadmap files"):
            for doc in process_roadmap_md(file_path):
                yield doc
    else:
        print(f"⚠️  Roadmap data not found at {ROADMAP_DIR}, skipping.")

    # 3. O*NET
    if ONET_DIR.exists():
        print("\n📊 Processing O*NET database...")
        txt_files = sorted(ONET_DIR.glob("*.txt"))
        for file_path in tqdm(txt_files, desc="O*NET files"):
            for doc in process_onet_file(file_path):
                yield doc
    else:
        print(f"⚠️  O*NET data not found at {ONET_DIR}, skipping.")


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_vector_database():
    """Build the ChromaDB vector database from all data sources."""

    print("=" * 60)
    print("🚀 Sha8alny RAG Vector Database Builder")
    print("=" * 60)

    # Load embedding model
    embedding_model = get_embedding_model()
    persist_dir = get_chroma_persist_dir()

    print(f"\n📥 Loading embedding model ({embedding_model})...")
    model = SentenceTransformer(embedding_model)

    # Initialise ChromaDB
    print(f"📁 Initializing ChromaDB at: {persist_dir}")
    persist_dir.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(persist_dir),
        settings=Settings(anonymized_telemetry=False),
    )

    # Fresh collection
    try:
        client.delete_collection("career_knowledge")
    except Exception:
        pass

    collection = client.create_collection(
        name="career_knowledge",
        metadata={"description": "Sha8alny career knowledge base for RAG"},
    )

    # Collect
    print("\n📄 Collecting documents...")
    all_docs = list(collect_all_documents())
    print(f"\n✅ Total documents collected: {len(all_docs)}")

    if not all_docs:
        print("❌ No documents found — check that data/ directories have content.")
        return None

    # Embed + store in batches
    print(f"\n🔄 Generating embeddings and storing (batch size: {BATCH_SIZE})...")

    for i in tqdm(range(0, len(all_docs), BATCH_SIZE), desc="Batches"):
        batch = all_docs[i : i + BATCH_SIZE]
        ids = [doc["id"] for doc in batch]
        contents = [doc["content"] for doc in batch]
        metadatas = [doc["metadata"] for doc in batch]

        embeddings = model.encode(contents, show_progress_bar=False).tolist()

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=metadatas,
        )

    # Summary
    print("\n" + "=" * 60)
    print("✅ Vector Database Built Successfully!")
    print("=" * 60)
    print(f"📊 Total documents: {collection.count()}")
    print(f"📁 Database location: {persist_dir}")
    print(f"📐 Embedding dimension: 384")
    print(f"🔧 Collection: career_knowledge")

    # Category breakdown
    sources: Dict[str, int] = {}
    for doc in all_docs:
        src = doc["metadata"].get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    print("\nSource breakdown:")
    for src, count in sorted(sources.items()):
        print(f"  - {src}: {count}")

    # Quick test query (non-fatal — index may already be complete)
    print("\n🧪 Testing with sample query...")
    try:
        test_query = "What skills do I need to become a backend developer?"
        test_embedding = model.encode([test_query]).tolist()
        results = collection.query(query_embeddings=test_embedding, n_results=3)

        print(f"Query: '{test_query}'")
        print("Top 3 results:")
        for i, (doc, meta) in enumerate(
            zip(results["documents"][0], results["metadatas"][0])
        ):
            print(f"  {i+1}. [{meta['source']}] {doc[:100]}...")
    except Exception as error:
        print(f"⚠️  Post-build smoke query failed (index may still be usable): {error}")

    return collection


if __name__ == "__main__":
    build_vector_database()
