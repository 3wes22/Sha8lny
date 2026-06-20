"""Clean + role-tag the raw Coursera dataset into a usable career-course catalog.

Input:  coursera_raw.csv   (azrai99/coursera-course-dataset, 6.6k all-of-Coursera rows)
Output: coursera_clean.csv / coursera_clean.json  (tech/career-relevant, role-tagged)
        + a printed data-quality + coverage report.
"""
from __future__ import annotations

import ast
import json
import math
import re

import pandas as pd

RAW = "coursera_raw.csv"
OUT_CSV = "coursera_clean.csv"
OUT_JSON = "coursera_clean.json"

# --- role vocabularies (aligned with the roadmap ladder's 8 roles) ----------
# Multi-word / >=3 char keywords matched on word boundaries against the course
# blob (title + skills + description head). Overlap across roles is expected.
ROLE_KEYWORDS: dict[str, list[str]] = {
    "backend": [
        "backend", "back-end", "back end", "rest api", "restful", "api design",
        "django", "flask", "fastapi", "spring boot", "node.js", "nodejs",
        "express", "microservice", "server-side", "postgresql", "mysql",
        "mongodb", "sql", "database design", "graphql", "redis", "java", "golang",
    ],
    "frontend": [
        "frontend", "front-end", "front end", "html", "css", "javascript",
        "typescript", "react", "angular", "vue", "svelte", "redux", "tailwind",
        "responsive web", "web design", "dom ", "next.js", "frontend development",
    ],
    "fullstack": [
        "full stack", "full-stack", "fullstack", "mern", "mean stack",
        "web application development", "end-to-end web",
    ],
    "data_science": [
        "data science", "data scientist", "data analysis", "data analytics",
        "pandas", "numpy", "statistics", "statistical", "tableau", "power bi",
        "data visualization", "exploratory data", "r programming", "business analytics",
        "data wrangling", "regression analysis",
    ],
    "machine_learning_engineer": [
        "machine learning", "deep learning", "neural network", "tensorflow",
        "pytorch", "scikit-learn", "keras", "natural language processing",
        "computer vision", "reinforcement learning", "mlops", "generative ai",
        "large language model", "feature engineering",
    ],
    "devops": [
        "devops", "ci/cd", "continuous integration", "jenkins", "docker",
        "kubernetes", "terraform", "ansible", "cloud computing", "aws",
        "amazon web services", "microsoft azure", "google cloud", "linux",
        "infrastructure as code", "site reliability", "containerization",
    ],
    "android": [
        "android", "kotlin", "jetpack compose", "mobile app development",
        "mobile development", "flutter", "react native", "ios development",
        "swift programming",
    ],
    "ui_ux_designer": [
        "ux design", "ui design", "user experience", "user interface",
        "figma", "design thinking", "wireframe", "prototyping", "usability",
        "interaction design", "adobe xd", "user research", "ux/ui",
    ],
}

LEVEL_MAP = {
    "beginner level": "beginner",
    "intermediate level": "intermediate",
    "advanced level": "advanced",
    "mixed level": "all_levels",
    "beginner": "beginner",
    "intermediate": "intermediate",
    "advanced": "advanced",
}

# Cut the verbose module-by-module text off the description blurb.
_MODULE_MARKER = re.compile(
    r"(Applied Learning Project|\b\d+\s+(videos|readings|assignments|modules|"
    r"quizzes|peer reviews|discussion prompts)\b|Week\s+\d+:|Module\s+\d+)",
    re.IGNORECASE,
)


def parse_skills(raw: object) -> list[str]:
    if not isinstance(raw, str) or len(raw.strip()) < 3:
        return []
    try:
        items = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(items, (list, tuple)):
        return []
    seen, out = set(), []
    for item in items:
        s = re.sub(r"\s+", " ", str(item).strip())
        key = s.lower()
        # Drop malformed source extractions that are sentences, not skills
        # (e.g. "declare and initialize different types of variables").
        if not s or key in seen:
            continue
        if len(s) > 40 or len(s.split()) > 5 or s.endswith("."):
            continue
        seen.add(key)
        out.append(s)
    return out


def norm_level(raw: object) -> str | None:
    return LEVEL_MAP.get(str(raw or "").strip().lower())


