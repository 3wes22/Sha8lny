#!/usr/bin/env python3
"""Generate thesis evaluation charts from committed JSON artifacts (no network).

Outputs SVG bar charts to docs/thesis/assets/:
  - fig-5.2-ranker-ndcg.svg
  - fig-5.3-retrieval-recall-mrr.svg
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RANKER_JSON = ROOT / "ai-models" / "models" / "custom" / "job_ranker_eval.json"
RETRIEVAL_DIR = ROOT / "ai-models" / "eval_results" / "retrieval"
OUT_DIR = ROOT / "docs" / "thesis" / "assets"


def _bar_chart_svg(
    *,
    title: str,
    labels: list[str],
    series: list[tuple[str, list[float]]],
    y_max: float | None = None,
    width: int = 720,
    height: int = 420,
) -> str:
    margin = {"l": 70, "r": 20, "t": 50, "b": 90}
    plot_w = width - margin["l"] - margin["r"]
    plot_h = height - margin["t"] - margin["b"]
    n_groups = len(labels)
    n_series = len(series)
    if y_max is None:
        y_max = max(max(vals) for _, vals in series) * 1.15 or 1.0

    group_w = plot_w / max(n_groups, 1)
    bar_w = group_w / (n_series + 1)

    colors = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ca8a04"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="{width/2:.1f}" y="28" text-anchor="middle" font-family="system-ui,sans-serif" font-size="16" font-weight="600">{title}</text>',
    ]

    # y-axis grid
    for tick in [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        if tick > y_max:
            continue
        y = margin["t"] + plot_h - (tick / y_max) * plot_h
        parts.append(
            f'<line x1="{margin["l"]}" y1="{y:.1f}" x2="{width-margin["r"]}" y2="{y:.1f}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{margin["l"]-8}" y="{y+4:.1f}" text-anchor="end" font-family="system-ui,sans-serif" font-size="11" fill="#6b7280">{tick:.1f}</text>'
        )

    for gi, label in enumerate(labels):
        for si, (series_name, values) in enumerate(series):
            val = values[gi]
            x = margin["l"] + gi * group_w + si * bar_w + bar_w * 0.25
            bar_h = (val / y_max) * plot_h if y_max else 0
            y = margin["t"] + plot_h - bar_h
            color = colors[si % len(colors)]
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.9:.1f}" height="{bar_h:.1f}" fill="{color}" rx="3"/>'
            )
            parts.append(
                f'<text x="{x + bar_w*0.45:.1f}" y="{y-4:.1f}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="10" fill="#111827">{val:.3f}</text>'
            )
        lx = margin["l"] + gi * group_w + group_w / 2
        parts.append(
            f'<text x="{lx:.1f}" y="{height-20}" text-anchor="middle" font-family="system-ui,sans-serif" font-size="11" fill="#374151">{label}</text>'
        )

  # legend
    legend_x = margin["l"]
    legend_y = height - 55
    for si, (series_name, _) in enumerate(series):
        color = colors[si % len(colors)]
        parts.append(f'<rect x="{legend_x + si*160}" y="{legend_y}" width="12" height="12" fill="{color}" rx="2"/>')
        parts.append(
            f'<text x="{legend_x + si*160 + 18}" y="{legend_y+10}" font-family="system-ui,sans-serif" font-size="11" fill="#374151">{series_name}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def ranker_chart() -> str:
    data = json.loads(RANKER_JSON.read_text())
    metrics = data["metrics"]
    labels = ["NDCG@5", "NDCG@10", "MAP"]
    series = [
        ("LightGBM", [metrics["ndcg@5"]["lightgbm"], metrics["ndcg@10"]["lightgbm"], metrics["map"]["lightgbm"]]),
        ("Overlap", [metrics["ndcg@5"]["overlap_baseline"], metrics["ndcg@10"]["overlap_baseline"], metrics["map"]["overlap_baseline"]]),
        ("Random", [metrics["ndcg@5"]["random_baseline"], metrics["ndcg@10"]["random_baseline"], metrics["map"]["random_baseline"]]),
    ]
    return _bar_chart_svg(
        title="Job ranker: LightGBM vs baselines (LOO-CV)",
        labels=labels,
        series=series,
        y_max=0.65,
    )


def retrieval_chart() -> str:
    baseline = json.loads((RETRIEVAL_DIR / "baseline.json").read_text())["metrics"]
    final = json.loads((RETRIEVAL_DIR / "abstain_floor.json").read_text())["metrics"]
    labels = ["Recall@5", "MRR"]
    series = [
        ("Dense baseline", [baseline["recall@5"], baseline["mrr"]]),
        ("Final pipeline", [final["recall@5"], final["mrr"]]),
    ]
    return _bar_chart_svg(
        title="Retrieval: dense baseline vs final hybrid pipeline (55 queries)",
        labels=labels,
        series=series,
        y_max=0.7,
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "fig-5.2-ranker-ndcg.svg").write_text(ranker_chart())
    (OUT_DIR / "fig-5.3-retrieval-recall-mrr.svg").write_text(retrieval_chart())
    print(f"Wrote charts to {OUT_DIR}")


if __name__ == "__main__":
    main()
