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


def seed_database(clear_existing: bool = True, force: bool = False):
    """
    Seed the vector database with knowledge base documents.

    This seeds ONLY the top-level ``data/knowledge_base/*.md`` files. The full
    advisory corpus (KB + BLS/MDN + roadmap.sh + O*NET, ~64k chunks) is built by
    ``build_vector_db.py`` into the *same* ``career_knowledge`` collection.
    Because ``clear_existing`` deletes that collection first, running this seeder
    against an already-built corpus would shrink it to a few hundred KB sections
    and gut retrieval. A safety guard refuses to clear a collection that is
    larger than this KB-only seed unless ``force`` (or ``SEEDER_FORCE=1``) is set.

    Args:
        clear_existing: If True, clear existing data before seeding.
        force: Override the shrink guard and clear regardless.
    """
    print("=" * 50)
    print("Knowledge Base Seeder")
    print("=" * 50)

    # Load documents first so we can size the seed and guard against clobbering
    # the full corpus built by build_vector_db.py.
    print("\nLoading knowledge base documents...")
    documents = load_knowledge_base()

    if not documents:
        print("No documents found to seed!")
        return

    force = force or os.getenv("SEEDER_FORCE", "").lower() in {"1", "true", "yes"}

    # Clear existing data if requested (with shrink guard)
    if clear_existing:
        try:
            existing = get_document_count()
        except Exception:
            existing = 0
        if existing > len(documents) and not force:
            print(
                f"\n⛔ Refusing to clear: the 'career_knowledge' collection holds "
                f"{existing} documents, but this KB-only seed would replace them "
                f"with just {len(documents)}.\n"
                f"   This collection is built by 'python -m src.rag.build_vector_db' "
                f"(the full ~64k-chunk advisory corpus) and persists on disk.\n"
                f"   To rebuild the full corpus, run build_vector_db.\n"
                f"   To override this guard and seed KB-only anyway, pass --force "
                f"(or set SEEDER_FORCE=1)."
            )
            return
        print("\nClearing existing collection...")
        clear_collection()

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
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Seed the knowledge-base markdown sections into the career_knowledge "
            "collection. For the full advisory corpus, use build_vector_db instead."
        )
    )
    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Append without clearing the existing collection first.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear even if it would shrink a larger existing corpus.",
    )
    args = parser.parse_args()
    seed_database(clear_existing=not args.no_clear, force=args.force)
