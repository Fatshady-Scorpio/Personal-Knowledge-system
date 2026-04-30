"""Context Manager - Manages token budget and selective loading for wiki queries.

This module handles:
1. Token budget management for large knowledge bases
2. Hierarchical loading (index → topic → entry → details)
3. Relevance-based context selection
4. Context window optimization
"""

import logging
from pathlib import Path
from typing import Optional
import tiktoken

logger = logging.getLogger(__name__)


class ContextManager:
    """Manage context loading with token budget constraints."""

    def __init__(
        self,
        wiki_dir: Path,
        token_budget: int = 100000,
        model: str = "qwen3.6-plus",
        domain: Optional[str] = None,
    ):
        self.wiki_dir = wiki_dir
        self.domain = domain

        if domain:
            # Domain-scoped: use domain directories
            self.concepts_dir = wiki_dir / "domains" / domain / "concepts"
            self.topics_dir = wiki_dir / "domains" / domain / "topics"
            self.index_path = wiki_dir / "domains" / domain / "index.md"
        else:
            # Legacy: flat structure
            self.concepts_dir = wiki_dir / "concepts"
            self.topics_dir = wiki_dir / "topics"
            self.index_path = wiki_dir / "index.md"

        self.token_budget = token_budget
        self.model = model

        # Token counter (use tiktoken for estimation)
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None

        # Loaded content cache
        self.loaded_entries: dict[str, str] = {}
        self.current_tokens: int = 0

    def load_for_query(self, query: str) -> dict:
        """Load relevant context for a query within token budget.

        Karpathy pattern: LLM reads index.md to navigate, not bulk loading.
        1. Load full domain index.md for LLM navigation
        2. Pre-load only entries with exact keyword match in title
        3. LLM uses index to identify additional entries worth reading
        4. Traverse bilateral links from pre-loaded entries (depth=1, max=3)
        5. Token budget prevents overloading

        Args:
            query: The user's query

        Returns:
            Dictionary with:
            - index: Full domain index (LLM navigates from here)
            - entries: Dict of {entry_name: content} (only exact matches)
            - related: List of related concept names
        """
        self.loaded_entries.clear()
        self.current_tokens = 0

        result = {
            "index": "",
            "entries": {},
            "related": [],
        }

        # Step 1: Load full domain index.md for LLM navigation
        if self.index_path.exists():
            index_content = self.index_path.read_text(encoding="utf-8")
            index_tokens = self._count_tokens(index_content)
            # Only include index if it fits within 20% of budget
            if index_tokens <= self.token_budget * 0.2:
                result["index"] = index_content
                self.current_tokens += index_tokens

        # Step 2: Extract only exact-match candidate entries (narrow pre-filter)
        candidates = self._extract_candidates_from_index(query)

        # Step 3: Load only the most relevant entries (token budget)
        for candidate in candidates:
            if self.current_tokens >= self.token_budget * 0.5:
                break

            content = self._load_entry(candidate)
            if content:
                entry_tokens = self._count_tokens(content)
                if self.current_tokens + entry_tokens <= self.token_budget * 0.5:
                    result["entries"][candidate] = content
                    result["related"].append(candidate)
                    self.current_tokens += entry_tokens

        # Step 4: Traverse bilateral links from loaded entries (limited)
        if result["entries"]:
            related = self._traverse_links(
                list(result["entries"].keys()),
                depth=1,
                max_additional=3,
            )
            for entry_name in related:
                if entry_name not in result["entries"]:
                    content = self._load_entry(entry_name)
                    if content:
                        entry_tokens = self._count_tokens(content)
                        if self.current_tokens + entry_tokens <= self.token_budget * 0.5:
                            result["entries"][entry_name] = content
                            result["related"].append(entry_name)
                            self.current_tokens += entry_tokens

        logger.info(
            f"Loaded context: {len(result['entries'])} entries, "
            f"{self.current_tokens}/{self.token_budget} tokens"
        )

        return result

    def _extract_candidates_from_index(self, query: str) -> list[str]:
        """Extract candidate entry names from index.

        Strategy: Return entries whose title matches query keywords.
        If no title match, return empty — the LLM navigates via the full
        index.md loaded in result["index"] without pre-loaded entries.

        Returns:
            List of entry names to pre-load
        """
        import re

        if not self.index_path.exists():
            return self._scan_all_entries()

        content = self.index_path.read_text(encoding="utf-8")
        query_lower = query.lower()

        # Extract all [[wiki links]] from index
        link_pattern = re.compile(r"\[\[([^\]]+)\]\]")
        all_links = []
        for match in link_pattern.findall(content):
            name = match.split("|")[0].strip() if "|" in match else match.strip()
            all_links.append(name)

        # Return entries whose title contains query keywords
        query_words = [w for w in query_lower.split() if len(w) >= 2]
        matched = [link for link in all_links if any(w in link.lower() for w in query_words)]
        return matched

    def _scan_all_entries(self) -> list[str]:
        """Fallback: scan all entry files when index is unavailable."""
        candidates = []
        for directory in [self.concepts_dir, self.topics_dir]:
            if directory.exists():
                for md_file in directory.glob("*.md"):
                    candidates.append(md_file.stem)
        return candidates

    def _load_entry(self, name: str) -> Optional[str]:
        """Load a wiki entry by name.

        Args:
            name: Entry name (filename without .md)

        Returns:
            Content string or None if not found
        """
        # Check cache first
        if name in self.loaded_entries:
            return self.loaded_entries[name]

        # Try concepts directory
        concept_path = self.concepts_dir / f"{name}.md"
        if concept_path.exists():
            content = concept_path.read_text(encoding="utf-8")
            self.loaded_entries[name] = content
            return content

        # Try topics directory
        topic_path = self.topics_dir / f"{name}.md"
        if topic_path.exists():
            content = topic_path.read_text(encoding="utf-8")
            self.loaded_entries[name] = content
            return content

        return None

    def _traverse_links(
        self,
        start_entries: list[str],
        depth: int = 1,
        max_additional: int = 10,
    ) -> list[str]:
        """Traverse bilateral links from starting entries.

        Args:
            start_entries: Starting entry names
            depth: How many hops to follow
            max_additional: Maximum additional entries to return

        Returns:
            List of related entry names
        """
        from ..compiler.link_extractor import LinkExtractor

        extractor = LinkExtractor(self.wiki_dir)
        extractor.build_link_graph()

        related = set()
        to_visit = set(start_entries)
        visited = set()

        for _ in range(depth):
            next_level = set()
            for current in to_visit:
                if current in visited:
                    continue
                visited.add(current)

                # Add outgoing links
                if current in extractor.outgoing_links:
                    next_level.update(extractor.outgoing_links[current])
                    related.update(extractor.outgoing_links[current])

                # Add incoming links
                if current in extractor.incoming_links:
                    next_level.update(extractor.incoming_links[current])
                    related.update(extractor.incoming_links[current])

            to_visit = next_level
            if len(related) >= max_additional:
                break

        related -= set(start_entries)
        return list(related)[:max_additional]

    def _count_tokens(self, text: str) -> int:
        """Count tokens in text.

        Uses tiktoken if available, otherwise estimates by character count.
        """
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            # Rough estimate: 4 characters per token for English
            # 2 characters per token for Chinese
            chinese_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            other_chars = len(text) - chinese_chars
            return chinese_chars // 2 + other_chars // 4

    def get_usage_stats(self) -> dict:
        """Get current context usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            "loaded_entries": len(self.loaded_entries),
            "current_tokens": self.current_tokens,
            "token_budget": self.token_budget,
            "utilization": self.current_tokens / self.token_budget,
        }

    def clear_cache(self) -> None:
        """Clear the loaded entries cache."""
        self.loaded_entries.clear()
        self.current_tokens = 0
