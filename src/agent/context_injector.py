"""Context injector for Claude/Agent integration."""

from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from ..retriever.embedder import Embedder
from ..retriever.vector_store import VectorStore
from ..retriever.semantic_search import SemanticSearch
from ..utils.config import get_config


class ContextInjector:
    """Inject relevant knowledge context into Claude/Agent sessions."""

    def __init__(self, knowledge_root: str | Path | None = None):
        self.config = get_config()
        self.knowledge_root = Path(knowledge_root or self.config.paths.get("knowledge_root", "./knowledge"))
        self.context_dir = self.knowledge_root / ".claude_contexts"
        self.context_dir.mkdir(parents=True, exist_ok=True)

        # Initialize search
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

    def get_context(
        self,
        query: str,
        max_notes: int = 5,
        include_full_content: bool = False
    ) -> str:
        """Get relevant context as markdown-formatted string.

        Args:
            query: The topic or question to get context for
            max_notes: Maximum number of notes to include
            include_full_content: Whether to include full content or just preview

        Returns:
            Formatted context string
        """
        # Search for relevant notes
        results = self.semantic_search.search(query, top_k=max_notes, min_score=0.3)

        if not results:
            return "未找到相关的知识内容。"

        # Build context string
        context_parts = [f"# 相关知识上下文 (查询：{query})\n"]

        for i, r in enumerate(results, 1):
            context_parts.append(f"\n## {i}. {r['title']}\n")
            context_parts.append(f"**分类**: {r.get('category', 'Unknown')}\n")
            context_parts.append(f"**标签**: {', '.join(r.get('tags', []))}\n")
            context_parts.append(f"**来源**: {r.get('file_path', '')}\n\n")

            if include_full_content and r.get('file_path'):
                try:
                    content = Path(r['file_path']).read_text(encoding='utf-8')
                    context_parts.append(content)
                except Exception:
                    context_parts.append(r.get('content_preview', ''))
            else:
                context_parts.append(r.get('content_preview', ''))

            context_parts.append("\n---\n")

        return "".join(context_parts)

    def save_context(self, query: str, context: str, session_id: str = "default") -> str:
        """Save context to file for later retrieval.

        Args:
            query: The query that generated the context
            context: The context string
            session_id: Session identifier

        Returns:
            Path to saved context file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"context_{session_id}_{timestamp}.md"
        filepath = self.context_dir / filename

        filepath.write_text(f"<!-- Query: {query} -->\n\n{context}", encoding="utf-8")
        return str(filepath)

    def load_context(self, session_id: str = "default") -> str | None:
        """Load most recent context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Context content or None if not found
        """
        context_files = sorted(self.context_dir.glob(f"context_{session_id}_*.md"), reverse=True)
        if not context_files:
            return None
        return context_files[0].read_text(encoding="utf-8")

    def clear_contexts(self, session_id: str | None = None):
        """Clear saved contexts.

        Args:
            session_id: If provided, only clear for specific session
        """
        if session_id:
            pattern = f"context_{session_id}_*.md"
        else:
            pattern = "context_*.md"

        for f in self.context_dir.glob(pattern):
            f.unlink()
