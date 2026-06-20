"""Collect Gemini API keys for quota-aware rotation."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Mapping

# Google is migrating from standard keys (AIza…) to authorization keys (AQ.).
# Both work with ?key= on the Gemini REST API; accept either prefix.
_KEY_PREFIXES = ("AIza", "AQ.")
_MAX_NUMBERED_KEYS = 9
_AIza_PATTERN = re.compile(r"AIza[0-9A-Za-z_-]+")
_AQ_PATTERN = re.compile(r"AQ\.[0-9A-Za-z_-]+")


def _is_valid_key(value: str) -> bool:
    candidate = str(value or "").strip()
    if not any(candidate.startswith(prefix) for prefix in _KEY_PREFIXES):
        return False
    if candidate.startswith("your-") or candidate.endswith("-here"):
        return False
    return True


def _extract_keys_from_text(text: str) -> list[str]:
    found: list[str] = []
    for match in _AIza_PATTERN.finditer(text):
        _append_unique(found, match.group(0))
    for match in _AQ_PATTERN.finditer(text):
        _append_unique(found, match.group(0))
    return found


def _append_unique(keys: list[str], value: str) -> None:
    candidate = str(value or "").strip().strip('"').strip("'")
    if _is_valid_key(candidate) and candidate not in keys:
        keys.append(candidate)


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in str(raw or "").split(",") if part.strip()]


def _keys_from_env_mapping(env: Mapping[str, str]) -> list[str]:
    keys: list[str] = []
    _append_unique(keys, env.get("GEMINI_API_KEY", ""))
    for part in _split_csv(env.get("GEMINI_API_KEYS", "")):
        _append_unique(keys, part)
    for index in range(2, _MAX_NUMBERED_KEYS + 1):
        _append_unique(keys, env.get(f"GEMINI_API_KEY_{index}", ""))
    return keys


def _keys_from_env_file(path: Path, *, include_commented: bool = True) -> list[str]:
    keys: list[str] = []
    if not path.exists():
        return keys

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("GEMINI_API_KEY") and "=" in stripped and not stripped.startswith("#"):
            _append_unique(keys, stripped.split("=", 1)[1])
            continue

        if not include_commented or not stripped.startswith("#"):
            continue

        body = stripped.lstrip("#").strip()
        if body.startswith("GEMINI_API_KEY") and "=" in body:
            _append_unique(keys, body.split("=", 1)[1])
            continue
        if any(body.startswith(prefix) for prefix in _KEY_PREFIXES):
            _append_unique(keys, body)
            continue

        for key in _extract_keys_from_text(body):
            _append_unique(keys, key)

    return keys


def collect_gemini_api_keys(
    *,
    env: Mapping[str, str] | None = None,
    env_file: Path | None = None,
    include_commented_from_file: bool = True,
) -> list[str]:
    """Return deduplicated Gemini keys in priority order."""
    environment = env if env is not None else os.environ
    keys = _keys_from_env_mapping(environment)
    if env_file is not None:
        for key in _keys_from_env_file(env_file, include_commented=include_commented_from_file):
            _append_unique(keys, key)
    return keys
