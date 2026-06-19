"""Tests for RoadmapAssembler."""

from unittest.mock import patch

import pytest

from apps.roadmaps.assembler import RoadmapAssembler
from apps.users.models import User


RETRIEVED_CHUNKS = [
    {
        "content": "- Python basics\n- Git workflow\n- Django REST APIs\n- Authentication\n- Deployment\n- Testing",
        "source_url": "https://roadmap.sh/backend",
        "doc_id": "rm_backend_test_0",
        "metadata": {"source": "roadmap.sh", "category": "backend"},
    }
]


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        auth0_id="assembler_user",
        email="assembler@example.com",
        username="assembler",
        full_name="Assembler User",
        date_of_birth="1990-01-01",
    )


@pytest.mark.django_db
class TestRoadmapAssembler:
    @patch.object(RoadmapAssembler, "_gap_reorder_milestones", wraps=RoadmapAssembler._gap_reorder_milestones)
    @patch("apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks")
    def test_assemble_uses_retrieved_chunks(self, mock_retrieve, _mock_reorder, test_user):
        mock_retrieve.return_value = RETRIEVED_CHUNKS

        phases, provenance = RoadmapAssembler.assemble(
            user=test_user,
            target_career="Backend Developer",
            assessment_result=None,
            current_level="beginner",
            weekly_hours=10,
            priority_skills=["Python"],
            gaps=["Authentication"],
            strengths=["Git"],
            top_skills=["Python"],
        )

        assert provenance.structure_source == "roadmap.sh"
        assert provenance.fallback_used is False
        assert provenance.retrieval_chunk_count == 1
        assert "https://roadmap.sh/backend" in provenance.retrieved_urls
        assert len(phases) == 3
        mock_retrieve.assert_called_once()

    @patch("apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks")
    def test_assemble_falls_back_when_retrieval_empty(self, mock_retrieve, test_user):
        mock_retrieve.return_value = []

        phases, provenance = RoadmapAssembler.assemble(
            user=test_user,
            target_career="Backend Developer",
            assessment_result=None,
            current_level="beginner",
            weekly_hours=10,
            priority_skills=[],
            gaps=[],
            strengths=[],
            top_skills=[],
        )

        assert provenance.fallback_used is True
        assert provenance.structure_source == "deterministic_fallback"
        assert len(phases) == 3

    @patch("apps.roadmaps.assembler.RoadmapPathRetriever.retrieve_path_chunks")
    def test_backend_onet_mappings_attached(self, mock_retrieve, test_user):
        mock_retrieve.return_value = [
            {
                "content": "- Python programming\n- REST API design\n- Database modeling",
                "source_url": "https://roadmap.sh/backend",
                "doc_id": "doc-onet",
                "metadata": {"source": "roadmap.sh", "category": "backend"},
            }
        ]

        _, provenance = RoadmapAssembler.assemble(
            user=test_user,
            target_career="Backend Developer",
            assessment_result=None,
            current_level="beginner",
            weekly_hours=10,
            priority_skills=["Python"],
            gaps=[],
            strengths=[],
            top_skills=[],
        )

        assert any(item["onet_element_id"] == "2.B.3.e" for item in provenance.onet_mappings)
