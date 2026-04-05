"""Tests for knowledge API."""

import pytest
from src.agent.knowledge_api import KnowledgeAPI
from src.utils.config import get_config


class TestKnowledgeAPI:
    """Test KnowledgeAPI class."""

    @pytest.fixture
    def api(self):
        """Create KnowledgeAPI instance."""
        return KnowledgeAPI()

    def test_search(self, api):
        """Test semantic search."""
        results = api.search("人工智能", top_k=3)
        assert isinstance(results, list)

    def test_answer(self, api):
        """Test RAG question answering."""
        result = api.answer("什么是机器学习？")
        assert "answer" in result

    def test_list_topics(self, api):
        """Test listing topics."""
        topics = api.list_topics()
        assert isinstance(topics, list)

    def test_get_note(self, api):
        """Test getting note by title."""
        # This may return None if no note exists yet
        note = api.get_note("Test")
        # Just verify it doesn't crash
        assert note is None or isinstance(note, dict)
