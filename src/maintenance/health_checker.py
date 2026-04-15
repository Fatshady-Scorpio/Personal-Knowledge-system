"""Health Checker - Performs integrity checks on the wiki knowledge base.

This module checks for:
1. Broken links (links to non-existent entries)
2. Orphaned entries (no incoming or outgoing links)
3. Contradictions (semantic conflicts between entries)
4. Missing sources (claims without citations)
5. Outdated content (stale timestamps)
6. AI hallucination indicators
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from ..utils.model_router import get_router
from ..compiler.link_extractor import LinkExtractor

logger = logging.getLogger(__name__)


class HealthChecker:
    """Perform health checks on the wiki knowledge base."""

    def __init__(self, wiki_dir: Path, model: Optional[str] = None):
        self.wiki_dir = wiki_dir
        self.concepts_dir = wiki_dir / "concepts"
        self.topics_dir = wiki_dir / "topics"
        self.model = model or "qwen3.6-plus"
        self.router = get_router()
        self.link_extractor = LinkExtractor(wiki_dir)

    def run_full_check(self) -> dict:
        """Run all health checks.

        Returns:
            Dictionary with check results
        """
        logger.info("Running full health check...")

        results = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self._get_statistics(),
            "broken_links": self.check_broken_links(),
            "orphaned_entries": self.check_orphaned_entries(),
            "contradictions": self.check_contradictions(),
            "missing_sources": self.check_missing_sources(),
            "outdated_content": self.check_outdated_content(),
            "hallucination_indicators": self.check_hallucination_indicators(),
        }

        logger.info(f"Health check complete: {results['statistics']}")
        return results

    def _get_statistics(self) -> dict:
        """Get basic statistics about the wiki."""
        concepts = list(self.concepts_dir.glob("*.md")) if self.concepts_dir.exists() else []
        topics = list(self.topics_dir.glob("*.md")) if self.topics_dir.exists() else []

        self.link_extractor.build_link_graph()

        return {
            "total_entries": len(concepts) + len(topics),
            "concepts": len(concepts),
            "topics": len(topics),
            "total_links": sum(len(targets) for targets in self.link_extractor.outgoing_links.values()),
            "hub_entries": len(self.link_extractor.find_hubs(min_connections=3)),
        }

    def check_broken_links(self) -> list[dict]:
        """Check for links pointing to non-existent entries.

        Returns:
            List of broken link records
        """
        return self.link_extractor.find_broken_links()

    def check_orphaned_entries(self) -> list[str]:
        """Check for entries with no connections.

        Returns:
            List of orphaned entry names
        """
        return self.link_extractor.find_orphaned_entries()

    def check_contradictions(self) -> list[dict]:
        """Use LLM to detect potential contradictions between entries.

        Returns:
            List of contradiction records with pairs of conflicting entries
        """
        contradictions = []

        # Get entries with confidence scores
        entries_to_check = []
        for directory in [self.concepts_dir, self.topics_dir]:
            if not directory.exists():
                continue
            for md_file in directory.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")
                if "confidence:" in content:
                    entries_to_check.append(md_file)

        # Check pairs of related entries for contradictions
        # Limit to avoid excessive API calls
        entries_to_check = entries_to_check[:20]

        for i, entry1 in enumerate(entries_to_check):
            for entry2 in entries_to_check[i + 1 :]:
                # Only check if they're related (share links)
                if not self._are_related(entry1.stem, entry2.stem):
                    continue

                contradiction = self._check_pair_for_contradiction(entry1, entry2)
                if contradiction:
                    contradictions.append(contradiction)

        return contradictions

    def _are_related(self, name1: str, name2: str) -> bool:
        """Check if two entries are related through links."""
        related = self.link_extractor.get_related_entries(name1, depth=2)
        return name2 in related

    def _check_pair_for_contradiction(
        self,
        path1: Path,
        path2: Path,
    ) -> Optional[dict]:
        """Use LLM to check if two entries contradict.

        Returns:
            Contradiction record or None
        """
        content1 = path1.read_text(encoding="utf-8")
        content2 = path2.read_text(encoding="utf-8")

        prompt = f"""请检查以下两个知识库词条是否存在矛盾或冲突。

