"""Tests for RoadmapPathRetriever."""

from unittest.mock import MagicMock, patch

import pytest

from apps.roadmaps.path_retriever import RoadmapPathRetriever, roadmap_sh_url


@pytest.mark.django_db
class TestRoadmapPathRetriever:
    def setup_method(self):
        RoadmapPathRetriever.reset()

    def test_roadmap_sh_url(self):
        assert roadmap_sh_url("backend") == "https://roadmap.sh/backend"

    @patch.object(RoadmapPathRetriever, "_get_collection")
    @patch.object(RoadmapPathRetriever, "_get_embedder")
    def test_retrieve_path_chunks_returns_structured_results(self, mock_embedder, mock_collection):
        collection = MagicMock()
        collection.count.return_value = 10
        collection.query.return_value = {
            "documents": [["Learn Python", "Build REST APIs"]],
            "metadatas": [[{"source": "roadmap.sh", "category": "backend"}, {"source": "roadmap.sh", "category": "backend"}]],
            "ids": [["doc-1", "doc-2"]],
        }
        mock_collection.return_value = collection
        mock_embedder.return_value.encode.return_value.tolist.return_value = [[0.1, 0.2]]

        chunks = RoadmapPathRetriever.retrieve_path_chunks("backend", "Backend Developer")

        assert len(chunks) == 2
        assert chunks[0]["doc_id"] == "doc-1"
        assert chunks[0]["source_url"] == "https://roadmap.sh/backend"
        collection.query.assert_called_once()
        assert collection.query.call_args.kwargs["where"] == {"source": "roadmap.sh"}

    @patch.object(RoadmapPathRetriever, "_get_collection")
    def test_retrieve_path_chunks_returns_empty_when_collection_missing(self, mock_collection):
        mock_collection.return_value = None
        assert RoadmapPathRetriever.retrieve_path_chunks("backend", "Backend Developer") == []
