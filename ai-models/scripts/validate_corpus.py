#!/usr/bin/env python3
"""
Corpus validation report (corpus v2).

Runs the validation layer over every fetched/authored corpus directory and
prints a pass/fail report. Exit code 1 if any file fails — usable as a
pre-build gate or CI check.

Usage:
    cd ai-models
    python3 scripts/validate_corpus.py
"""

from __future__ import annotations

import sys
from pathlib import Path

AI_MODELS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_MODELS_ROOT))

from src.rag.corpus_validation import validate_file  # noqa: E402

FETCHED_DIRS = ["bls_ooh", "mdn", "egypt_official", "tech_trends"]


def main() -> int:
    kb_dir = AI_MODELS_ROOT / "data" / "knowledge_base"
    failures = 0
    total = 0

    for dir_name in FETCHED_DIRS:
        source_dir = kb_dir / dir_name
        if not source_dir.exists():
            print(f"-- {dir_name}: directory missing, skipping")
            continue
        print(f"== {dir_name}/")
        for path in sorted(source_dir.glob("*.md")):
            total += 1
            issues = validate_file(path)
            if issues:
                failures += 1
                print(f"  FAIL {path.name}: {'; '.join(issues)}")
            else:
                print(f"  ok   {path.name}")

    print(f"\n{total - failures}/{total} files pass validation")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
