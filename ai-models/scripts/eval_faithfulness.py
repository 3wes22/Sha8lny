"""LLM-as-judge faithfulness scorer (Task 4.1) — scaffold.

Faithfulness = does each advisory answer stay supported by its retrieved
passages? A judge (Gemini in production) returns 1 = supported / 0 = unsupported
per (answer, passages) item; we report the mean. Judge calls are **cached to
disk** so a run does not re-spend quota on unchanged items.

The judge is **injectable** so tests run with a deterministic stub and no
network/quota — production wiring passes a Gemini-backed judge. Running the real
judge is an operator step on a fresh ``GEMINI_API_KEY`` (the full test suite
exhausts quota).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

# (answer, passages) -> 1.0 supported / 0.0 unsupported
Judge = Callable[[str, list[str]], float]

_CACHE_DIR = Path(__file__).resolve().parents[1] / "eval_results" / "faithfulness"


def _item_key(answer: str, passages: list[str]) -> str:
    blob = json.dumps({"a": answer, "p": passages}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def score_faithfulness(
    items: Iterable[dict[str, Any]],
    judge: Judge,
    *,
    cache_dir: Path | None = None,
) -> dict[str, Any]:
    """Score a batch of {answer, passages} items with a judge, caching per item.

    Returns ``{"n": int, "faithfulness": float, "per_item": [...]}``.
    """
    cache_dir = cache_dir or _CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)

    per_item: list[dict[str, Any]] = []
    for item in items:
        answer = str(item.get("answer") or "")
        passages = [str(p) for p in (item.get("passages") or [])]
        key = _item_key(answer, passages)
        cache_path = cache_dir / f"{key}.json"

        if cache_path.exists():
            score = float(json.loads(cache_path.read_text())["score"])
            cached = True
        else:
            score = float(judge(answer, passages))
            cache_path.write_text(json.dumps({"score": score}))
            cached = False
        per_item.append({"key": key, "score": score, "cached": cached})

    n = len(per_item)
    mean = sum(entry["score"] for entry in per_item) / n if n else 0.0
    return {"n": n, "faithfulness": mean, "per_item": per_item}


def _gemini_judge(answer: str, passages: list[str]) -> float:  # pragma: no cover - operator path
    """Production judge — wired to Gemini. Run by the operator on a fresh key."""
    raise RuntimeError(
        "Gemini judge not wired in this environment; pass an injected judge or run "
        "with a real GEMINI_API_KEY via the backend GemmaClient."
    )


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Faithfulness eval (LLM judge).")
    parser.add_argument("--items", type=Path, help="JSON list of {answer, passages}.")
    args = parser.parse_args()
    data = json.loads(args.items.read_text()) if args.items else []
    result = score_faithfulness(data, _gemini_judge)
    print(json.dumps(result, indent=2))
