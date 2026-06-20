"""Tests for expert review analysis helper."""

import json
from pathlib import Path

from scripts.analyze_expert_review import engine_vs_human, overlap_pairwise_mad


def test_overlap_pairwise_mad_with_no_scores():
    rows = [{"item_id": "OE01", "score_1to5": ""}]
    result = overlap_pairwise_mad(rows, {"OE01"})
    assert result["items_with_scores"] == 0


def test_overlap_pairwise_mad_computes_mean_diff(tmp_path: Path):
    rows = [
        {"item_id": "OE01", "score_1to5": "4"},
        {"item_id": "OE01", "score_1to5": "5"},
        {"item_id": "OE02", "score_1to5": "3"},
        {"item_id": "OE02", "score_1to5": "3"},
    ]
    result = overlap_pairwise_mad(rows, {"OE01", "OE02"})
    assert result["items_with_scores"] == 2
    assert result["mean_pairwise_abs_diff"] == 0.5  # only OE01 differs by 1


def test_engine_vs_human_reads_nested_scores(tmp_path: Path):
    engine_path = tmp_path / "engine.json"
    engine_path.write_text(
        json.dumps({"scores": {"OE01": {"score": 4.0, "scoring_method": "keyword_coverage"}}})
    )
    rows = [
        {"item_id": "OE01", "score_1to5": "3"},
        {"item_id": "OE01", "score_1to5": "5"},
    ]
    result = engine_vs_human(rows, engine_path)
    assert result["compared_items"] == 1
    assert result["mean_abs_diff_vs_engine"] == 0.0
