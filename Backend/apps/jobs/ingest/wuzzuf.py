"""
Parse saved Wuzzuf search-result HTML into job dicts.

Tested against HTML saved from Wuzzuf search pages (batch ingest, not live polling).
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

WUZZUF_BASE = "https://wuzzuf.net"


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def parse_wuzzuf_page(html: str, *, career_hint: str = "") -> list[dict[str, Any]]:
    """
    Parse a single Wuzzuf search results HTML page.

    Returns list of raw job dicts with keys used by ingest command.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs: list[dict[str, Any]] = []

    for card in soup.select("div[data-testid='job-card'], article.job-card, div.job-card"):
        title_el = card.select_one("h2 a, h3 a, a[href*='/jobs/']")
        if not title_el:
            continue
        title = _clean_text(title_el.get_text())
        href = title_el.get("href") or ""
        external_url = urljoin(WUZZUF_BASE, href) if href else ""
        company_el = card.select_one("[data-testid='company-name'], .company, .job-company")
        company_name = _clean_text(company_el.get_text() if company_el else "Unknown")
        location_el = card.select_one("[data-testid='location'], .location, .job-location")
        location_city = _clean_text(location_el.get_text() if location_el else "Cairo")

        external_id_match = re.search(r"/jobs/([^/?#]+)", external_url)
        external_id = external_id_match.group(1) if external_id_match else title.lower().replace(" ", "-")[:80]

        snippet = _clean_text(card.get_text(" ", strip=True))[:500]
        skills = _extract_skills(snippet, career_hint=career_hint)

        jobs.append(
            {
                "external_id": external_id,
                "title": title,
                "company_name": company_name,
                "location_city": location_city or "Cairo",
                "location_country": "Egypt",
                "external_url": external_url,
                "posted_date": date.today(),
                "experience_level": _infer_level(title),
                "job_type": "full_time",
                "is_remote": "remote" in snippet.lower(),
                "description": snippet,
                "requirements": snippet,
                "skills": skills,
                "source": "wuzzuf",
            }
        )

    if jobs:
        return jobs

    # Fallback: anchor tags that look like job links
    for index, anchor in enumerate(soup.select("a[href*='/jobs/']"), start=1):
        href = anchor.get("href") or ""
        title = _clean_text(anchor.get_text())
        if len(title) < 4:
            continue
        external_url = urljoin(WUZZUF_BASE, href)
        external_id_match = re.search(r"/jobs/([^/?#]+)", external_url)
        external_id = external_id_match.group(1) if external_id_match else f"job-{index}"
        jobs.append(
            {
                "external_id": external_id,
                "title": title,
                "company_name": "Unknown",
                "location_city": "Cairo",
                "location_country": "Egypt",
                "external_url": external_url,
                "posted_date": date.today(),
                "experience_level": _infer_level(title),
                "job_type": "full_time",
                "is_remote": False,
                "description": title,
                "requirements": title,
                "skills": _extract_skills(title, career_hint=career_hint),
                "source": "wuzzuf",
            }
        )
    return jobs


def _infer_level(title: str) -> str:
    lowered = title.lower()
    if any(token in lowered for token in ("senior", "lead", "principal", "staff")):
        return "senior"
    if any(token in lowered for token in ("junior", "entry", "graduate", "intern")):
        return "entry"
    return "mid"


def _extract_skills(text: str, *, career_hint: str = "") -> list[str]:
    catalog = [
        "Python",
        "Django",
        "FastAPI",
        "PostgreSQL",
        "SQL",
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "Docker",
        "AWS",
        "Git",
        "REST API",
        "Java",
        "Kotlin",
        "Flutter",
        "Data Analysis",
        "Pandas",
        "Machine Learning",
    ]
    found = [skill for skill in catalog if skill.lower() in text.lower()]
    if career_hint and not found:
        if "backend" in career_hint.lower():
            found = ["Python", "Django", "PostgreSQL"]
        elif "frontend" in career_hint.lower():
            found = ["JavaScript", "React", "TypeScript"]
        elif "data" in career_hint.lower():
            found = ["Python", "SQL", "Pandas"]
    return found[:6]
