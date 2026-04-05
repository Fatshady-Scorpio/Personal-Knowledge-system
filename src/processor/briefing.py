"""Daily briefing generator."""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from ..utils.config import get_config
from ..graph.graph_store import GraphStore

logger = logging.getLogger(__name__)


class DailyBriefing:
    """Generate daily briefing report."""

    def __init__(self, knowledge_root: Optional[str | Path] = None):
        self.config = get_config()
        self.knowledge_root = Path(knowledge_root or self.config.paths.get("knowledge_root", "./knowledge"))
        self.outputs_dir = self.knowledge_root / "50-Outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        self.graph = GraphStore(
            db_path=self.config.settings.get("graph", {}).get("db_path")
        )

    def generate(self, date: Optional[datetime] = None) -> str:
        """Generate daily briefing for a given date.

        Args:
            date: Date to generate briefing for (default: today)

        Returns:
            Path to generated briefing file
        """
        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        briefing_date = date.strftime("%Y 年 %m 月 %d 日")

        # Find today's processed files
        processed_dir = self.knowledge_root / "20-Processed"
        today_files = []

        if processed_dir.exists():
            for f in processed_dir.rglob("*.md"):
                try:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime.date() == date.date():
                        content = f.read_text(encoding="utf-8")
                        today_files.append({
                            "title": f.stem,
                            "path": str(f),
                            "content": content[:500],  # Preview
                            "full_path": f
                        })
                except Exception as e:
                    logger.debug(f"Error reading file {f}: {e}")

        # Get graph stats
        graph_stats = self._get_graph_stats()

        # Group by category
        categorized = self._categorize_files(today_files)

        # Generate briefing content
        content = self._build_briefing(
            date=briefing_date,
            files=today_files,
            categorized=categorized,
            graph_stats=graph_stats
        )

        # Save briefing
        briefing_file = self.outputs_dir / f"daily_briefing_{date_str}.md"
        briefing_file.write_text(content, encoding="utf-8")

        logger.info(f"Generated daily briefing: {briefing_file}")
        return str(briefing_file)

    def _get_graph_stats(self) -> dict:
        """Get knowledge graph statistics."""
        # This is a simplified version - would need to query the graph
        return {
            "total_nodes": 0,
            "total_edges": 0,
            "hot_topics": []
        }

    def _categorize_files(self, files: list[dict]) -> dict:
        """Categorize files by topic."""
        categories = {}

        for f in files:
            # Try to extract category from content or path
            category = "其他"
            content = f.get("content", "").lower()

            # Simple keyword-based categorization
            if any(kw.lower() in content for kw in ["llm", "大模型", "语言模型"]):
                category = "LLM"
            elif any(kw.lower() in content for kw in ["多模态", "multimodal", "图像"]):
                category = "多模态"
            elif any(kw.lower() in content for kw in ["rag", "检索增强"]):
                category = "RAG"
            elif any(kw.lower() in content for kw in ["agent", "智能体"]):
                category = "Agent"
            elif any(kw.lower() in content for kw in ["推理", "inference", "优化"]):
                category = "推理优化"

            if category not in categories:
                categories[category] = []
            categories[category].append(f)

        return categories

    def _build_briefing(
        self,
        date: str,
        files: list[dict],
        categorized: dict,
        graph_stats: dict
    ) -> str:
        """Build briefing markdown content."""

        parts = [
            f"# 每日 AI 简报 - {date}",
            "",
            f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 今日概览",
            "",
            f"- 处理文章：{len(files)} 篇",
            f"- 新增笔记：{len(files)} 条",
            f"- 更新主题：{len(categorized)} 个",
            "",
        ]

        # Add categorized content
        if categorized:
            parts.append("## 精选内容")
            parts.append("")

            for category, cat_files in sorted(categorized.items()):
                parts.append(f"### {category}")
                parts.append("")

                for f in cat_files[:5]:  # Max 5 per category
                    title = f["title"]
                    # Try to extract original title from content
                    content = f.get("content", "")
                    if "---" in content:
                        frontmatter = content.split("---")[1]
                        if "title:" in frontmatter:
                            title = frontmatter.split("title:")[1].strip().strip('"\'')

                    parts.append(f"- [{title}]({f['path']})")
                    if f["content"]:
                        preview = f["content"][:100].replace("\n", " ")
                        parts.append(f"  > {preview}...")
                    parts.append("")

        # Graph updates section
        parts.extend([
            "## 知识图谱更新",
            "",
            f"- 新增关联：{graph_stats.get('total_edges', 0)} 条",
            "",
        ])

        # Hot topics
        if graph_stats.get("hot_topics"):
            parts.append("### 热点主题")
            parts.append("")
            for topic in graph_stats["hot_topics"][:5]:
                parts.append(f"- {topic}")
            parts.append("")

        # Reading recommendations
        parts.extend([
            "## 推荐阅读",
            "",
            "基于你的兴趣，今日重点关注：LLM、RAG、推理优化",
            "",
            "---",
            "",
            "*此简报由 Personal Knowledge System 自动生成*",
        ])

        return "\n".join(parts)

    def generate_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[str]:
        """Generate briefings for a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of generated briefing file paths
        """
        briefings = []
        current = start_date

        while current <= end_date:
            try:
                path = self.generate(current)
                briefings.append(path)
            except Exception as e:
                logger.error(f"Error generating briefing for {current}: {e}")
            current += timedelta(days=1)

        return briefings
