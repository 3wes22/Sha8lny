"""External taxonomy → curated role/subskill mappings.

These maps are deliberately empty in v1. They exist so that follow-up
content PRs that adapt external question banks (e.g. LinkedIn-style quiz
JSON, generic CS interview Q&A CSVs) into ``ScenarioDocument`` drafts have
a single explicit place to declare the mapping from external (role,
skill, subtopic) keys to curated ``(role_key, subskill_key)``.

Adapter scripts (``scripts/adapt_external_sources.py``, added later) read
these maps and emit ``review_status="draft"`` scenarios for human review.
Nothing in this module is consumed at request time.
"""

from __future__ import annotations


LINKEDIN_TO_ROLE_GRAPH: dict[tuple[str, str, str], tuple[str, str]] = {
    # ("backend-developer", "python", "oop"): ("backend", "service_decomposition"),
    # Populate per role in follow-up content PRs.
}


CSV_TO_ROLE_GRAPH: dict[str, tuple[str, str]] = {
    # "Explain the concept of polymorphism.": ("backend", "service_decomposition"),
    # Populate when authoring open-ended scenarios that draw from the
    # general interview-question CSV.
}
