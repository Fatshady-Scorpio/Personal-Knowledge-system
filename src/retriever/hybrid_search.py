"""Hybrid search combining BM25 and semantic search."""

from pathlib import Path
from .bm25_search import BM25Search
from .local_embedder import LocalEmbedder
from .vector_store import VectorStore
import numpy as np


class HybridSearch:
    """Hybrid search combining keyword and semantic search."""

    def __init__(
        self,
        knowledge_root: str | Path,
        use_semantic: bool = True,
        bm25_weight: float = 0.5,
        semantic_weight: float = 0.5
    ):
        self.knowledge_root = Path(knowledge_root)
        self.use_semantic = use_semantic
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight

        # Initialize BM25
        self.bm25 = BM25Search(knowledge_root)

        # Initialize semantic search if enabled
        if use_semantic:
            self.embedder = LocalEmbedder()
            self.vector_store = VectorStore(
                dimension=1024,  # qwen2.5-coder embedding dim
                index_path=self.knowledge_root / ".local_index"
            )
        else:
            self.embedder = None
            self.vector_store = None

    def build_index(self, rebuild: bool = False) -> int:
        """Build both BM25 and semantic indexes.

        Returns:
            Number of documents indexed
        """
        # Build BM25 index
        count = self.bm25.build_index()

        # Build semantic index if enabled
        if self.use_semantic and self.embedder:
            if self.embedder.check_connection():
                # Re-embed all documents
                embeddings = self.embedder.embed_batch([
                    f"{d['title']}: {d['content'][:1000]}"
                    for d in self.bm25.documents
                ])
                self.vector_store.add(embeddings, self.bm25.documents)
                self.vector_store.save()
            else:
                print("Warning: Ollama not available, using BM25 only")
                self.use_semantic = False

        return count

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_hybrid: bool = True
    ) -> list[dict]:
        """Search using hybrid or single method.

        Args:
            query: Search query
            top_k: Number of results
            use_hybrid: Whether to use hybrid search

        Returns:
            List of results with combined scores
        """
        if not use_hybrid or not self.use_semantic:
            # BM25 only
            return self.bm25.search(query, top_k=top_k)

        # Get BM25 results
        bm25_results = self.bm25.search(query, top_k=top_k * 2)

        # Get semantic results
        query_embedding = self.embedder.embed(query)
        semantic_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        # Combine results
        return self._combine_results(bm25_results, semantic_results, top_k)

    def _combine_results(
        self,
        bm25_results: list[dict],
        semantic_results: list[dict],
        top_k: int
    ) -> list[dict]:
        """Combine BM25 and semantic results with reciprocal rank fusion."""
        # Build score maps
        bm25_scores = {r["file_path"]: r["score"] for r in bm25_results}
        semantic_scores = {r["file_path"]: 1 / (1 + r.get("distance", 1)) for r in semantic_results}

        # Get all unique files
        all_files = set(bm25_scores.keys()) | set(semantic_scores.keys())

        # Combine scores
        combined = []
        for file_path in all_files:
            bm25_score = bm25_scores.get(file_path, 0)
            semantic_score = semantic_scores.get(file_path, 0)

            # Normalize and combine
            combined_score = (
                self.bm25_weight * bm25_score +
                self.semantic_weight * semantic_score
            )

            # Find the document
            for r in bm25_results + semantic_results:
                if r["file_path"] == file_path:
                    doc = r.copy()
                    doc["combined_score"] = combined_score
                    doc["bm25_score"] = bm25_score
                    doc["semantic_score"] = semantic_score
                    combined.append(doc)
                    break

        # Sort by combined score
        combined.sort(key=lambda x: x["combined_score"], reverse=True)
        return combined[:top_k]
