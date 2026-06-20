"""Unit tests for CV text extraction and heuristic parsing."""

import io

import pytest

from apps.career_tools.resume_parser import (
    ALLOWED_EXTENSIONS,
    MAX_UPLOAD_BYTES,
    extract_text,
    parse_resume_text,
    validate_upload,
)


SAMPLE_CV = """
Mohamed Wes
mohamed@example.com
+201012345678

Summary
Backend engineer with Django and PostgreSQL experience building scalable APIs.

Experience
Backend Developer at Acme Corp (2022–2024)
Built REST APIs serving 10k requests/day and reduced latency by 40%.

Education
BSc Computer Science, Cairo University, 2022

Skills
Python, Django, PostgreSQL, React, Docker
"""


def test_parse_resume_text_extracts_contact_and_skills():
    parsed = parse_resume_text(SAMPLE_CV)

    assert parsed["personal_info"]["name"] == "Mohamed Wes"
    assert parsed["personal_info"]["email"] == "mohamed@example.com"
    assert "+201012345678" in parsed["personal_info"]["phone"]
    assert "Django" in parsed["personal_info"]["summary"]

    skills = parsed["skills"]["items"]
    assert "Python" in skills
    assert "Django" in skills

    work = parsed["work_experience"]["items"]
    assert len(work) >= 1
    assert any("Acme" in str(item) for item in work)

    education = parsed["education"]["items"]
    assert len(education) >= 1


def test_extract_text_from_plain_txt():
    file_obj = io.BytesIO(b"Hello CV")
    assert extract_text(file_obj, "resume.txt") == "Hello CV"


def test_validate_upload_rejects_bad_extension():
    with pytest.raises(ValueError, match="Unsupported"):
        validate_upload("resume.exe", 100)


def test_validate_upload_rejects_oversized_file():
    with pytest.raises(ValueError, match="5 MB"):
        validate_upload("resume.pdf", MAX_UPLOAD_BYTES + 1)


def test_allowed_extensions():
    assert ".pdf" in ALLOWED_EXTENSIONS
    assert ".docx" in ALLOWED_EXTENSIONS
    assert ".txt" in ALLOWED_EXTENSIONS
