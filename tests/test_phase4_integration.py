"""Phase 4 integration tests."""

import pytest
from src.agent.knowledge_api import KnowledgeAPI
from src.agent.context_injector import ContextInjector
from src.agent.task_delegate import TaskDelegate


class TestPhase4:
    """Test Phase 4 integration."""

    @pytest.fixture
    def api(self):
        return KnowledgeAPI()

    @pytest.fixture
    def injector(self, tmp_path):
        return ContextInjector(knowledge_root=tmp_path)

    @pytest.fixture
    def delegate(self, tmp_path):
        return TaskDelegate(knowledge_root=tmp_path)

    def test_knowledge_api_search(self, api):
        """Test KnowledgeAPI search."""
        results = api.search("测试", top_k=3)
        assert isinstance(results, list)

    def test_knowledge_api_answer(self, api):
        """Test KnowledgeAPI Q&A."""
        result = api.answer("测试问题")
        assert "answer" in result

    def test_context_injector(self, injector):
        """Test ContextInjector."""
        context = injector.get_context("测试")
        assert isinstance(context, str)

        path = injector.save_context("测试", context, "test")
        assert path is not None

        loaded = injector.load_context("test")
        assert loaded is not None

    def test_task_delegate_capabilities(self, delegate):
        """Test TaskDelegate capabilities."""
        caps = delegate.get_available_capabilities()
        assert len(caps) > 0

    def test_task_delegate_research(self, delegate):
        """Test TaskDelegate research."""
        result = delegate.research_topic("人工智能", depth=1)
        assert "topic" in result
        assert "answer" in result
