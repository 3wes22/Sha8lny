"""Deterministic question-quality rubric, derived from AUTHOR_GUIDE.

Scores a generated question on cheap, reproducible signals so RAG-on vs RAG-off
can be compared without an LLM. Each check is a bool; `total` is their sum.
"""

from __future__ import annotations

import statistics
from typing import Any

_MIN_SCENARIO_WORDS = 8
_OPTIONS_CV_THRESHOLD = 0.5

_CHECK_KEYS = (
    "has_concrete_scenario",
    "no_banned_phrase",
    "decision_not_definition",
    "options_parallel",
    "uses_role_vocab",
)

_BANNED = (
    "disable logging",
    "preserves correctness, clarity, and maintainability",
    "generic self-rating",
)

# Minimal role-vocabulary anchors (extend per role as needed).
_ROLE_VOCAB = {
    "backend": ("idempotency", "queryset", "index", "transaction", "cache", "latency", "n+1"),
    "frontend": ("hydration", "re-render", "memo", "layout", "accessibility", "bundle"),
    "data_science": ("leakage", "bias", "variance", "stratified", "feature", "overfit"),
    "devops": ("rollback", "pipeline", "container", "scaling", "observability", "deploy"),
    "android": ("lifecycle", "coroutine", "recompose", "viewmodel", "intent", "fragment"),
    "machine_learning_engineer": ("inference", "throughput", "quantization", "serving", "drift"),
    "ui_ux_designer": ("affordance", "hierarchy", "contrast", "flow", "usability", "wireframe"),
    "fullstack": ("api", "state", "cache", "auth", "render", "schema"),
}


def score_question(question: dict[str, Any], *, role_key: str) -> dict[str, Any]:
    scenario = str(question.get("scenario_context") or "").strip()
    stem = str(question.get("stem") or "").lower()
    options = question.get("options") or []
    blob = " ".join([scenario.lower(), stem] + [str(o.get("label", "")).lower() for o in options])

    has_concrete_scenario = len(scenario.split()) >= _MIN_SCENARIO_WORDS
    no_banned_phrase = not any(b in blob for b in _BANNED)
    decision_not_definition = any(
        w in stem for w in ("which", "best", "most", "strongest", "prevents", "reduces")
    )
    if len(options) >= 2:
        lengths = [len(str(o.get("label", ""))) for o in options]
        options_parallel = (statistics.pstdev(lengths) / (statistics.mean(lengths) or 1)) < _OPTIONS_CV_THRESHOLD
    else:
        options_parallel = True
    vocab = _ROLE_VOCAB.get(role_key, ())
    uses_role_vocab = any(term in blob for term in vocab)

    checks = {
        "has_concrete_scenario": has_concrete_scenario,
        "no_banned_phrase": no_banned_phrase,
        "decision_not_definition": decision_not_definition,
        "options_parallel": options_parallel,
        "uses_role_vocab": uses_role_vocab,
    }
    checks["total"] = sum(1 for key in _CHECK_KEYS if checks[key])
    return checks
