"""Parse curated job CSV exports into normalized ingest payloads."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_COLUMNS = {
    "external_id",
    "title",
    "company_name",
    "location_city",
    "external_url",
    "posted_date",
    "skills",
}


def _parse_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _parse_date(value: str):
    raw = str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def parse_jobs_csv(path: Path, *, source: str = "wuzzuf") -> list[dict[str, Any]]:
    """
    Load jobs from a CSV file.

    Expected columns: external_id, title, company_name, location_city,
    external_url, posted_date, skills (semicolon-separated), optional
    experience_level, job_type, is_remote, description, requirements.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {sorted(missing)}")

        for index, row in enumerate(reader, start=1):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            skills_raw = (row.get("skills") or "").strip()
            skills = [item.strip() for item in skills_raw.split(";") if item.strip()]
            external_url = (row.get("external_url") or "").strip()
            rows.append(
                {
                    "external_id": (row.get("external_id") or f"{source}-{index}").strip(),
                    "title": title,
                    "company_name": (row.get("company_name") or "Unknown").strip(),
                    "location_city": (row.get("location_city") or "Cairo").strip(),
                    "location_country": (row.get("location_country") or "Egypt").strip(),
                    "external_url": external_url or f"https://wuzzuf.net/jobs/{index}",
                    "posted_date": _parse_date(row.get("posted_date") or ""),
                    "experience_level": (row.get("experience_level") or "mid").strip(),
                    "job_type": (row.get("job_type") or "full_time").strip(),
                    "is_remote": _parse_bool(row.get("is_remote") or ""),
                    "description": (row.get("description") or "").strip(),
                    "requirements": (row.get("requirements") or "").strip(),
                    "skills": skills,
                    "source": source,
                }
            )
    return rows
