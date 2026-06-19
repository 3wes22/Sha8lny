"""
Unit tests for the structure-aware chunker (plan Task 1.6).

Replaces the fixed 500-char ``chunk_text`` (which split mid-sentence and was
fed heading-stripped text). Contract:

- Splits on H2/H3 boundaries; heading titles become ``section``/``subsection``
  metadata (the same keys the eval-set matchers rely on).
- Long sections are packed into chunks of <= max_chars, broken at sentence
  boundaries, with one-sentence overlap between consecutive chunks.
- Caller-provided base metadata (source, file, quality_tier, ...) is merged
  into every chunk's metadata.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.chunking import chunk_markdown  # noqa: E402


DOC = """# Backend Developer Roadmap

Intro paragraph about backend development as a career.

## Learning the Basics

Pick a language first. Python and JavaScript are common choices for beginners.

### Internet Fundamentals

HTTP is the foundation of data communication. DNS resolves names to addresses.

## Databases

Relational databases store data in tables. SQL is the standard query language.
"""

BASE_META = {"source": "roadmap.sh", "file": "backend.md", "quality_tier": "dev_fallback"}


def _chunks(text=DOC, max_chars=500):
    return chunk_markdown(text, base_metadata=BASE_META, max_chars=max_chars)


class TestStructure:
    def test_sections_become_metadata(self):
        sections = {c["metadata"].get("section") for c in _chunks()}
        assert "Learning the Basics" in sections
        assert "Databases" in sections

    def test_h3_becomes_subsection(self):
        sub = [c for c in _chunks() if c["metadata"].get("subsection") == "Internet Fundamentals"]
        assert len(sub) == 1
        assert "HTTP is the foundation" in sub[0]["content"]
        assert sub[0]["metadata"]["section"] == "Learning the Basics"

    def test_base_metadata_merged_into_every_chunk(self):
        for chunk in _chunks():
            assert chunk["metadata"]["source"] == "roadmap.sh"
            assert chunk["metadata"]["file"] == "backend.md"
            assert chunk["metadata"]["quality_tier"] == "dev_fallback"

    def test_heading_text_retained_in_content(self):
        db = [c for c in _chunks() if c["metadata"].get("section") == "Databases"][0]
        assert db["content"].startswith("## Databases")

    def test_preamble_before_first_h2_kept_with_doc_title_section(self):
        first = _chunks()[0]
        assert "Intro paragraph" in first["content"]
        assert first["metadata"]["section"] == "Backend Developer Roadmap"


class TestPacking:
    def setup_method(self):
        sentences = " ".join(f"Sentence number {i} explains a backend concept." for i in range(60))
        self.long_doc = f"## Big Section\n\n{sentences}\n"

    def test_long_section_split_into_multiple_chunks(self):
        chunks = chunk_markdown(self.long_doc, base_metadata=BASE_META, max_chars=500)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk["content"]) <= 500

    def test_chunks_end_on_sentence_boundary(self):
        chunks = chunk_markdown(self.long_doc, base_metadata=BASE_META, max_chars=500)
        for chunk in chunks:
            assert chunk["content"].rstrip().endswith("."), (
                f"chunk ends mid-sentence: ...{chunk['content'][-60:]!r}"
            )

    def test_consecutive_chunks_overlap_by_one_sentence(self):
        chunks = chunk_markdown(self.long_doc, base_metadata=BASE_META, max_chars=500)
        for prev, cur in zip(chunks, chunks[1:]):
            prev_sentences = [s for s in prev["content"].split(". ") if s.strip()]
            last_sentence = prev_sentences[-1].rstrip(".").strip()
            assert last_sentence in cur["content"], "no sentence overlap between chunks"

    def test_all_chunks_share_section_metadata(self):
        chunks = chunk_markdown(self.long_doc, base_metadata=BASE_META, max_chars=500)
        assert all(c["metadata"]["section"] == "Big Section" for c in chunks)


class TestEdgeCases:
    def test_tiny_sections_are_dropped(self):
        chunks = chunk_markdown("## A\n\nHi.\n\n## Real Section\n\n" + "Useful content. " * 10,
                                base_metadata=BASE_META)
        sections = {c["metadata"]["section"] for c in chunks}
        assert "A" not in sections  # below min length
        assert "Real Section" in sections

    def test_empty_text_returns_no_chunks(self):
        assert chunk_markdown("", base_metadata=BASE_META) == []

    def test_plain_text_without_headings_still_chunks(self):
        chunks = chunk_markdown("Plain prose. " * 30, base_metadata=BASE_META, max_chars=200)
        assert chunks
        assert all("section" in c["metadata"] for c in chunks)
