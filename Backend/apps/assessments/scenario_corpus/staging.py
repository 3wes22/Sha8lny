"""JSONL staging for generated drafts + promotion into per-role .py modules.

Drafts live in `_staging/<role>.jsonl` and are NEVER imported by the registry
(it only enumerates the role modules), so staged content can never reach
retrieval. Promotion appends reviewed dict literals into `<role>.py`'s
SCENARIOS list, keeping version control the source of truth.
"""

from __future__ import annotations

import json
import pprint
from pathlib import Path
from typing import Any

_CORPUS_DIR = Path(__file__).resolve().parent
_STAGING_DIR = _CORPUS_DIR / "_staging"


def staging_path(role_key: str) -> Path:
    return _STAGING_DIR / f"{role_key}.jsonl"


def append_drafts(role_key: str, docs: list[dict[str, Any]]) -> int:
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    path = staging_path(role_key)
    with path.open("a", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=True) + "\n")
    return len(docs)


def read_drafts(role_key: str) -> list[dict[str, Any]]:
    path = staging_path(role_key)
    if not path.exists():
        return []
    drafts: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            drafts.append(json.loads(line))
    return drafts


def write_drafts(role_key: str, docs: list[dict[str, Any]]) -> None:
    """Overwrite staging (used to drop promoted/rejected drafts)."""
    _STAGING_DIR.mkdir(parents=True, exist_ok=True)
    path = staging_path(role_key)
    with path.open("w", encoding="utf-8") as handle:
        for doc in docs:
            handle.write(json.dumps(doc, ensure_ascii=True) + "\n")


def format_scenario_literal(doc: dict[str, Any]) -> str:
    """Render one scenario as a black-compatible dict literal with trailing comma.
    `corpus_version` is emitted as a plain string value (not the symbol)."""
    body = pprint.pformat(dict(doc), width=88, sort_dicts=False)
    return f"    {body},\n"


def promote_to_module(role_key: str, docs: list[dict[str, Any]]) -> int:
    """Insert literals at the head of the module's SCENARIOS list (just after
    the opening ``[``). Head-insertion avoids having to find the matching
    closing ``]`` in a file whose scenario literals contain many ``]`` of their
    own; scenario order is irrelevant to the registry, so this is safe."""
    module_path = _CORPUS_DIR / f"{role_key}.py"
    source = module_path.read_text(encoding="utf-8")
    open_marker = "SCENARIOS: list[ScenarioDocument] = ["
    # Normalise the empty-stub form `... = []` to the multiline open form first.
    empty_form = "SCENARIOS: list[ScenarioDocument] = []"
    if empty_form in source:
        source = source.replace(empty_form, open_marker + "\n]")
    if open_marker not in source:
        raise ValueError(f"{module_path} has no recognizable SCENARIOS list opener")
    insert_at = source.index(open_marker) + len(open_marker)
    literals = "\n" + "".join(format_scenario_literal(doc) for doc in docs)
    new_source = source[:insert_at] + literals + source[insert_at:]
    module_path.write_text(new_source, encoding="utf-8")
    return len(docs)
