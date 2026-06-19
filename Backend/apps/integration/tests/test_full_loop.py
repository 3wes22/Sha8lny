"""Integration tests for the assessment → roadmap → advisory loop."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.assessments.models import Assessment, AssessmentResult
from apps.roadmaps.models import Roadmap
from apps.roadmaps.services import RoadmapService
from apps.users.models import User


@pytest.mark.django_db
class TestFullDemoLoop:
    @patch("apps.advisory.llm_service.GemmaClient")
    @patch("apps.roadmaps.ai_pipeline.GemmaClient")
    @patch("apps.assessments.ai_pipeline.GemmaClient")
    def test_assessment_to_roadmap_to_advisory_chain(
        self,
        mock_assessment_client,
        mock_roadmap_client,
        mock_advisory_client,
        user,
    ):
        assessment_client = MagicMock()
        assessment_client.generate_structured.return_value = MagicMock(
            payload={
                "questions": [
                    {
                        "subskill_key": "python_basics",
                        "competency": "Python",
                        "learning_objective": "Validate syntax knowledge",
                        "scenario_context": "A service fails on import.",
                        "stem": "Which fix resolves the import error?",
                        "question_type": "single_choice",
                        "difficulty": 2,
                        "estimated_seconds": 45,
                        "options": [
                            {"key": "A", "text": "Fix PYTHONPATH"},
                            {"key": "B", "text": "Ignore tests"},
                            {"key": "C", "text": "Delete logs"},
                            {"key": "D", "text": "Disable auth"},
                        ],
                        "answer_key": {"selected": "A"},
                        "explanation": "PYTHONPATH resolves module lookup.",
                        "correct_answer_rationale": "Import paths must be valid.",
                        "option_rationales": [],
                    }
                ]
            },
            metadata=MagicMock(
                processing_time_ms=120,
                model="gemini-2.5-flash-lite",
                provider="gemini",
                trace_id="trace-assessment",
                fallback_used=False,
            ),
            prompt_tokens=100,
            completion_tokens=80,
        )
        mock_assessment_client.return_value = assessment_client

        roadmap_client = MagicMock()
        roadmap_client.generate_structured.return_value = MagicMock(
            payload={
                "roadmap_summary": "Personalized backend roadmap",
                "phases": [],
            },
            metadata=MagicMock(
                processing_time_ms=90,
                model="gemini-2.5-flash-lite",
                provider="gemini",
                trace_id="trace-roadmap",
                fallback_used=False,
            ),
            prompt_tokens=50,
            completion_tokens=40,
        )
        mock_roadmap_client.return_value = roadmap_client

        advisory_client = MagicMock()
        advisory_client.generate_text.return_value = MagicMock(
            text="Focus on strengthening SQL and API design next.",
            metadata=MagicMock(
                processing_time_ms=70,
                model="gemini-2.5-flash",
                provider="gemini",
                trace_id="trace-advisory",
                fallback_used=False,
            ),
            prompt_tokens=30,
            completion_tokens=20,
        )
        mock_advisory_client.return_value = advisory_client

        assessment = Assessment.objects.create(
            user=user,
            assessment_type="skills",
            target_career="Backend Developer",
            stage="completed",
            status="completed",
            ai_processing_status="completed",
        )
        result = AssessmentResult.objects.create(
            assessment=assessment,
            overall_score=Decimal("78.00"),
            skill_scores={"python": 70},
            strengths=["Python"],
            areas_for_improvement=["SQL"],
            recommended_careers=[{"title": "Backend Developer", "match_score": 88, "reasoning": "Strong fit"}],
            recommended_learning_paths=[{"skill": "SQL", "priority": "high", "resources": []}],
            roadmap_signal={
                "role": "backend_developer",
                "subskill_gaps": [{"subskill_key": "sql_queries", "gap": 2}],
                "priority_order": ["SQL"],
            },
            ai_insights="Solid backend baseline.",
            llm_model_used="test-model",
        )

        roadmap = RoadmapService.create_ai_roadmap_shell(
            user=user,
            assessment=result,
            target_career="Backend Developer",
            current_level="intermediate",
            target_level="job-ready",
        )
        populated = RoadmapService.populate_ai_roadmap(roadmap)
        assert populated.ai_processing_status == "completed"
        assert populated.phases.exists()

        from apps.advisory.llm_service import LLMAdvisoryService

        service = LLMAdvisoryService()
        with patch(
            "apps.advisory.llm_service.get_rag_runtime"
        ) as mock_runtime:
            mock_runtime.return_value = {
                "classify_message": lambda message: ("in_scope", ""),
                "get_redirect_response": lambda message: "redirect",
                "get_clarifying_question": lambda: "clarify",
                "system_prompt": "test",
                "retrieve_context": lambda message, top_k=4: [
                    {
                        "content": "Backend roles in Egypt emphasize Python and SQL.",
                        "metadata": {"category": "market", "topic": "backend"},
                        "score": 0.8,
                    }
                ],
            }
            response_text, _, metadata = service.generate_response(
                "What should I focus on next for a backend role?",
                user_context=service.build_user_context(user),
            )

        assert "SQL" in response_text or "backend" in response_text.lower()
        assert metadata["source"] == "llm"
