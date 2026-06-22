#!/usr/bin/env python3
"""Analyze completed expert-review scores from expert_review_scoring_sheet.csv.

Computes inter-rater stats on the overlap block (OE01–OE05) and mean absolute
difference vs optional engine scores JSON.

Usage:
  python ai-models/scripts/analyze_expert_review.py \\
    --csv docs/product/expert_review_scoring_sheet.csv \\
    --engine docs/product/expert_review_engine_scores.json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


def load_scores(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def overlap_pairwise_mad(rows: list[dict[str, str]], overlap_items: set[str]) -> dict[str, float]:
    by_item: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        item = row.get("item_id", "")
        score = row.get("score_1to5", "").strip()
        if item not in overlap_items or not score:
            continue
        by_item[item].append(float(score))

    pairwise_diffs: list[float] = []
    for scores in by_item.values():
        if len(scores) < 2:
            continue
        for i in range(len(scores)):
            for j in range(i + 1, len(scores)):
                pairwise_diffs.append(abs(scores[i] - scores[j]))

    if not pairwise_diffs:
        return {"items_with_scores": 0, "mean_pairwise_abs_diff": None}

    return {
        "items_with_scores": len(by_item),
        "mean_pairwise_abs_diff": statistics.mean(pairwise_diffs),
        "max_pairwise_abs_diff": max(pairwise_diffs),
    }


def engine_vs_human(rows: list[dict[str, str]], engine_path: Path) -> dict[str, float]:
    raw = json.loads(engine_path.read_text())
    engine = raw.get("scores", raw)

    human_by_item: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        item = row.get("item_id", "")
        score = row.get("score_1to5", "").strip()
        if item and score:
            human_by_item[item].append(float(score))

    diffs: list[float] = []
    for item, human_scores in human_by_item.items():
        entry = engine.get(item)
        if entry is None:
            continue
        engine_score = float(entry["score"] if isinstance(entry, dict) else entry)
        human_mean = statistics.mean(human_scores)
        diffs.append(abs(human_mean - engine_score))

    if not diffs:
        return {"compared_items": 0, "mean_abs_diff_vs_engine": None}

    return {
        "compared_items": len(diffs),
        "mean_abs_diff_vs_engine": statistics.mean(diffs),
        "max_abs_diff_vs_engine": max(diffs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze expert review CSV.")
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--engine", type=Path, help="Optional {item_id: engine_score} JSON")
    args = parser.parse_args()

    rows = load_scores(args.csv)
    filled = sum(1 for r in rows if r.get("score_1to5", "").strip())
    overlap = {f"OE{i:02d}" for i in range(1, 6)}

    report = {
        "total_rows": len(rows),
        "filled_scores": filled,
        "overlap_block": overlap_pairwise_mad(rows, overlap),
    }
    if filled == 0:
        report["status"] = "pending — no reviewer scores entered yet"
    else:
        report["status"] = "partial or complete"

    if args.engine and args.engine.exists():
        report["engine_comparison"] = engine_vs_human(rows, args.engine)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
