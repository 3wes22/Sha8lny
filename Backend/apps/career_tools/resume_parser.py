"""
Heuristic CV text extraction and parsing for ATS scoring.

Uses pypdf / python-docx (already in requirements) to read uploaded files,
then maps plain text into the JSON sections ResumeService expects.
"""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import PurePath
from typing import Any, Dict, List, Tuple

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+", re.IGNORECASE)
PHONE_RE = re.compile(r"\+?\d[\d\s\-().]{8,}\d")

SECTION_HEADINGS: Dict[str, Tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "objective", "about"),
    "work_experience": (
        "experience",
        "work experience",
        "employment",
        "professional experience",
        "work history",
    ),
    "education": ("education", "academic background", "qualifications"),
    "skills": ("skills", "technical skills", "core competencies", "technologies"),
    "projects": ("projects", "personal projects", "selected projects"),
    "certifications": ("certifications", "licenses", "certificates"),
    "languages": ("languages", "language skills"),
}

SKILL_KEYWORDS = [
    "Python",
    "Django",
    "JavaScript",
    "TypeScript",
    "React",
    "Node.js",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "Git",
    "Linux",
    "Java",
    "C++",
    "C#",
    "Go",
    "Rust",
    "FastAPI",
    "Flask",
    "REST",
    "GraphQL",
    "HTML",
    "CSS",
    "Tailwind",
    "Vue",
    "Angular",
    "Machine Learning",
    "TensorFlow",
    "PyTorch",
    "Agile",
    "Scrum",
    "CI/CD",
    "Terraform",
    "Ansible",
    "Nginx",
    "Kafka",
    "Spark",
    "Pandas",
    "NumPy",
    "Excel",
    "Power BI",
    "Tableau",
    "Figma",
    "Photoshop",
    "Communication",
    "Leadership",
    "Problem Solving",
]


def validate_upload(filename: str, size: int) -> str:
    """Return normalized extension or raise ValueError."""
    ext = PurePath(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext or 'unknown'}'. Use PDF, DOCX, or TXT."
        )
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("File exceeds the 5 MB upload limit.")
    return ext


def extract_text(file_obj, filename: str) -> str:
    """Extract plain text from an uploaded CV file."""
    size = getattr(file_obj, "size", None)
    if size is None:
        pos = file_obj.tell()
        file_obj.seek(0, 2)
        size = file_obj.tell()
        file_obj.seek(pos)

    ext = validate_upload(filename, size)
    file_obj.seek(0)

    if ext == ".txt":
        raw = file_obj.read()
        if isinstance(raw, str):
            return raw
        return raw.decode("utf-8", errors="replace")

    if ext == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(file_obj.read()))
        parts: List[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)

    if ext == ".docx":
        from docx import Document

        document = Document(BytesIO(file_obj.read()))
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())

    raise ValueError(f"Unsupported file type: {ext}")


def _normalize_lines(text: str) -> List[str]:
    lines = [line.strip() for line in text.replace("\r\n", "\n").split("\n")]
    return [line for line in lines if line]


def _is_heading(line: str) -> str | None:
    lowered = line.lower().strip(":").strip()
    for section_key, labels in SECTION_HEADINGS.items():
        if lowered in labels or any(lowered.startswith(label) for label in labels):
            return section_key
    return None


def _split_sections(lines: List[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {}
    current_key = "preamble"
    sections[current_key] = []

    for line in lines:
        heading = _is_heading(line)
        if heading:
            current_key = heading
            sections.setdefault(current_key, [])
            continue
        sections.setdefault(current_key, []).append(line)

    return sections


def _extract_contact(lines: List[str]) -> Dict[str, str]:
    personal: Dict[str, str] = {}
    joined = "\n".join(lines[:20])

    email_match = EMAIL_RE.search(joined)
    if email_match:
        personal["email"] = email_match.group(0)

    phone_match = PHONE_RE.search(joined)
    if phone_match:
        personal["phone"] = phone_match.group(0).strip()

    for line in lines[:8]:
        if EMAIL_RE.search(line) or PHONE_RE.search(line):
            continue
        if len(line.split()) >= 2 and len(line) <= 80 and not _is_heading(line):
            personal.setdefault("name", line)
            break

    summary_lines = []
    in_summary = False
    for line in lines:
        heading = _is_heading(line)
        if heading == "summary":
            in_summary = True
            continue
        if in_summary:
            if heading:
                break
            summary_lines.append(line)

    if summary_lines:
        personal["summary"] = " ".join(summary_lines[:6])
    elif len(lines) > 3:
        candidate = lines[2] if len(lines) > 2 else ""
        if candidate and not EMAIL_RE.search(candidate) and not PHONE_RE.search(candidate):
            if len(candidate.split()) >= 4:
                personal.setdefault("summary", candidate)

    return personal


def _lines_to_items(lines: List[str]) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    buffer: List[str] = []

    def flush() -> None:
        if not buffer:
            return
        text = " ".join(buffer).strip()
        if text:
            items.append({"text": text})
        buffer.clear()

    for line in lines:
        if line.startswith(("-", "•", "*")):
            flush()
            items.append({"text": line.lstrip("-•* ").strip()})
        elif re.match(r"^\d{4}", line) or " at " in line.lower():
            flush()
            items.append({"text": line})
        else:
            buffer.append(line)
    flush()
    return items


def _extract_skills(lines: List[str], full_text: str) -> List[str]:
    found: List[str] = []
    section_text = " ".join(lines).lower() if lines else ""

    for keyword in SKILL_KEYWORDS:
        key_lower = keyword.lower()
        if key_lower in section_text or key_lower in full_text.lower():
            if keyword not in found:
                found.append(keyword)

    if lines and not found:
        for part in re.split(r"[,;|/•\n]", " ".join(lines)):
            token = part.strip()
            if 2 <= len(token) <= 40 and token not in found:
                found.append(token)

    return found[:30]


def parse_resume_text(text: str) -> Dict[str, Any]:
    """Map raw CV text into resume JSON sections."""
    lines = _normalize_lines(text)
    sections = _split_sections(lines)
    personal_info = _extract_contact(lines)

    work_lines = sections.get("work_experience", [])
    education_lines = sections.get("education", [])
    skills_lines = sections.get("skills", [])
    project_lines = sections.get("projects", [])
    cert_lines = sections.get("certifications", [])
    language_lines = sections.get("languages", [])

    skills = _extract_skills(skills_lines, text)

    return {
        "personal_info": personal_info,
        "work_experience": {"items": _lines_to_items(work_lines)},
        "education": {"items": _lines_to_items(education_lines)},
        "skills": {"items": skills},
        "projects": {"items": _lines_to_items(project_lines)},
        "certifications": {"items": _lines_to_items(cert_lines)},
        "languages": {"items": _lines_to_items(language_lines)},
    }