## 词条 1: {path1.stem}

{content1[:1500]}

## 词条 2: {path2.stem}

{content2[:1500]}

## 任务

判断两个词条是否存在：
1. **事实矛盾**: 对同一事实的描述不一致
2. **数据冲突**: 引用的数据或数字不一致
3. **定义冲突**: 对同一概念的定义有差异

如果存在矛盾，请说明：
```json
{{
    "type": "事实矛盾 | 数据冲突 | 定义冲突",
    "description": "矛盾的具体描述",
    "entry1_claim": "词条 1 的说法",
    "entry2_claim": "词条 2 的说法"
}}
```

如果没有矛盾，只返回 "null"。

只返回 JSON 或 null，不要其他内容。"""

        try:
            response = self.router.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )

            response = response.strip()
            if response == "null" or not response:
                return None

            # Parse JSON
            import json

            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()

            contradiction = json.loads(response)
            contradiction["entry1"] = path1.stem
            contradiction["entry2"] = path2.stem
            return contradiction

        except Exception as e:
            logger.warning(f"Failed to check contradiction for {path1.stem} vs {path2.stem}: {e}")
            return None

    def check_missing_sources(self) -> list[dict]:
        """Check for claims that lack source citations.

        Returns:
            List of entries with missing sources
        """
        missing = []

        for directory in [self.concepts_dir, self.topics_dir]:
            if not directory.exists():
                continue

            for md_file in directory.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")

                # Check for source metadata
                has_source_meta = "created_from:" in content or "source:" in content

                # Check for inline citations
                has_inline_citations = "来源" in content or "参考文献" in content

                # Check for confidence score
                has_confidence = "confidence:" in content

                if not has_source_meta and not has_inline_citations:
                    missing.append({
                        "entry": md_file.stem,
                        "file": str(md_file),
                        "issue": "missing_source",
                    })

        return missing

    def check_outdated_content(
        self,
        max_age_days: int = 90,
    ) -> list[dict]:
        """Check for potentially outdated content.

        Args:
            max_age_days: Maximum age before content is considered outdated

        Returns:
            List of outdated entry records
        """
        outdated = []
        cutoff = datetime.now() - timedelta(days=max_age_days)

        for directory in [self.concepts_dir, self.topics_dir]:
            if not directory.exists():
                continue

            for md_file in directory.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")

                # Extract created_at from frontmatter
                created_at = self._extract_date(content, "created_at")
                updated_at = self._extract_date(content, "updated_at")

                # Use most recent date
                effective_date = updated_at or created_at

                if effective_date and effective_date < cutoff:
                    outdated.append({
                        "entry": md_file.stem,
                        "file": str(md_file),
                        "created_at": created_at.isoformat() if created_at else None,
                        "updated_at": updated_at.isoformat() if updated_at else None,
                        "age_days": (datetime.now() - effective_date).days,
                    })

        # Sort by age (oldest first)
        outdated.sort(key=lambda x: x["age_days"], reverse=True)
        return outdated

    def check_hallucination_indicators(self) -> list[dict]:
        """Check for potential AI hallucination indicators.

        Indicators include:
        - Low confidence scores
        - Vague sources
        - Unverifiable claims

        Returns:
            List of potential hallucination records
        """
        indicators = []

        for directory in [self.concepts_dir, self.topics_dir]:
            if not directory.exists():
                continue

            for md_file in directory.glob("*.md"):
                content = md_file.read_text(encoding="utf-8")

                # Check confidence score
                confidence = self._extract_confidence(content)
                if confidence is not None and confidence < 0.7:
                    indicators.append({
                        "entry": md_file.stem,
                        "file": str(md_file),
                        "type": "low_confidence",
                        "confidence": confidence,
                    })

                # Check for vague sources
                if "来源" in content:
                    source_section = content.split("来源")[1].split("\n")[0]
                    if len(source_section.strip()) < 10:
                        indicators.append({
                            "entry": md_file.stem,
                            "file": str(md_file),
                            "type": "vague_source",
                        })

        return indicators

    def _extract_date(self, content: str, field: str) -> Optional[datetime]:
        """Extract a date field from frontmatter."""
        import re

        pattern = rf"{field}:\s*(\d{{4}}-\d{{2}}-\d{{2}}[T\s]?\d{{2}}:\d{{2}}:\d{{2}})?"
        match = re.search(pattern, content)

        if match:
            date_str = match.group(1)
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                return None
        return None

    def _extract_confidence(self, content: str) -> Optional[float]:
        """Extract confidence score from frontmatter."""
        import re

        match = re.search(r"confidence:\s*([\d.]+)", content)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def generate_report(self, results: Optional[dict] = None) -> str:
        """Generate a markdown health report.

        Args:
            results: Results from run_full_check() or None to run now

        Returns:
            Markdown report content
        """
        if results is None:
            results = self.run_full_check()

        stats = results["statistics"]

        report = f"""# 知识库健康检查报告

