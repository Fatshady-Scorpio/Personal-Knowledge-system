"""Local Retriever — BM25 retrieval + bilateral link expansion per domain.

Combines BM25 text search with wiki link graph traversal for
comprehensive local knowledge retrieval.
"""

import logging
from pathlib import Path
from typing import Optional

from .indexer import DomainIndex, tokenize

logger = logging.getLogger(__name__)


class LocalRetriever:
    """Retrieve wiki entries from a single domain.

    Pipeline:
    1. BM25 search → top-k results
    2. Bilateral link expansion → related entries
    3. Combine, deduplicate, score
    """

    def __init__(self, domain_index: DomainIndex, wiki_root: Path):
        self.index = domain_index
        self.wiki_root = wiki_root

        # Link cache
        self._entry_links: dict[str, list[str]] = {}

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        link_depth: int = 1,
        max_link_expansion: int = 5,
        min_score: float = 0.01,
    ) -> list[dict]:
        """Retrieve entries relevant to query.

        Args:
            query: User query
            top_k: BM25 top-k results
            link_depth: How many hops for link expansion
            max_link_expansion: Maximum additional entries from links
            min_score: Minimum BM25 score to include

        Returns:
            List of {name, score, content, source} dicts
        """
        # Step 1: BM25 search
        bm25_results = self.index.search(query, top_k=top_k)

        # Step 2: Link expansion from top BM25 results
        linked = self._expand_links(
            seed_names=[r["name"] for r in bm25_results[:3]],
            depth=link_depth,
            max_additional=max_link_expansion,
        )

        # Step 3: Combine results
        seen = set()
        results = []

        # Add BM25 results
        for r in bm25_results:
            if r["score"] >= min_score:
                seen.add(r["name"])
                results.append({
                    "name": r["name"],
                    "score": r["score"],
                    "content": r["content"],
                    "source": "bm25",
                })

        # Add linked results (not already in BM25 results)
        for name in linked:
            if name not in seen:
                content = self.index.get_entry(name)
                if content:
                    results.append({
                        "name": name,
                        "score": 0.0,  # Link expansion has no BM25 score
                        "content": content,
                        "source": "link",
                    })
                    seen.add(name)

        return results

    def _expand_links(
        self,
        seed_names: list[str],
        depth: int = 1,
        max_additional: int = 5,
    ) -> list[str]:
        """Traverse bilateral links from seed entries.

        Args:
            seed_names: Starting entry names
            depth: Hops to follow
            max_additional: Maximum additional entries

        Returns:
            List of related entry names
        """
        related = set()
        to_visit = set(seed_names)
        visited = set()

        for _ in range(depth):
            next_level = set()
            for current in to_visit:
                if current in visited:
                    continue
                visited.add(current)

                # Extract links from entry content
                if current not in self._entry_links:
                    content = self.index.get_entry(current)
                    if content:
                        self._entry_links[current] = self._extract_links(content)
                    else:
                        self._entry_links[current] = []

                for link_target in self._entry_links[current]:
                    next_level.add(link_target)
                    related.add(link_target)

            to_visit = next_level
            if len(related) >= max_additional:
                break

        # Remove seed entries
        related -= set(seed_names)
        return list(related)[:max_additional]

    def _extract_links(self, content: str) -> list[str]:
        """Extract wiki link targets from content."""
        import re
        links = re.findall(r"\[\[([^\]]+)\]\]", content)
        return [link.replace(" ", "_") for link in links]

    def get_entry(self, name: str) -> Optional[str]:
        """Get full content of a specific entry."""
        return self.index.get_entry(name)

    def get_domain(self) -> str:
        """Return the domain name."""
        return self.index.domain
