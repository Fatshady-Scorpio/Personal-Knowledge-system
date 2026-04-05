"""BM25 keyword search for local retrieval."""

from rank_bm25 import BM25Okapi
from pathlib import Path
from typing import Optional
import pickle
import jieba


class BM25Search:
    """BM25-based keyword search over knowledge base."""

    def __init__(self, knowledge_root: str | Path):
        self.knowledge_root = Path(knowledge_root)
        self.documents: list[dict] = []
        self.bm25: Optional[BM25Okapi] = None
        self.index_path = self.knowledge_root / ".bm25_index"

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        return list(jieba.cut(text))

    def build_index(self) -> int:
        """Build BM25 index from knowledge base.

        Returns:
            Number of documents indexed
        """
        self.documents = []
        tokenized_docs = []

        # Scan markdown files
        for md_file in self.knowledge_root.rglob("*.md"):
            if "20-Processed" in str(md_file):
                content = md_file.read_text(encoding="utf-8")
                self.documents.append({
                    "title": md_file.stem,
                    "content": content,
                    "content_preview": content[:500],
                    "file_path": str(md_file),
                    "category": md_file.parent.name
                })
                tokenized_docs.append(self.tokenize(content))

        # Build BM25 index
        if tokenized_docs:
            self.bm25 = BM25Okapi(tokenized_docs)
            self.save_index()

        return len(self.documents)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search for documents matching query.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching documents with scores
        """
        if self.bm25 is None:
            self.load_index()

        if self.bm25 is None:
            return []

        query_tokens = self.tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self.documents[idx].copy()
                doc["score"] = float(scores[idx])
                results.append(doc)

        return results

    def save_index(self):
        """Save BM25 index to disk."""
        if self.bm25 is None:
            return

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "bm25_state": self.bm25
            }, f)

    def load_index(self):
        """Load BM25 index from disk."""
        if not self.index_path.exists():
            return

        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.bm25 = data["bm25_state"]
