"""Tests for the career_tools app: ATS scoring, resume document generation, and portfolio publishing."""

import io
from decimal import Decimal

import pytest
from rest_framework import status

from apps.career_tools.models import Portfolio, Resume
from apps.career_tools.services import PortfolioService, ResumeService

try:
    from reportlab.pdfgen import canvas
except ImportError:  # pragma: no cover
    canvas = None


BASE = "/api/v1/career-tools"

SAMPLE_CV_TEXT = """
Mohamed Wes
mohamed@example.com
+201012345678

Summary
Backend engineer with Django and PostgreSQL experience.

Experience
Backend Developer at Acme Corp (2022–2024)
Built REST APIs serving 10k requests/day.

Education
BSc Computer Science, Cairo University

Skills
Python, Django, PostgreSQL, React
"""


def _make_pdf_bytes(text: str) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(72, 800, text[:80])
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def _complete_resume(user) -> Resume:
    return ResumeService.create_resume(
        user=user,
        title="Backend Engineer Resume",
        personal_info={
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+201000000000",
            "summary": "Backend engineer with Django and PostgreSQL experience.",
        },
        work_experience={"items": [
            {"company": "Acme", "role": "Backend Dev", "achievements": "Cut latency by 40%."}
        ]},
        education={"items": [{"institution": "Cairo University", "degree": "BSc CS"}]},
        skills={"items": ["Python", "Django", "PostgreSQL"]},
        projects={"items": [{"title": "Payments API"}]},
    )


# --- ATS scoring (service) --------------------------------------------------


@pytest.mark.django_db
def test_compute_ats_score_rewards_complete_resume(user):
    resume = _complete_resume(user)
    score, suggestions = ResumeService.compute_ats_score(resume)
    assert score >= Decimal("90")
    assert suggestions == []


@pytest.mark.django_db
def test_compute_ats_score_flags_sparse_resume(user):
    resume = ResumeService.create_resume(user=user, title="Empty Resume")
    score, suggestions = ResumeService.compute_ats_score(resume)
    assert score < Decimal("40")
    assert any("contact" in s.lower() for s in suggestions)
    assert any("work experience" in s.lower() for s in suggestions)


@pytest.mark.django_db
def test_compute_ats_score_is_deterministic(user):
    resume = _complete_resume(user)
    first, _ = ResumeService.compute_ats_score(resume)
    second, _ = ResumeService.compute_ats_score(resume)
    assert first == second


# --- Resume action endpoints ------------------------------------------------


