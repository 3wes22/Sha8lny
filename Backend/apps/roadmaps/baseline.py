"""Annotate a roadmap blueprint with assessment-derived completion.

Pure, side-effect-free. Bands below the learner's entry point are marked
already-passed (``completed`` + ``from_assessment=True``) unless a flagged gap
keeps an individual milestone active; bands at/above the entry point are active
unless a proven-mastery signal pre-passes a milestone. Gaps win ties.
"""

from __future__ import annotations

import copy
import re
from typing import Any

# How many leading bands a learner has already cleared, by proficiency level.
ENTRY_BAND_BY_LEVEL: dict[str, int] = {
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}


def _tokens(label: str) -> list[str]:
    # Threshold is 3 (not 4) so short skill acronyms like "SQL" and "Git"
    # still match milestone text; see test_gap_in_passed_band_stays_active.
    return [tok for tok in re.split(r"[^a-z0-9]+", label.lower()) if len(tok) >= 3]


def _matches(labels: list[str], text: str) -> bool:
    lowered = text.lower()
    for label in labels:
        for tok in _tokens(label):
            if tok in lowered:
                return True
    return False


def apply_assessment_baseline(
    phases: list[dict[str, Any]],
    current_level: str,
    gaps: list[str],
    mastered: list[str],
) -> list[dict[str, Any]]:
    """Return a deep copy of ``phases`` with per-milestone status + from_assessment."""
    entry = ENTRY_BAND_BY_LEVEL.get((current_level or "").lower(), 0)
    gaps = [g for g in (gaps or []) if g]
    mastered = [m for m in (mastered or []) if m]
    out = copy.deepcopy(phases)

    for band_idx, phase in enumerate(out):
        for milestone in phase.get("milestones", []):
            text = " ".join(
                [
                    str(milestone.get("title", "")),
                    " ".join(str(s) for s in milestone.get("skills", [])),
                ]
            )
            matches_gap = _matches(gaps, text)
            matches_mastery = _matches(mastered, text)

            if band_idx < entry and not matches_gap:
                milestone["status"] = "completed"
                milestone["from_assessment"] = True
            elif band_idx >= entry and matches_mastery and not matches_gap:
                milestone["status"] = "completed"
                milestone["from_assessment"] = True
            else:
                milestone["status"] = "not_started"
                milestone["from_assessment"] = False

    return out
