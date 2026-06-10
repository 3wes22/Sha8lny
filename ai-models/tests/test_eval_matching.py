"""
Unit tests for eval-set matcher semantics (plan Task 1.3).

Semantics (documented in tests/test_eval_set_schema.py): a matcher hits a
retrieved doc when every field it specifies matches — metadata equality for
source/file/section/subsection, case-insensitive substring for
content_contains.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag.eval_matching import first_hit_rank, hit_matcher_indexes, matcher_hits  # noqa: E402


DOC = {
    "id": "kb_ab12cd34_7",
    "content": "## Salary Negotiation in Egypt\nKnow your worth before the interview.",
    "metadata": {
        "source": "knowledge_base",
        "file": "egyptian_market.md",
        "section": "Salary Negotiation in Egypt",
    },
}


class TestMatcherHits:
    def test_full_metadata_match(self):
        matcher = {
            "source": "knowledge_base",
            "file": "egyptian_market.md",
            "section": "Salary Negotiation in Egypt",
        }
        assert matcher_hits(matcher, DOC) is True

    def test_partial_fields_only_specified_ones_checked(self):
        assert matcher_hits({"source": "knowledge_base", "file": "egyptian_market.md"}, DOC) is True

    def test_wrong_file_fails(self):
        assert matcher_hits({"source": "knowledge_base", "file": "learning_paths.md"}, DOC) is False

    def test_missing_metadata_key_fails(self):
        assert matcher_hits(
            {"source": "knowledge_base", "file": "egyptian_market.md", "subsection": "Anything"},
            DOC,
        ) is False

    def test_content_contains_case_insensitive(self):
        matcher = {"source": "knowledge_base", "file": "egyptian_market.md", "content_contains": "know your WORTH"}
        assert matcher_hits(matcher, DOC) is True

    def test_content_contains_absent_fails(self):
        matcher = {"source": "knowledge_base", "file": "egyptian_market.md", "content_contains": "15-1252.00"}
        assert matcher_hits(matcher, DOC) is False

    def test_doc_without_metadata_fails_gracefully(self):
        assert matcher_hits({"source": "knowledge_base", "file": "x.md"}, {"content": "hi"}) is False


class TestRankHelpers:
    def setup_method(self):
        other = {"content": "irrelevant", "metadata": {"source": "onet", "file": "Skills.txt"}}
        self.docs = [other, DOC, other]
        self.matchers = [
            {"source": "knowledge_base", "file": "egyptian_market.md"},
            {"source": "roadmap.sh", "file": "backend.md"},
        ]

    def test_first_hit_rank_one_indexed(self):
        assert first_hit_rank(self.docs, self.matchers) == 2

    def test_first_hit_rank_zero_when_no_hit(self):
        assert first_hit_rank(self.docs[:1], self.matchers) == 0

    def test_hit_matcher_indexes(self):
        assert hit_matcher_indexes(self.docs, self.matchers) == {0}

    def test_hit_matcher_indexes_with_k_limit(self):
        assert hit_matcher_indexes(self.docs, self.matchers, k=1) == set()
