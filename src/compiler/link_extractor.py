"""Link Extractor - Extracts and validates bilateral links ([[link]] syntax) from wiki entries.

This module:
1. Extracts all [[wiki links]] from markdown content
2. Builds a link graph (which entries link to which)
3. Validates that linked entries exist
4. Finds broken links and orphaned entries
"""

import logging
import re
from pathlib import Path
from typing import Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class LinkExtractor:
    """Extract and analyze bilateral links from wiki entries."""

    # Pattern for [[wiki links]]
    LINK_PATTERN = re.compile(r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]")

    def __init__(self, wiki_dir: Path):
        self.wiki_dir = wiki_dir
        self.concepts_dir = wiki_dir / "concepts"
        self.topics_dir = wiki_dir / "topics"

        # Link graph: {source_name: [target_names]}
        self.outgoing_links: dict[str, list[str]] = defaultdict(list)
        self.incoming_links: dict[str, list[str]] = defaultdict(list)

    def extract_links(self, content: str) -> list[tuple[str, Optional[str]]]:
        """Extract all wiki links from content.

        Args:
            content: Markdown content

        Returns:
            List of (link_text, alias) tuples
            e.g., [["Transformer", None], ["LLM|大语言模型", "大语言模型"]]
        """
        matches = self.LINK_PATTERN.findall(content)
        return [(m[0], m[1] if m[1] else None) for m in matches]

    def extract_from_file(self, path: Path) -> list[tuple[str, Optional[str]]]:
        """Extract links from a markdown file.

        Args:
            path: Path to markdown file

        Returns:
            List of (link_text, alias) tuples
        """
        if not path.exists():
            return []

        content = path.read_text(encoding="utf-8")
        return self.extract_links(content)

    def build_link_graph(self) -> dict[str, list[str]]:
        """Build a complete link graph from all wiki entries.

        Returns:
            Dictionary mapping source entry names to list of target entry names
        """
        self.outgoing_links.clear()
        self.incoming_links.clear()

        # Scan all markdown files
        for directory in [self.concepts_dir, self.topics_dir]:
            if not directory.exists():
                continue

            for md_file in directory.glob("*.md"):
                source_name = md_file.stem
                links = self.extract_from_file(md_file)

                for link_text, _ in links:
                    # Normalize link target (use exact text as target)
                    target_name = self._normalize_link_name(link_text)
                    self.outgoing_links[source_name].append(target_name)
                    self.incoming_links[target_name].append(source_name)

        logger.info(
            f"Built link graph: {len(self.outgoing_links)} sources, "
            f"{len(self.incoming_links)} targets"
        )

        return dict(self.outgoing_links)

    def find_broken_links(self) -> list[dict]:
        """Find links that point to non-existent entries.

        Returns:
            List of broken link dictionaries with:
            - source: File containing the broken link
            - target: Non-existent target
            - line: Line number (if available)
        """
        if not self.outgoing_links:
            self.build_link_graph()

        # Get all existing entry names
        existing = set()
        for directory in [self.concepts_dir, self.topics_dir]:
            if directory.exists():
                existing.update(f.stem for f in directory.glob("*.md"))

        # Find broken links
        broken = []
        for source, targets in self.outgoing_links.items():
            for target in targets:
                if target not in existing:
                    broken.append({
                        "source": source,
                        "target": target,
                        "type": "missing_target",
                    })

        logger.warning(f"Found {len(broken)} broken links")
        return broken

    def find_orphaned_entries(self) -> list[str]:
        """Find entries with no incoming or outgoing links.

        Returns:
            List of orphaned entry names
        """
        if not self.outgoing_links:
            self.build_link_graph()

        # Get all entry names
        all_entries = set()
        for directory in [self.concepts_dir, self.topics_dir]:
            if directory.exists():
                all_entries.update(f.stem for f in directory.glob("*.md"))

        # Find orphaned entries
        orphaned = []
        for entry in all_entries:
            has_outgoing = entry in self.outgoing_links and len(self.outgoing_links[entry]) > 0
            has_incoming = entry in self.incoming_links and len(self.incoming_links[entry]) > 0

            if not has_outgoing and not has_incoming:
                orphaned.append(entry)

        logger.warning(f"Found {len(orphaned)} orphaned entries")
        return orphaned

    def find_hubs(self, min_connections: int = 5) -> list[tuple[str, int]]:
        """Find highly-connected entries (hubs).

        Args:
            min_connections: Minimum number of connections to be a hub

        Returns:
            List of (entry_name, connection_count) tuples, sorted by count
        """
        if not self.incoming_links:
            self.build_link_graph()

        hubs = []
        for entry, sources in self.incoming_links.items():
            if len(sources) >= min_connections:
                hubs.append((entry, len(sources)))

        hubs.sort(key=lambda x: x[1], reverse=True)
        return hubs

    def get_related_entries(self, entry_name: str, depth: int = 1) -> list[str]:
        """Find entries related to a given entry through links.

        Args:
            entry_name: Starting entry
            depth: How many hops to follow (1 = direct links only)

        Returns:
            List of related entry names
        """
        if not self.outgoing_links:
            self.build_link_graph()

        related = set()
        to_visit = {entry_name}
        visited = set()

        for _ in range(depth):
            next_level = set()
            for current in to_visit:
                if current in visited:
                    continue
                visited.add(current)

                # Add outgoing links
                if current in self.outgoing_links:
                    next_level.update(self.outgoing_links[current])
                    related.update(self.outgoing_links[current])

                # Add incoming links
                if current in self.incoming_links:
                    next_level.update(self.incoming_links[current])
                    related.update(self.incoming_links[current])

            to_visit = next_level

        related.discard(entry_name)  # Remove self
        return list(related)

    def _normalize_link_name(self, link_text: str) -> str:
        """Normalize a link to match file naming convention.

        E.g., "LLM 架构 " -> "LLM_架构"
        """
        # Replace spaces with underscores
        normalized = link_text.replace(" ", "_")
        # Remove special characters except underscore and Chinese
        normalized = "".join(
            c for c in normalized
            if c.isalnum() or c == "_" or "\u4e00" <= c <= "\u9fff"
        )
        return normalized

    def create_link_report(self) -> str:
        """Generate a report on link health.

        Returns:
            Markdown report content
        """
        broken = self.find_broken_links()
        orphaned = self.find_orphaned_entries()
        hubs = self.find_hubs(min_connections=3)

        content = f"""# 链接健康报告

生成时间：{__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M")}

## 统计

- 词条总数：{len(self.outgoing_links)}
- 断裂链接：{len(broken)}
- 孤岛词条：{len(orphaned)}
- 核心枢纽：{len(hubs)}

## 🔴 断裂链接

"""
        if broken:
            for link in broken[:20]:  # Show first 20
                content += f"- `[[{link['target']}]]` in `{link['source']}`\n"
        else:
            content += "✅ 无断裂链接\n"

        content += "\n## ⚪ 孤岛词条（无入链或出链）\n\n"
        if orphaned:
            for entry in orphaned[:20]:
                content += f"- `{entry}`\n"
        else:
            content += "✅ 无孤岛词条\n"

        content += "\n## 🎯 核心枢纽（被频繁引用）\n\n"
        if hubs:
            for entry, count in hubs[:10]:
                content += f"- `{entry}` ({count} 次引用)\n"
        else:
            content += "暂无核心枢纽\n"

        return content
