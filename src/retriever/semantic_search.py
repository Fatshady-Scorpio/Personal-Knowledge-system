"""Semantic search service."""

from pathlib import Path
from .embedder import Embedder
from .vector_store import VectorStore


class SemanticSearch:
    """Semantic search over knowledge base."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        knowledge_root: str | Path
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.knowledge_root = Path(knowledge_root)

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> list[dict]:
        """Search for semantically similar content.

        Args:
            query: The search query
            top_k: Number of results
            min_score: Minimum similarity score (0-1)

        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.embed(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k * 2)

        # Filter by score and format
        filtered_results = []
        for r in results:
            # Convert distance to similarity score (lower distance = higher similarity)
            score = 1 / (1 + r.get("distance", 1.0))
            if score >= min_score:
                filtered_results.append({
                    "title": r.get("title", "Unknown"),
                    "content_preview": r.get("content_preview", "")[:200],
                    "file_path": r.get("file_path", ""),
                    "category": r.get("category", ""),
                    "tags": r.get("tags", []),
                    "score": round(score, 3)
                })

        return filtered_results[:top_k]

    def build_index(self, rebuild: bool = False) -> int:
        """Build index from existing knowledge base.

        Args:
            rebuild: If True, rebuild index from scratch

        Returns:
            Number of documents indexed
        """
        if rebuild:
            self.vector_store = VectorStore(
                dimension=1536,
                index_path=self.vector_store.index_path
            )

        # Scan knowledge base for markdown files
        documents = []
        for md_file in self.knowledge_root.rglob("*.md"):
            if "20-Processed" in str(md_file):  # Only index processed files
                content = md_file.read_text(encoding="utf-8")
                documents.append({
                    "title": md_file.stem,
                    "content": content,
                    "content_preview": content[:500],
                    "file_path": str(md_file),
                    "category": md_file.parent.name
                })

        if not documents:
            return 0

        # Generate embeddings
        texts = [f"{d['title']}: {d['content'][:1000]}" for d in documents]
        embeddings = self.embedder.embed_batch(texts)

        # Add to vector store
        self.vector_store.add(embeddings, documents)
        self.vector_store.save()

        return len(documents)