生成时间：{results["timestamp"]}

## 📊 总体统计

| 指标 | 数值 |
|------|------|
| 词条总数 | {stats['total_entries']} |
| 概念词条 | {stats['concepts']} |
| 主题词条 | {stats['topics']} |
| 双向链接 | {stats['total_links']} |
| 核心枢纽 | {stats['hub_entries']} |

## ✅ 检查结果

"""

        # Broken links
        report += "### 断裂链接\n\n"
        if results["broken_links"]:
            for link in results["broken_links"][:10]:
                report += f"- `[[{link['target']}]]` in `{link['source']}`\n"
        else:
            report += "✅ 无断裂链接\n"
        report += "\n"

        # Orphaned entries
        report += "### 孤岛词条\n\n"
        if results["orphaned_entries"]:
            for entry in results["orphaned_entries"][:10]:
                report += f"- `{entry}`\n"
        else:
            report += "✅ 无孤岛词条\n"
        report += "\n"

        # Contradictions
        report += "### 潜在矛盾\n\n"
        if results["contradictions"]:
            for c in results["contradictions"][:10]:
                report += f"- `{c['entry1']}` vs `{c['entry2']}`: {c['description']}\n"
        else:
            report += "✅ 未发现矛盾\n"
        report += "\n"

        # Missing sources
        report += "### 缺少来源\n\n"
        if results["missing_sources"]:
            report += f"共 {len(results['missing_sources'])} 个词条缺少明确来源\n"
        else:
            report += "✅ 所有词条都有来源\n"
        report += "\n"

        # Outdated content
        report += "### 过期内容\n\n"
        if results["outdated_content"]:
            for entry in results["outdated_content"][:10]:
                report += f"- `{entry['entry']}` ({entry['age_days']} 天)\n"
        else:
            report += "✅ 无过期内容\n"
        report += "\n"

        # Hallucination indicators
        report += "### 幻觉风险\n\n"
        if results["hallucination_indicators"]:
            for h in results["hallucination_indicators"][:10]:
                report += f"- `{h['entry']}` ({h['type']})\n"
        else:
            report += "✅ 无幻觉风险指标\n"

        return report

    def save_report(self, report: str, output_dir: Optional[Path] = None) -> Path:
        """Save health report to file.

        Args:
            report: Markdown report content
            output_dir: Output directory (default: wiki/reports/)

        Returns:
            Path to saved report
        """
        if output_dir is None:
            output_dir = self.wiki_dir / "reports"
            output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"health_{timestamp}.md"
        output_path = output_dir / filename

        output_path.write_text(report, encoding="utf-8")
        logger.info(f"Saved health report to {output_path}")

        return output_path
