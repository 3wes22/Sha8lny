"""
Schema validation for the retrieval eval question set (plan Task 1.2).

The eval set anchors relevance to *stable* chunk metadata, never to chunk ids
(ids are hash+index based and change on every rebuild — see
``src/rag/build_vector_db.py``). Matcher semantics, implemented by the eval
runner (Task 1.3):

- A retrieved chunk is a HIT for a matcher when every field specified in the
  matcher matches the chunk: ``source``/``file``/``section``/``subsection``
  compare against ``chunk.metadata`` by equality; ``content_contains`` is a
  case-insensitive substring test against the chunk text.
- A chunk is relevant to a query if ANY of the query's matchers hits.
- Per-query recall = fraction of the query's matchers hit by the top-k;
  precision@k / reciprocal rank treat "matches any matcher" as relevant.
"""

import json
from pathlib import Path

import pytest


AI_MODELS_ROOT = Path(__file__).parent.parent
EVAL_SET_PATH = AI_MODELS_ROOT / "data" / "eval" / "retrieval_eval_set.jsonl"
KB_DIR = AI_MODELS_ROOT / "data" / "knowledge_base"
ROADMAP_DIR = AI_MODELS_ROOT / "data" / "roadmap-sh-data" / "src" / "data"
ONET_DIR = AI_MODELS_ROOT / "data" / "onet_data" / "db_30_1_text"

ALLOWED_SOURCES = {"knowledge_base", "roadmap.sh", "onet"}
ALLOWED_MATCHER_KEYS = {"source", "file", "section", "subsection", "category", "content_contains"}
REQUIRED_ENTRY_KEYS = {"query_id", "query", "relevant"}
ALLOWED_ENTRY_KEYS = REQUIRED_ENTRY_KEYS | {"category", "notes"}


def _load_entries():
    if not EVAL_SET_PATH.exists():
        pytest.fail(f"Eval set missing: {EVAL_SET_PATH}")
    entries = []
    with EVAL_SET_PATH.open() as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                pytest.fail(f"Line {line_no} is not valid JSON: {exc}")
    return entries


@pytest.fixture(scope="module")
def entries():
    return _load_entries()


def test_minimum_size(entries):
    assert len(entries) >= 50, f"Eval set has {len(entries)} entries; need >= 50"


def test_unique_query_ids(entries):
    ids = [e["query_id"] for e in entries]
    assert len(ids) == len(set(ids)), "Duplicate query_id values found"


def test_entry_shape(entries):
    for entry in entries:
        missing = REQUIRED_ENTRY_KEYS - entry.keys()
        assert not missing, f"{entry.get('query_id')}: missing keys {missing}"
        unknown = entry.keys() - ALLOWED_ENTRY_KEYS
        assert not unknown, f"{entry.get('query_id')}: unknown keys {unknown}"
        assert isinstance(entry["query"], str) and len(entry["query"]) >= 10, (
            f"{entry['query_id']}: query must be a realistic question string"
        )
        assert isinstance(entry["relevant"], list) and entry["relevant"], (
            f"{entry['query_id']}: relevant must be a non-empty list"
        )


def test_matcher_shape(entries):
    for entry in entries:
        for matcher in entry["relevant"]:
            unknown = matcher.keys() - ALLOWED_MATCHER_KEYS
            assert not unknown, f"{entry['query_id']}: unknown matcher keys {unknown}"
            assert matcher.get("source") in ALLOWED_SOURCES, (
                f"{entry['query_id']}: matcher source must be one of {ALLOWED_SOURCES}"
            )
            has_anchor = isinstance(matcher.get("file"), str) and matcher["file"] or (
                isinstance(matcher.get("category"), str) and matcher["category"]
            )
            assert has_anchor, (
                f"{entry['query_id']}: matcher needs a file name or (roadmap.sh) a category"
            )
            for optional in ("section", "subsection", "content_contains"):
                if optional in matcher:
                    assert isinstance(matcher[optional], str) and matcher[optional], (
                        f"{entry['query_id']}: {optional} must be a non-empty string"
                    )


def test_ground_truth_files_exist(entries):
    """Every referenced file must exist on disk — no imaginary ground truth."""
    roadmap_names = None  # built lazily; the tree holds ~10k files
    for entry in entries:
        for matcher in entry["relevant"]:
            source, file_name = matcher["source"], matcher.get("file")
            if source == "knowledge_base":
                assert (KB_DIR / file_name).exists(), (
                    f"{entry['query_id']}: {file_name} not in knowledge_base/"
                )
            elif source == "onet":
                assert (ONET_DIR / file_name).exists(), (
                    f"{entry['query_id']}: {file_name} not in onet db_30_1_text/"
                )
            elif source == "roadmap.sh":
                category = matcher.get("category")
                if category:
                    category_dir = ROADMAP_DIR / "roadmaps" / category
                    assert category_dir.is_dir(), (
                        f"{entry['query_id']}: no roadmap category dir {category!r}"
                    )
                else:
                    if roadmap_names is None:
                        roadmap_names = {p.name for p in ROADMAP_DIR.rglob("*.md")}
                    assert file_name in roadmap_names, (
                        f"{entry['query_id']}: {file_name} not under roadmap-sh-data/src/data/"
                    )
