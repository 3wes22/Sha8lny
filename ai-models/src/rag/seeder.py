"""
Knowledge Base Seeder

Seeds the vector database with career knowledge documents.
Run this after setting up the RAG system.
"""

import os
from pathlib import Path
from typing import List, Dict
import re

from .vector_store import add_documents, clear_collection, get_document_count


# Path to knowledge base documents
KB_PATH = Path(__file__).parent.parent.parent / "data" / "knowledge_base"


def parse_markdown_sections(content: str, source_file: str) -> List[Dict]:
    """
    Parse markdown content into sections for better retrieval.
    
    Each H2 (##) or H3 (###) section becomes a separate document.
    """
    documents = []
    
    # Split by H2 headers
    h2_sections = re.split(r'\n## ', content)
    
    for section in h2_sections:
        if not section.strip():
            continue
        
        # Get the section title
        lines = section.split('\n')
        title = lines[0].strip().lstrip('#').strip()
        body = '\n'.join(lines[1:]).strip()
        
        if len(body) < 50:  # Skip very short sections
            continue
        
        # Further split by H3 if section is too long
        if len(body) > 2000:
            h3_sections = re.split(r'\n### ', body)
            for h3 in h3_sections:
                if not h3.strip() or len(h3.strip()) < 50:
                    continue
                h3_lines = h3.split('\n')
                h3_title = h3_lines[0].strip().lstrip('#').strip()
                h3_body = '\n'.join(h3_lines[1:]).strip()
                
                if h3_body:
                    documents.append({
                        "content": f"## {title}\n### {h3_title}\n{h3_body}",
                        "metadata": {
                            "source": source_file,
                            "section": title,
                            "subsection": h3_title,
                            "category": categorize_content(title, h3_title),
                        }
                    })
        else:
            documents.append({
                "content": f"## {title}\n{body}",
                "metadata": {
                    "source": source_file,
                    "section": title,
                    "category": categorize_content(title, ""),
                }
            })
    
    return documents


def categorize_content(title: str, subsection: str) -> str:
    """Categorize content based on title keywords."""
    combined = f"{title} {subsection}".lower()
    
    if any(word in combined for word in ["career", "job", "interview", "resume", "cv", "salary"]):
        return "career_development"
    elif any(word in combined for word in ["learn", "course", "study", "path", "roadmap"]):
        return "learning"
    elif any(word in combined for word in ["egypt", "cairo", "market", "companies"]):
        return "egyptian_market"
    elif any(word in combined for word in ["skill", "assess", "gap", "develop"]):
        return "skill_development"
    else:
        return "general"


def load_knowledge_base() -> List[Dict]:
    """Load all markdown files from knowledge base."""
    all_documents = []
    
    if not KB_PATH.exists():
        print(f"Knowledge base path not found: {KB_PATH}")
        return []
    
    for md_file in KB_PATH.glob("*.md"):
        print(f"Processing: {md_file.name}")
        
        content = md_file.read_text(encoding="utf-8")
        documents = parse_markdown_sections(content, md_file.name)
        all_documents.extend(documents)
        
        print(f"  → Extracted {len(documents)} sections")
    
    return all_documents


def seed_database(clear_existing: bool = True):
    """
    Seed the vector database with knowledge base documents.
    
    Args:
        clear_existing: If True, clear existing data before seeding
    """
    print("=" * 50)
    print("Knowledge Base Seeder")
    print("=" * 50)
    
    # Clear existing data if requested
    if clear_existing:
        print("\nClearing existing collection...")
        clear_collection()
    
    # Load documents
    print("\nLoading knowledge base documents...")
    documents = load_knowledge_base()
    
    if not documents:
        print("No documents found to seed!")
        return
    
    print(f"\nTotal documents to seed: {len(documents)}")
    
    # Prepare for insertion
    contents = [doc["content"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    
    # Add to vector store
    print("\nSeeding vector database...")
    ids = add_documents(contents, metadatas)
    
    print(f"\n✅ Successfully seeded {len(ids)} documents")
    print(f"Current document count: {get_document_count()}")
    
    # Show category breakdown
    categories = {}
    for doc in documents:
        cat = doc["metadata"].get("category", "unknown")
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\nCategory breakdown:")
    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}")


if __name__ == "__main__":
    seed_database()
