"""RAG-based question answering service."""

from .embedder import Embedder
from .vector_store import VectorStore
from ..utils.model_router import get_router


class RAGQA:
    """Question answering using Retrieval Augmented Generation."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        model: str = "qwen3.5-plus"
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.router = get_router()
        self.model = model

    def answer(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True
    ) -> dict:
        """Answer a question using retrieved context.

        Args:
            question: The question to answer
            top_k: Number of documents to retrieve
            include_sources: Whether to include source references

        Returns:
            Dictionary with answer and optionally sources
        """
        # Retrieve relevant context
        query_embedding = self.embedder.embed(question)
        results = self.vector_store.search(query_embedding, top_k)

        if not results:
            return {
                "answer": "抱歉，没有找到相关的知识内容。",
                "sources": []
            }

        # Build context from retrieved documents
        context_parts = []
        sources = []

        for i, r in enumerate(results, 1):
            context_parts.append(f"[资料{i}] {r.get('content_preview', '')[:500]}")
            sources.append({
                "title": r.get("title", "Unknown"),
                "file_path": r.get("file_path", ""),
                "score": 1 / (1 + r.get("distance", 1.0))
            })

        context = "\n\n".join(context_parts)

        # Generate answer using LLM
        prompt = f"""请基于以下资料回答问题。如果资料中没有相关信息，请说明。

资料：
{context}

问题：{question}

请用中文回答，确保答案准确且完整。"""

        answer = self.router.call(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )

        result = {"answer": answer}

        if include_sources:
            result["sources"] = sources

        return result
