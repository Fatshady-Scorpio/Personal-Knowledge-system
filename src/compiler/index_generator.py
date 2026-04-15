"""Index Generator - Creates and maintains the wiki index.md navigation file.

The index.md serves as:
1. Content-oriented catalog for humans
2. Navigation map for LLM queries
3. Entry point for wiki traversal
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from collections import defaultdict

from ..utils.model_router import get_router

logger = logging.getLogger(__name__)


class IndexGenerator:
    """Generate and maintain the wiki index.md file."""

    def __init__(self, wiki_dir: Path, model: Optional[str] = None):
        self.wiki_dir = wiki_dir
        self.concepts_dir = wiki_dir / "concepts"
        self.topics_dir = wiki_dir / "topics"
        self.index_path = wiki_dir / "index.md"
        self.model = model or "qwen3.6-plus"
        self.router = get_router()

    def generate(self) -> str:
        """Generate the index.md file from existing wiki entries.

        Returns:
            Path to generated index.md as string
        """
        logger.info("Generating wiki index...")

        # Scan all concepts and topics
        concepts = self._scan_entries(self.concepts_dir)
        topics = self._scan_entries(self.topics_dir)

        # Use LLM to organize into hierarchical structure
        index_content = self._organize_index(concepts, topics)

        # Write index file
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(index_content, encoding="utf-8")

        logger.info(f"Generated index.md with {len(concepts)} concepts")
        return str(self.index_path)

    def _scan_entries(self, directory: Path) -> list[dict]:
        """Scan markdown files in a directory.

        Returns:
            List of entry dictionaries with metadata
        """
        entries = []

        if not directory.exists():
            return entries

        for md_file in directory.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                metadata = self._parse_frontmatter(content)

                entries.append({
                    "path": md_file,
                    "name": md_file.stem,
                    "title": metadata.get("title", md_file.stem),
                    "type": metadata.get("type", "concept"),
                    "related": metadata.get("related_topics", []),
                    "confidence": metadata.get("confidence", 0.5),
                    "tags": metadata.get("tags", []),
                    "created_from": metadata.get("created_from", ""),
                })
            except Exception as e:
                logger.warning(f"Failed to parse {md_file}: {e}")

        return entries

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter (simple parser)."""
        metadata = {}

        if not content.startswith("---"):
            return metadata

        parts = content.split("---", 2)
        if len(parts) < 3:
            return metadata

        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Parse lists
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]

                metadata[key] = value

        return metadata

    def _organize_index(self, concepts: list[dict], topics: list[dict]) -> str:
        """Use LLM to organize entries into hierarchical index.

        Args:
            concepts: List of concept entries
            topics: List of topic entries

        Returns:
            Markdown content for index.md
        """
        # Prepare input for LLM
        concept_list = "\n".join([
            f"- {c['title']} (tags: {', '.join(c['tags']) if c['tags'] else '无'})"
            for c in concepts
        ])

        topic_list = "\n".join([
            f"- {t['title']}"
            for t in topics
        ])

        prompt = f"""请为以下知识库词条生成一个层次化的索引目录。

## 现有概念（concepts/）
{concept_list}

## 现有主题（topics/）
{topic_list or "暂无"}

## 任务

请按以下结构生成 index.md：

```markdown
# 知识库索引

最后更新：{datetime.now().strftime("%Y-%m-%d")}

## 核心主题

### 🧠 主题名称
**概述**: 1-2 句话概述

**核心概念**:
- [[概念 1]] - 简短说明
- [[概念 2]] - 简短说明

**子主题**:
- [[子主题 1]]
- [[子主题 2]]

---

## 按领域分类

### 领域名称
- [[相关概念]]
```

## 要求

1. 将相关概念组织成有意义的主题分组
2. 为每个主题写一个简短的概述
3. 使用 [[双向链接]] 格式引用所有词条
4. 使用 emoji 作为主题图标（🧠 🤖 📚 🔧 等）
5. 保持层次清晰，便于浏览

只返回 markdown 内容，不要其他说明。"""

        try:
            response = self.router.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.5,
            )

            # Add header
            content = f"""# 知识库索引

最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}

本文档是知识库的导航目录，支持：
- **人类浏览**: 按主题分类的快速导航
- **LLM 查询**: 作为查询入口点，引导知识遍历

---

"""
            content += response.strip()
            return content

        except Exception as e:
            logger.error(f"Failed to generate index: {e}")
            return self._generate_fallback_index(concepts, topics)

    def _generate_fallback_index(self, concepts: list[dict], topics: list[dict]) -> str:
        """Generate a simple fallback index without LLM."""
        # Group by tags
        by_tags = defaultdict(list)
        for c in concepts:
            for tag in c.get("tags", ["未分类"]):
                by_tags[tag].append(c)

        content = f"""# 知识库索引

最后更新：{datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 按标签分类

"""
        for tag, entries in sorted(by_tags.items()):
            content += f"### {tag}\n\n"
            for e in entries:
                content += f"- [[{e['title']}]]\n"
            content += "\n"

        if topics:
            content += "## 主题\n\n"
            for t in topics:
                content += f"- [[{t['title']}]]\n"

        return content

    def update_incremental(self, new_concepts: list[dict]) -> None:
        """Update index incrementally when new concepts are added.

        Appends new concepts to the existing index under an "新增词条" section,
        avoiding full regeneration unless the index doesn't exist.

        Args:
            new_concepts: List of newly created concept entries
        """
        if not new_concepts:
            logger.info("No new concepts to add to index")
            return

        if not self.index_path.exists():
            # Generate full index if none exists
            self.generate()
            return

        # Append new concepts to existing index
        existing_content = self.index_path.read_text(encoding="utf-8")

        new_section = "\n\n## 新增词条\n\n"
        for concept in new_concepts:
            title = concept.get("title", concept.get("name", "未知"))
            tags = concept.get("tags", [])
            tag_str = f" ({', '.join(tags)})" if tags else ""
            new_section += f"- [[{title}]]{tag_str}\n"

        new_section += f"\n最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"

        updated_content = existing_content.rstrip() + new_section
        self.index_path.write_text(updated_content, encoding="utf-8")
        logger.info(f"Added {len(new_concepts)} new concepts to index incrementally")

    def get_entry_point(self, query_topic: str) -> str:
        """Get the relevant section of index.md for a query topic.

        This allows selective loading of index content based on query.

        Args:
            query_topic: The topic to find in index

        Returns:
            Relevant section of index.md
        """
        if not self.index_path.exists():
            return ""

        content = self.index_path.read_text(encoding="utf-8")

        # Simple heuristic: find section containing the query
        lines = content.split("\n")
        result_lines = []
        in_relevant_section = False

        for line in lines:
            if query_topic.lower() in line.lower():
                in_relevant_section = True

            if in_relevant_section:
                result_lines.append(line)

                # End section at next major heading
                if line.startswith("## ") and query_topic.lower() not in line.lower():
                    break

        return "\n".join(result_lines) if result_lines else content
