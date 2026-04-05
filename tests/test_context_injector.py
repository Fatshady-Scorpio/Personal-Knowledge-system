"""Tests for context injector."""

import pytest
from src.agent.context_injector import ContextInjector


class TestContextInjector:
    """Test ContextInjector class."""

    @pytest.fixture
    def injector(self, tmp_path):
        """Create ContextInjector instance."""
        return ContextInjector(knowledge_root=tmp_path)

    def test_get_context(self, injector):
        """Test getting context for query."""
        context = injector.get_context("测试查询", max_notes=3)
        assert isinstance(context, str)

    def test_save_and_load_context(self, injector):
        """Test saving and loading context."""
        context = "# Test Context\n\nSome content."
        path = injector.save_context("测试", context, "test_session")

        loaded = injector.load_context("test_session")
        assert loaded is not None
        assert "测试查询" in loaded or "Test Context" in loaded

    def test_clear_contexts(self, injector):
        """Test clearing contexts."""
        injector.save_context("测试 1", "Content 1", "test_session")
        injector.save_context("测试 2", "Content 2", "test_session")

        injector.clear_contexts("test_session")

        loaded = injector.load_context("test_session")
        assert loaded is None
