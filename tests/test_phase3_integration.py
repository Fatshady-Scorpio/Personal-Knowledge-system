"""Phase 3 integration tests."""

import pytest
from pathlib import Path
from src.retriever.embedder import Embedder
from src.retriever.vector_store import VectorStore
from src.retriever.semantic_search import SemanticSearch
from src.retriever.rag_qa import RAGQA
from src.utils.config import get_config


class TestPhase3:
    """Test Phase 3 functionality."""

    @pytest.fixture
    def embedder(self):
        config = get_config()
        return Embedder(api_key=config.bailian_api_key)

    @pytest.fixture
    def vector_store(self, tmp_path):
        return VectorStore(dimension=1536, index_path=tmp_path / "test_index")

    def test_embedder(self, embedder):
        """Test embedding generation."""
        result = embedder.embed("测试文本")
        assert len(result) > 0

    def test_vector_store(self, vector_store, embedder):
        """Test vector store operations."""
        embedding = embedder.embed("测试")
        vector_store.add([embedding], [{"title": "测试文档"}])
        assert vector_store.count == 1

    def test_semantic_search(self, embedder, vector_store, tmp_path):
        """Test semantic search."""
        # Add test documents
        embeddings = embedder.embed_batch(["人工智能介绍", "机器学习教程"])
        vector_store.add(embeddings, [
            {"title": "AI 介绍", "content_preview": "人工智能..."},
            {"title": "ML 教程", "content_preview": "机器学习..."}
        ])

        search = SemanticSearch(embedder, vector_store, tmp_path)
        results = search.search("AI 是什么", top_k=2)
        assert len(results) > 0

    def test_rag_qa(self, embedder, vector_store):
        """Test RAG question answering."""
        # Add test context
        embedding = embedder.embed("Python 是一种编程语言")
        vector_store.add([embedding], [{
            "title": "Python 介绍",
            "content_preview": "Python 是一种高级编程语言..."
        }])

        qa = RAGQA(embedder, vector_store)
        result = qa.answer("Python 是什么？")

        assert "answer" in result
