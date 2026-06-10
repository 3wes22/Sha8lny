"""
Unit tests for the corpus validation layer (corpus v2).

Every file entering the fetched-corpus directories must pass shape checks
before the builder embeds it: provenance header (source/url/license/captured),
minimum substantive length, heading structure, no raw-HTML junk, no control
characters. Chunk-level dedupe removes exact duplicates within a source.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.corpus_validation import dedupe_chunks, validate_file_text  # noqa: E402


VALID = (
    "<!-- source: egypt_official | url: https://itida.gov.eg/x\n"
    "     license: official publication, excerpt-and-cite\n"
    "     captured: 2026-06-10 via research connector -->\n\n"
    "# Egypt ICT Sector\n\n"
    "## Growth\n\n" + ("The sector grows quickly and creates jobs. " * 20)
)


class TestValidateFileText:
    def test_valid_file_has_no_issues(self):
        assert validate_file_text(VALID) == []

    def test_missing_header_flagged(self):
        issues = validate_file_text("# Title\n\n" + "Body text here. " * 50)
        assert any("provenance header" in i for i in issues)

    def test_header_missing_fields_flagged(self):
        text = "<!-- source: x -->\n\n# T\n\n" + "Body. " * 100
        issues = validate_file_text(text)
        assert any("url" in i for i in issues)
        assert any("license" in i for i in issues)
        assert any("captured" in i for i in issues)

    def test_fetched_date_field_also_accepted(self):
        text = (
            "<!-- source: MDN Web Docs | url: https://developer.mozilla.org/x\n"
            "     license: CC-BY-SA 2.5 or later | attribution: Mozilla Contributors\n"
            "     fetched: 2026-06-10 -->\n\n"
            "# Title\n\n## Section\n\n" + "Useful prose content here. " * 30
        )
        assert validate_file_text(text) == []

    def test_too_short_body_flagged(self):
        text = VALID.split("# Egypt")[0] + "# T\n\nShort body."
        assert any("too short" in i for i in validate_file_text(text))

    def test_no_headings_flagged(self):
        text = (
            "<!-- source: x | url: https://e.g/x\n license: l\n captured: d -->\n\n"
            + "Plain prose without any structure at all. " * 20
        )
        assert any("heading" in i for i in validate_file_text(text))

    def test_html_junk_flagged(self):
        html = "<div><span>" * 80
        text = VALID + "\n" + html
        assert any("HTML" in i for i in validate_file_text(text))

    def test_control_characters_flagged(self):
        assert any("control" in i for i in validate_file_text(VALID + "\x00\x01"))


class TestDedupeChunks:
    def _chunk(self, content, source="roadmap.sh", category="backend"):
        return {"content": content, "metadata": {"source": source, "category": category}}

    def test_exact_duplicates_within_source_dropped(self):
        chunks = [self._chunk("Same   text."), self._chunk("same text.")]
        kept, dropped = dedupe_chunks(chunks)
        assert len(kept) == 1 and dropped == 1

    def test_same_content_different_category_kept(self):
        # the same roadmap topic legitimately appears under several roles
        chunks = [self._chunk("CORS basics."), self._chunk("CORS basics.", category="frontend")]
        kept, dropped = dedupe_chunks(chunks)
        assert len(kept) == 2 and dropped == 0

    def test_first_occurrence_wins(self):
        chunks = [self._chunk("A first."), self._chunk("Other."), self._chunk("a  FIRST.")]
        kept, _ = dedupe_chunks(chunks)
        assert kept[0]["content"] == "A first."
        assert len(kept) == 2