def parse_float(raw: object) -> float | None:
    text = str(raw or "").strip()
    if not text or "not found" in text.lower():
        return None
    try:
        v = float(text.replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None
    return None if math.isnan(v) else v


def parse_int(raw: object) -> int | None:
    m = re.search(r"[\d,]+", str(raw or ""))
    if not m:
        return None
    try:
        return int(m.group(0).replace(",", ""))
    except ValueError:
        return None


def short_description(raw: object) -> str:
    text = re.sub(r"\s+", " ", str(raw or "").strip())
    if not text:
        return ""
    m = _MODULE_MARKER.search(text)
    if m and m.start() > 80:
        text = text[: m.start()].strip()
    return text[:600].rsplit(" ", 1)[0].strip() if len(text) > 600 else text


def tag_roles(blob: str) -> list[str]:
    roles = []
    for role, keywords in ROLE_KEYWORDS.items():
        for kw in keywords:
            # word-boundary-ish: keyword surrounded by non-alnum or string edge
            if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", blob):
                roles.append(role)
                break
    return roles


def main() -> None:
    df = pd.read_csv(RAW)
    raw_n = len(df)

    df = df.dropna(subset=["title", "URL"])
    df = df[df["URL"].str.contains("coursera.org", na=False)]
    df = df.drop_duplicates(subset=["URL"])
    after_basic = len(df)

    records = []
    for _, row in df.iterrows():
        skills = parse_skills(row.get("Skills"))
        desc = short_description(row.get("Description"))
        title = re.sub(r"\s+", " ", str(row.get("title") or "").strip())
        # Tag roles from the CURATED signals only (title + skills), NOT the noisy
        # description — description matching produced false positives like
        # "Nuclear fuel management" -> backend (its text mentions ETL/data structures).
        role_blob = " ".join([title, " ".join(skills)]).lower()
        roles = tag_roles(role_blob)
        if not roles:
            continue  # drop non-career / off-topic courses
        records.append(
            {
                "title": title,
                "url": str(row.get("URL")).strip(),
                "organization": str(row.get("Organization") or "").strip() or None,
                "instructor": str(row.get("Instructor") or "").strip() or None,
                "level": norm_level(row.get("Level")),
                "skills": skills,
                "description": desc,
                "rating": parse_float(row.get("rating")),
                "num_reviews": parse_int(row.get("num_reviews")),
                "enrolled": parse_int(row.get("enrolled")),
                "satisfaction_rate": parse_float(row.get("Satisfaction Rate")),
                "roles": roles,
                "provider": "Coursera",
            }
        )

    clean = pd.DataFrame(records)
    clean.to_csv(OUT_CSV, index=False)
    with open(OUT_JSON, "w") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=1)

    # ---------------- report ----------------
    print("=" * 64)
    print("COURSERA CAREER-COURSE CATALOG — CLEANING REPORT")
    print("=" * 64)
    print(f"raw rows ................. {raw_n}")
    print(f"valid (title+coursera url, deduped) .. {after_basic}")
    print(f"career-relevant (>=1 role tag) ....... {len(clean)}")
    print()
    print("Per-role coverage (a course can map to several roles):")
    role_counts = {r: int(clean['roles'].apply(lambda rs: r in rs).sum()) for r in ROLE_KEYWORDS}
    for r, c in sorted(role_counts.items(), key=lambda x: -x[1]):
        print(f"   {r:30} {c}")
    print()
    print("Level distribution:")
    print("   " + str(clean["level"].value_counts(dropna=False).to_dict()))
    print()
    print(f"with parsed rating ....... {clean['rating'].notna().sum()} "
          f"({clean['rating'].notna().mean()*100:.0f}%)")
    print(f"with skills (>=1) ........ {(clean['skills'].apply(len) > 0).sum()} "
          f"({(clean['skills'].apply(len) > 0).mean()*100:.0f}%)")
    print(f"with enrollment .......... {clean['enrolled'].notna().sum()}")
    print(f"avg rating (where present) {clean['rating'].dropna().mean():.2f}")
    print()
    from collections import Counter
    skill_counter = Counter(s.lower() for row in records for s in row["skills"])
    print("Top 15 skills:")
    for s, c in skill_counter.most_common(15):
        print(f"   {s:32} {c}")
    print()
    print("Sample backend courses:")
    sample = clean[clean["roles"].apply(lambda rs: "backend" in rs)].head(4)
    for _, r in sample.iterrows():
        print(f"   [{r['level']}] {r['title'][:54]:56} ⭐{r['rating']}  {r['url'][:48]}")
    print("=" * 64)
    print(f"WROTE: {OUT_CSV}  +  {OUT_JSON}")


if __name__ == "__main__":
    main()
