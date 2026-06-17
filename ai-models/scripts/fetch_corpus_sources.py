#!/usr/bin/env python3
"""
Fetch license-approved corpus sources into the knowledge base (plan Task 1.7).

Sources and licenses are registered in docs/product/DATASET_REGISTRY.md
(registry-first rule: licenses were verified 2026-06-10, before this script
was written).

- MDN Web Docs (CC-BY-SA 2.5+, attribution "Mozilla Contributors"): fetched
  directly; each output file carries an attribution header.
- BLS Occupational Outlook Handbook (US public domain): bls.gov serves 403 to
  non-browser clients, so profile pages are captured via the research
  connector and committed under data/knowledge_base/bls_ooh/ with provenance
  headers. BLS_OOH_PAGES below is the authoritative list of captured pages.

Usage:
    cd ai-models
    ../Backend/venv/bin/python scripts/fetch_corpus_sources.py --source mdn
"""

from __future__ import annotations

import argparse
import ssl
import time
import urllib.request
from datetime import date
from pathlib import Path


def _ssl_context() -> ssl.SSLContext:
    """macOS Pythons often lack a wired CA bundle; prefer certifi's."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()

AI_MODELS_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = AI_MODELS_ROOT / "data" / "knowledge_base"

USER_AGENT = "Sha8lnyGradProject/1.0 (academic; corpus fetch; contact: repo)"

# slug -> URL. Slugs become file names: <slug>.md
MDN_PAGES = {
    "http-overview": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview",
    "http-caching": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching",
    "http-cors": "https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS",
    "rest-glossary": "https://developer.mozilla.org/en-US/docs/Glossary/REST",
    "javascript-introduction": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction",
    "javascript-event-loop": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Event_loop",
    "fetch-api": "https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API",
    "web-security": "https://developer.mozilla.org/en-US/docs/Web/Security",
    "web-performance": "https://developer.mozilla.org/en-US/docs/Web/Performance",
    "accessibility": "https://developer.mozilla.org/en-US/docs/Web/Accessibility",
    "css-layout-intro": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Introduction",
    "responsive-design": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design",
}

# Captured via research connector (bls.gov blocks scripted fetches).
# Public domain (17 U.S.C. §105). Kept here as the provenance record.
BLS_OOH_PAGES = {
    "software-developers": "https://www.bls.gov/ooh/computer-and-information-technology/software-developers.htm",
    "web-developers": "https://www.bls.gov/ooh/computer-and-information-technology/web-developers.htm",
    "data-scientists": "https://www.bls.gov/ooh/math/data-scientists.htm",
    "database-administrators": "https://www.bls.gov/ooh/computer-and-information-technology/database-administrators.htm",
    "computer-systems-analysts": "https://www.bls.gov/ooh/computer-and-information-technology/computer-systems-analysts.htm",
    "information-security-analysts": "https://www.bls.gov/ooh/computer-and-information-technology/information-security-analysts.htm",
    "network-systems-administrators": "https://www.bls.gov/ooh/computer-and-information-technology/network-and-computer-systems-administrators.htm",
    "computer-support-specialists": "https://www.bls.gov/ooh/computer-and-information-technology/computer-support-specialists.htm",
}


def html_to_markdown(html: str) -> str:
    """Extract the main article as heading-structured plain text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find("article") or soup.body
    if main is None:
        return ""

    for tag in main.find_all(["nav", "aside", "script", "style", "footer", "iframe"]):
        tag.decompose()

    lines = []
    for el in main.find_all(["h1", "h2", "h3", "p", "li", "pre"]):
        text = el.get_text(" ", strip=True)
        if not text:
            continue
        if el.name == "h1":
            lines.append(f"# {text}")
        elif el.name == "h2":
            lines.append(f"## {text}")
        elif el.name == "h3":
            lines.append(f"### {text}")
        elif el.name == "li":
            lines.append(f"- {text}")
        else:
            lines.append(text)
    return "\n\n".join(lines)


def fetch_mdn(force: bool = False) -> int:
    out_dir = KB_DIR / "mdn"
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0

    for slug, url in MDN_PAGES.items():
        out_path = out_dir / f"{slug}.md"
        if out_path.exists() and not force:
            print(f"  skip (exists): {slug}")
            continue
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=30, context=_ssl_context()) as response:
                html = response.read().decode("utf-8", errors="replace")
        except Exception as error:
            print(f"  FAILED {slug}: {error}")
            continue

        body = html_to_markdown(html)
        if len(body) < 500:
            print(f"  FAILED {slug}: extracted body too short ({len(body)} chars)")
            continue

        header = (
            f"<!-- source: MDN Web Docs | url: {url}\n"
            f"     license: CC-BY-SA 2.5 or later | attribution: Mozilla Contributors\n"
            f"     fetched: {date.today().isoformat()} -->\n\n"
        )
        out_path.write_text(header + body + "\n")
        print(f"  wrote {out_path.name} ({len(body)} chars)")
        written += 1
        time.sleep(1)  # be polite

    return written


def convert_bls_extract(extract_json_path: Path) -> int:
    """Convert a research-connector extract JSON into bls_ooh corpus files.

    The connector returns {results: [{url, raw_content, ...}]}. File names are
    derived from the URL stem so they match the BLS_OOH_PAGES provenance list.
    """
    import json

    out_dir = KB_DIR / "bls_ooh"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.loads(Path(extract_json_path).read_text())

    written = 0
    for result in payload.get("results", []):
        url = result.get("url", "")
        body = (result.get("raw_content") or "").strip()
        slug = url.rstrip("/").rsplit("/", 1)[-1].removesuffix(".htm")
        if not slug or len(body) < 1000:
            print(f"  FAILED {slug or url}: body too short ({len(body)} chars)")
            continue
        header = (
            f"<!-- source: BLS Occupational Outlook Handbook | url: {url}\n"
            f"     license: U.S. federal government work, public domain (17 U.S.C. 105)\n"
            f"     captured: {date.today().isoformat()} via research connector\n"
            f"     (bls.gov serves 403 to scripted fetches) -->\n\n"
        )
        (out_dir / f"{slug}.md").write_text(header + body + "\n")
        print(f"  wrote {slug}.md ({len(body)} chars)")
        written += 1

    for failed in payload.get("failed_results", []):
        print(f"  FAILED (connector): {failed}")
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["mdn", "bls_ooh"], required=True)
    parser.add_argument("--force", action="store_true", help="re-fetch existing files")
    parser.add_argument("--extract-json", type=Path,
                        help="bls_ooh: path to a research-connector extract JSON to convert")
    args = parser.parse_args()

    if args.source == "mdn":
        written = fetch_mdn(force=args.force)
        print(f"\nMDN: {written} new files in {KB_DIR / 'mdn'}")
    elif args.source == "bls_ooh":
        if not args.extract_json:
            parser.error("--source bls_ooh requires --extract-json (see module docstring)")
        written = convert_bls_extract(args.extract_json)
        print(f"\nBLS OOH: {written} new files in {KB_DIR / 'bls_ooh'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