@pytest.mark.django_db
def test_optimize_ats_endpoint_returns_real_score(authenticated_client, user):
    resume = _complete_resume(user)
    response = authenticated_client.post(f"{BASE}/resumes/{resume.id}/optimize_ats/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["ats_score"] >= 90
    assert "ats_grade" in response.data
    resume.refresh_from_db()
    assert resume.is_ats_optimized is True
    assert resume.ats_processing_status == "completed"


@pytest.mark.django_db
def test_generate_returns_structured_document_not_501(authenticated_client, user):
    resume = _complete_resume(user)
    response = authenticated_client.post(f"{BASE}/resumes/{resume.id}/generate/?file_format=pdf")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["export_format"] == "pdf"
    assert response.data["export_available"] is False
    section_keys = {section["key"] for section in response.data["document"]["sections"]}
    assert {"personal_info", "work_experience", "skills"} <= section_keys


@pytest.mark.django_db
def test_generate_rejects_invalid_format(authenticated_client, user):
    resume = _complete_resume(user)
    response = authenticated_client.post(f"{BASE}/resumes/{resume.id}/generate/?file_format=txt")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_resume_endpoint_assigns_user(authenticated_client, user):
    response = authenticated_client.post(
        f"{BASE}/resumes/", {"title": "API Created Resume"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "API Created Resume"
    resume = Resume.objects.get(id=response.data["id"])
    assert resume.user == user


@pytest.mark.django_db
def test_upload_resume_txt_populates_fields_and_scores(authenticated_client, user):
    upload = io.BytesIO(SAMPLE_CV_TEXT.encode("utf-8"))
    upload.name = "my-cv.txt"

    response = authenticated_client.post(
        f"{BASE}/resumes/upload/",
        {"file": upload},
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "my-cv"
    assert float(response.data["ats_score"]) > 0
    assert response.data["personal_info"]["email"] == "mohamed@example.com"

    resume = Resume.objects.get(id=response.data["id"])
    assert resume.user == user
    assert resume.is_ats_optimized is True


@pytest.mark.django_db
@pytest.mark.skipif(canvas is None, reason="reportlab not installed")
def test_upload_resume_pdf_extracts_text(authenticated_client, user):
    pdf_bytes = _make_pdf_bytes("mohamed@example.com Python Django")
    upload = io.BytesIO(pdf_bytes)
    upload.name = "cv.pdf"
    upload.size = len(pdf_bytes)

    response = authenticated_client.post(
        f"{BASE}/resumes/upload/",
        {"file": upload},
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    resume = Resume.objects.get(id=response.data["id"])
    assert resume.pdf_file.name.endswith(".pdf")


@pytest.mark.django_db
def test_upload_resume_rejects_unsupported_type(authenticated_client):
    upload = io.BytesIO(b"not a resume")
    upload.name = "cv.exe"

    response = authenticated_client.post(
        f"{BASE}/resumes/upload/",
        {"file": upload},
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported" in response.data["error"]


@pytest.mark.django_db
def test_resume_list_is_scoped_to_user(authenticated_client, user, another_user):
    mine = _complete_resume(user)
    ResumeService.create_resume(user=another_user, title="Someone else's resume")
    response = authenticated_client.get(f"{BASE}/resumes/")
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"] if isinstance(response.data, dict) else response.data
    returned_ids = {item["id"] for item in results}
    assert str(mine.id) in returned_ids
    assert len(returned_ids) == 1


# --- AI resume improvement -------------------------------------------------


class _StubGemmaResponse:
    def __init__(self, payload):
        self.payload = payload
        self.text = ""
        self.prompt_tokens = 10
        self.completion_tokens = 20


@pytest.mark.django_db
def test_improve_with_ai_returns_structured_fields(user, monkeypatch):
    resume = _complete_resume(user)

    def fake_generate_structured(self, **kwargs):
        return _StubGemmaResponse({
            "improved_summary": "Results-driven backend engineer who cut API latency by 40%.",
            "strengthened_bullets": ["Reduced p95 latency 40% by adding Redis caching."],
            "missing_keywords": ["CI/CD", "Kubernetes"],
            "recommendations": ["Add a metrics-driven summary."],
        })

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        fake_generate_structured,
    )

    result = ResumeService.improve_with_ai(resume)

    assert result["ai_used"] is True
    assert "latency" in result["improved_summary"]
    assert "CI/CD" in result["missing_keywords"]
    assert result["strengthened_bullets"]
    assert float(result["ats_score"]) >= 0


@pytest.mark.django_db
def test_improve_with_ai_falls_back_when_llm_fails(user, monkeypatch):
    resume = ResumeService.create_resume(user=user, title="Sparse Resume")

    def boom(self, **kwargs):
        from apps.core.exceptions import AIServiceError

        raise AIServiceError("provider unavailable", details={"reason": "timeout"})

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        boom,
    )

    result = ResumeService.improve_with_ai(resume)

    assert result["ai_used"] is False
    assert result["recommendations"]  # deterministic suggestions present


@pytest.mark.django_db
def test_improve_endpoint_returns_payload(authenticated_client, user, monkeypatch):
    resume = _complete_resume(user)

    monkeypatch.setattr(
        "apps.core.gemma_client.GemmaClient.generate_structured",
        lambda self, **kwargs: _StubGemmaResponse({
            "improved_summary": "Strong summary.",
            "strengthened_bullets": ["Bullet."],
            "missing_keywords": ["Docker"],
            "recommendations": ["Tip."],
        }),
    )

    response = authenticated_client.post(f"{BASE}/resumes/{resume.id}/improve/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["ai_used"] is True
    assert response.data["improved_summary"] == "Strong summary."


@pytest.mark.django_db
def test_improve_endpoint_scoped_to_owner(authenticated_client, another_user):
    others = ResumeService.create_resume(user=another_user, title="Not yours")
    response = authenticated_client.post(f"{BASE}/resumes/{others.id}/improve/")
    assert response.status_code == status.HTTP_404_NOT_FOUND


# --- Portfolio publish + public view (regression: was referencing .slug) ----


@pytest.mark.django_db
def test_create_portfolio_endpoint_assigns_user(authenticated_client, user):
    response = authenticated_client.post(
        f"{BASE}/portfolios/", {"title": "API Created Portfolio"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["title"] == "API Created Portfolio"
    portfolio = Portfolio.objects.get(id=response.data["id"])
    assert portfolio.user == user


@pytest.mark.django_db
def test_portfolio_publish_and_public_view(authenticated_client, api_client, user):
    portfolio = PortfolioService.create_portfolio(
        user=user, title="My Portfolio", custom_url_slug="test-user-portfolio"
    )

    publish = authenticated_client.post(f"{BASE}/portfolios/{portfolio.id}/publish/")
    assert publish.status_code == status.HTTP_200_OK
    assert publish.data["slug"] == "test-user-portfolio"
    assert publish.data["public_url"] == "/portfolio/test-user-portfolio"

    # Public view requires no authentication.
    public = api_client.get(f"{BASE}/portfolios/public/test-user-portfolio/")
    assert public.status_code == status.HTTP_200_OK
    assert public.data["title"] == "My Portfolio"

    portfolio.refresh_from_db()
    assert portfolio.is_public is True
    assert portfolio.view_count == 1
