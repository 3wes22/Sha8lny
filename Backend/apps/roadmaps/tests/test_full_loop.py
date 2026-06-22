"""Deterministic full-loop integration test (Task 4.7).

Covers the core product chain on **deterministic fallbacks only** — no network,
no Gemini, no Chroma:

    assessment result
      -> roadmap structure (provenance, fallback-aware)
      -> courses (embedding match populated)
      -> jobs (skill-matched + ranked + explained)
      -> advisory (citation contract + grounded no-context)

This is the offline demo path; every external boundary is forced to its
deterministic fallback so the loop survives a dead GEMINI_API_KEY.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.assessments.models import Assessment, AssessmentResult
from apps.advisory.llm_service import LLMAdvisoryService
from apps.courses.course_index import CourseIndex
from apps.courses.models import Course, CoursePlatform
from apps.jobs.models import Job, JobPlatform, JobSkill
from apps.jobs.services import JobService
from apps.roadmaps.assembler import RoadmapAssembler
from apps.roadmaps.models import Roadmap, RoadmapMilestone, RoadmapPhase
from apps.roadmaps.services import RoadmapService
from apps.users.models import Skill, User, UserSkill


@pytest.fixture
def loop_user(db):
    return User.objects.create_user(
        auth0_id="full_loop_auth0",
        email="full-loop@example.com",
        username="full_loop_user",
        full_name="Full Loop User",
        date_of_birth="1997-01-01",
    )


@pytest.mark.django_db
def test_full_loop_runs_on_deterministic_fallbacks(loop_user):
    # --- assessment -----------------------------------------------------
    assessment = Assessment.objects.create(
        user=loop_user,
        assessment_type="skills",
        target_career="Backend Developer",
        questions=[],
        total_questions=0,
        status="completed",
        ai_processing_status="completed",
    )
    result = AssessmentResult.objects.create(
        assessment=assessment,
        overall_score=72,
        skill_scores={"python": 80},
        strengths=["Python"],
        areas_for_improvement=["System design"],
        recommended_careers=[{"title": "Backend Developer", "match_score": 88}],
        recommended_learning_paths=[],
        ai_insights="Solid fundamentals",
        llm_model_used="mock-v1",
        ai_confidence_score=0.8,
    )

    # --- roadmap structure (deterministic fallback provenance) ----------
    with patch(
        "apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks",
        return_value=[],
    ):
        phases, provenance = RoadmapAssembler.assemble(
            user=loop_user,
            target_career=result.assessment.target_career,
            assessment_result=result,
            current_level="beginner",
            weekly_hours=10,
            priority_skills=["Python"],
            gaps=["System design"],
            strengths=["Python"],
            top_skills=["Python"],
        )
    assert provenance.fallback_used is True
    assert provenance.structure_license_tier == "internal"
    assert len(phases) >= 1

    # Persist a roadmap with a course milestone derived from the assessment.
    roadmap = Roadmap.objects.create(
        user=loop_user,
        title="Backend roadmap",
        target_career=result.assessment.target_career,
        current_level="beginner",
        target_level="job-ready",
        estimated_duration_weeks=12,
        status=Roadmap.DRAFT,
    )
    phase = RoadmapPhase.objects.create(
        roadmap=roadmap,
        title="Foundations",
        description="Core backend",
        order=1,
        estimated_duration_weeks=4,
    )
    milestone = RoadmapMilestone.objects.create(
        phase=phase,
        title="Strengthen Python for backend",
        description="Practice",
        milestone_type=RoadmapMilestone.COURSE,
        order=1,
        estimated_duration_hours=Decimal("10.00"),
        skills=["Python"],
    )

    # --- courses (embedding match populated) ----------------------------
    course_platform = CoursePlatform.objects.create(
        name="Loop Platform",
        slug="loop-platform",
        website_url="https://courses.example.com",
        integration_type=CoursePlatform.MANUAL,
    )
    course = Course.objects.create(
        platform=course_platform,
        external_id="loop-c1",
        title="Python for Backend",
        slug="python-for-backend",
        description="APIs and data",
        url="https://courses.example.com/loop-c1",
        is_published=True,
    )
    with patch.object(
        CourseIndex,
        "search",
        return_value=[{"course_id": str(course.id), "title": course.title, "score": 0.9}],
    ):
        RoadmapService.match_courses_for_roadmap(roadmap)
    milestone.refresh_from_db()
    assert milestone.courses.exists()
    assert milestone.courses.first().match_score > Decimal("0")

    # --- jobs (skill-matched + ranked + explained) ----------------------
    python_skill = Skill.objects.create(name="Python", slug="python", category="technical")
    UserSkill.objects.create(user=loop_user, skill=python_skill, proficiency_level="intermediate")
    job_platform = JobPlatform.objects.create(
        name="Loop Jobs",
        slug="loop-jobs",
        website_url="https://jobs.example.com",
        is_active=True,
        scraping_enabled=True,
        target_countries=["Egypt"],
    )
    from django.utils import timezone

    job = Job.objects.create(
        platform=job_platform,
        external_id="loop-backend-1",
        external_url="https://jobs.example.com/loop-backend-1",
        title="Backend Developer",
        company_name="Loop Co",
        description="Build backends",
        requirements="Python",
        location_city="Cairo",
        location_country="Egypt",
        job_type="full_time",
        experience_level="mid",
        salary_currency="EGP",
        salary_period="monthly",
        posted_date=timezone.now().date(),
        is_active=True,
    )
    JobSkill.objects.create(job=job, skill=python_skill, is_required=True)

    matches = JobService.match_jobs_for_user(loop_user, limit=5)
    assert len(matches) >= 1
    top = matches[0]
    assert "Python" in top["matching_skills"]
    assert "top_factors" in top["explanation"]

    # --- advisory (citation contract + grounded no-context) -------------
    service = LLMAdvisoryService()
    with patch("apps.advisory.llm_service.get_rag_runtime", return_value=None):
        _response, _delay, metadata = service.generate_response(
            "What should I learn next for a backend job?",
            conversation_history=[],
            user_context={"skills": ["Python"]},
        )
    # Citation contract is attached on every path, even the deterministic fallback.
    assert "retrieved_documents" in metadata
    assert metadata["retrieved_documents"] == []
    assert "no_retrieval_context" in metadata
