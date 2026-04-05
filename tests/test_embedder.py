"""Tests for embedder module."""

import pytest
from src.retriever.embedder import Embedder
from src.utils.config import get_config


class TestEmbedder:
    """Test Embedder class."""

    @pytest.fixture
    def embedder(self):
        """Create Embedder instance."""
        config = get_config()
        return Embedder(api_key=config.bailian_api_key)

    def test_embed_returns_list(self, embedder):
        """Test that embed returns a list of floats."""
        result = embedder.embed("这是一段测试文本")

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch(self, embedder):
        """Test batch embedding."""
        texts = ["文本一", "文本二", "文本三"]
        results = embedder.embed_batch(texts)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)
