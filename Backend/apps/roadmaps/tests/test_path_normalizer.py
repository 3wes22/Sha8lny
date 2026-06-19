"""Tests for RoadmapPathNormalizer."""

import pytest

from apps.roadmaps.path_normalizer import RoadmapPathNormalizer


SAMPLE_CHUNKS = [
    {
        "content": (
            "## Pick a Language\n"
            "- Learn Python basics\n"
            "- Understand Git\n"
            "## Learn Framework\n"
            "1. Django fundamentals\n"
            "2. REST API design\n"
            "## Advanced Topics\n"
            "- Authentication patterns\n"
            "- Deployment basics\n"
            "- Testing with pytest\n"
        ),
        "source_url": "https://roadmap.sh/backend",
        "doc_id": "rm_backend_abc_0",
        "metadata": {"source": "roadmap.sh", "category": "backend"},
    }
]


@pytest.mark.django_db
class TestRoadmapPathNormalizer:
    def test_normalize_extracts_three_phases_from_chunks(self):
        phases = RoadmapPathNormalizer.normalize(SAMPLE_CHUNKS, "backend")

        assert len(phases) == 3
        assert phases[0].phase_number == 1
        assert len(phases[0].milestone_titles) >= 1
        assert phases[0].source_urls == ["https://roadmap.sh/backend"]
        assert "rm_backend_abc_0" in phases[0].source_doc_ids

    def test_normalize_empty_chunks_uses_fallback(self):
        phases = RoadmapPathNormalizer.normalize([], "backend")

        assert len(phases) == 3
        assert phases[0].title.startswith("Foundations")
