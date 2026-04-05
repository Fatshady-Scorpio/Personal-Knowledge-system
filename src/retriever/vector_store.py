"""Vector store using FAISS for efficient similarity search."""

import faiss
import numpy as np
import json
from pathlib import Path
from typing import Optional


class VectorStore:
    """FAISS-based vector store for semantic search."""

    def __init__(self, dimension: int = 1536, index_path: str | Path | None = None):
        """Initialize vector store.

        Args:
            dimension: Embedding dimension (1536 for text-embedding-v2)
            index_path: Path to save/load index
        """
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: list[dict] = []  # Store metadata for each vector

        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load()

    def add(self, embeddings: list[list[float]], metadata: list[dict]):
        """Add vectors to the index.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dicts (one per embedding)
        """
        if not embeddings:
            return

        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)

        # Add to FAISS index
        self.index.add(vectors)

        # Store metadata
        self.metadata.extend(metadata)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10
    ) -> list[dict]:
        """Search for similar vectors.

        Args:
            query_embedding: The query embedding
            top_k: Number of results to return

        Returns:
            List of results with metadata and distance
        """
        if self.index.ntotal == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                results.append({
                    **self.metadata[idx],
                    "distance": float(distances[0][i])
                })

        return results

    def save(self):
        """Save index and metadata to disk."""
        if self.index_path is None:
            return

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path) + ".index")

        # Save metadata
        metadata_path = self.index_path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self):
        """Load index and metadata from disk."""
        if self.index_path is None:
            return

        index_path = str(self.index_path) + ".index"
        metadata_path = self.index_path.with_suffix(".json")

        if Path(index_path).exists():
            self.index = faiss.read_index(index_path)

        if Path(metadata_path).exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    @property
    def count(self) -> int:
        """Get number of vectors in the index."""
        return self.index.ntotal
