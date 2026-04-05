"""Knowledge API for external agent integration."""

from pathlib import Path
from typing import Optional
import json

from ..retriever.embedder import Embedder
from ..retriever.vector_store import VectorStore
from ..retriever.semantic_search import SemanticSearch
from ..retriever.rag_qa import RAGQA
from ..utils.config import get_config


class KnowledgeAPI:
    """External API for knowledge base access."""

    def __init__(self, knowledge_root: str | Path | None = None):
        self.config = get_config()
        self.knowledge_root = Path(knowledge_root or self.config.paths.get("knowledge_root", "./knowledge"))

        # Initialize retriever components
        self.embedder = Embedder(api_key=self.config.bailian_api_key)
        self.vector_store = VectorStore(
            dimension=1536,
            index_path=self.config.settings.get("retriever", {}).get("index_path")
        )
        self.semantic_search = SemanticSearch(
            embedder=self.embedder,
            vector_store=self.vector_store,
            knowledge_root=self.knowledge_root
        )
        self.rag_qa = RAGQA(
            embedder=self.embedder,
            vector_store=self.vector_store,
            model=self.config.settings.get("retriever", {}).get("rag", {}).get("model", "qwen3.5-plus")
        )

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search knowledge base.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching documents
        """
        return self.semantic_search.search(query, top_k=top_k)

    def answer(self, question: str, top_k: int = 5) -> dict:
        """Answer question using knowledge base.

        Args:
            question: The question
            top_k: Number of context documents

        Returns:
            Dictionary with answer and sources
        """
        return self.rag_qa.answer(question, top_k=top_k)

    def get_note(self, title: str) -> dict | None:
        """Get a specific note by title.

        Args:
            title: Note title

        Returns:
            Note content and metadata
        """
        # Search in 20-Processed and 30-Topics
        for category in ["20-Processed", "30-Topics"]:
            note_path = self.knowledge_root / category / f"{title}.md"
            if note_path.exists():
                content = note_path.read_text(encoding="utf-8")
                return {
                    "title": title,
                    "content": content,
                    "path": str(note_path),
                    "category": category
                }
        return None

    def list_topics(self) -> list[str]:
        """List all topic categories.

        Returns:
            List of topic names
        """
        topics_dir = self.knowledge_root / "30-Topics"
        if not topics_dir.exists():
            return []
        return [d.name for d in topics_dir.iterdir() if d.is_dir()]

    def get_topic_notes(self, topic: str) -> list[dict]:
        """Get all notes in a topic.

        Args:
            topic: Topic name

        Returns:
            List of note metadata
        """
        topic_dir = self.knowledge_root / "30-Topics" / topic
        if not topic_dir.exists():
            return []

        notes = []
        for md_file in topic_dir.rglob("*.md"):
            notes.append({
                "title": md_file.stem,
                "path": str(md_file),
                "preview": md_file.read_text(encoding="utf-8")[:200]
            })
        return notes
