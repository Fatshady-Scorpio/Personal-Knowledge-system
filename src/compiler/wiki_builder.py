"""Wiki Builder - Compiles raw materials into structured wiki entries.

This module uses LLM to:
1. Extract core concepts from raw materials
2. Generate summaries
3. Identify bilateral links ([[link]] syntax)
4. Create structured wiki entries with metadata

Supports bilingual (English->Chinese) concept extraction and wiki entry generation.
"""

import logging
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from ..utils.model_router import get_router
from .raw_processor import RawMaterial, RawProcessor

logger = logging.getLogger(__name__)


class WikiBuilder:
    """Build wiki entries from raw materials using LLM compilation."""

    def __init__(
        self,
        raw_processor: RawProcessor,
        wiki_dir: Path,
        model: Optional[str] = None,
    ):
        self.raw_processor = raw_processor
        self.wiki_dir = wiki_dir
        self.concepts_dir = wiki_dir / "concepts"
        self.topics_dir = wiki_dir / "topics"
        self.model = model or "qwen3.6-plus"
        self.router = get_router()

        # Ensure directories exist
        self.concepts_dir.mkdir(parents=True, exist_ok=True)
        self.topics_dir.mkdir(parents=True, exist_ok=True)

    def compile(self, raw_path: Path, output_dir: Optional[Path] = None) -> list[Path]:
        """Compile a raw material into wiki entries.

        Args:
            raw_path: Path to the raw material
            output_dir: Optional specific output directory

        Returns:
            List of paths to created wiki entries
        """
        logger.info(f"Compiling raw material: {raw_path}")

        # Read raw material
        material = self.raw_processor.read(raw_path)

        if material.status == "compiled":
            logger.warning(f"Material already compiled: {raw_path}")
            return []

        # Use LLM to extract concepts and generate wiki entries
        concepts = self._extract_concepts(material)

        # Create wiki entries
        created_paths = []
        for concept in concepts:
            path = self._create_wiki_entry(concept, material)
            if path:
                created_paths.append(path)

        # Update raw material status
        if created_paths:
            self.raw_processor.update_status(raw_path, "compiled")

        logger.info(f"Created {len(created_paths)} wiki entries from {raw_path}")
        return created_paths

    def _extract_concepts(self, material: RawMaterial) -> list[dict]:
        """Use LLM to extract concepts from raw material.

        Detects if content is primarily English and uses bilingual prompt.

        Returns:
            List of concept dictionaries with title, definition, summary, related, etc.
        """
        has_english = self._detect_english_content(material)

        if has_english:
            prompt = self._build_bilingual_prompt(material)
        else:
            prompt = self._build_chinese_prompt(material)

        try:
            response = self.router.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.3,
                timeout=120,
            )

            import json

            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()

            concepts = json.loads(response)
            logger.info(f"Extracted {len(concepts)} concepts")
            return concepts

        except Exception as e:
            logger.error(f"Failed to extract concepts: {e}")
            return []

    def _detect_english_content(self, material: RawMaterial) -> bool:
        """Detect if the material contains significant English content."""
        text_to_check = material.content + (material.user_notes or "")

        english_chars = sum(1 for c in text_to_check if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in text_to_check if c.isalpha())

        return total_chars > 0 and (english_chars / total_chars) > 0.3

    def _build_bilingual_prompt(self, material: RawMaterial) -> str:
        """Build prompt for bilingual (English->Chinese) concept extraction."""
        return f"""请从以下英文内容中提取核心概念，生成**中英文双语**的结构化知识词条。

## 输入材料
**标题**: {material.title}
**来源**: {material.source or '未知'}
**标签**: {', '.join(material.tags) if material.tags else '无'}

**内容** (英文原文):
{material.content[:8000]}

{f"**用户的思考**: {material.user_notes}" if material.user_notes else ""}

## 任务要求

请提取 3-8 个核心概念，为每个概念生成以下信息（**中英文双语**，JSON 格式）：

```json
[
    {{
        "title": "中文概念名称",
        "title_en": "English concept name",
        "definition": "中文定义（50 字以内）",
        "definition_en": "English definition (one sentence)",
        "summary": "中文详细解释（200-300 字）",
        "summary_en": "English detailed explanation",
        "related": ["相关中文概念 1", "相关中文概念 2"],
        "related_en": ["Related English concept 1", "Related English concept 2"],
        "key_points": ["中文关键点 1", "中文关键点 2", "中文关键点 3"],
        "key_points_en": ["English key point 1", "English key point 2"],
        "confidence": 0.85
    }}
]
```

**要求**:
1. 概念名称要准确、简洁，适合作为双向链接 [[中文名称]]
2. 中文定义要精炼，英文定义保持准确
3. 相关概念应该用中文命名，便于链接
4. confidence 分数反映你对提取准确性的信心

只返回 JSON 数组，不要其他内容。"""

    def _build_chinese_prompt(self, material: RawMaterial) -> str:
        """Build prompt for Chinese-only concept extraction."""
        return f"""请从以下内容中提取核心概念，生成结构化的知识词条。

## 输入材料
**标题**: {material.title}
**来源**: {material.source or '未知'}
**标签**: {', '.join(material.tags) if material.tags else '无'}

**内容**:
{material.content[:8000]}

{f"**用户的思考**: {material.user_notes}" if material.user_notes else ""}

## 任务要求

请提取 3-8 个核心概念，为每个概念生成以下信息（JSON 格式）：

```json
[
    {{
        "title": "概念名称",
        "definition": "一句话定义（50 字以内）",
        "summary": "详细解释（200-300 字）",
        "related": ["相关概念 1", "相关概念 2"],
        "key_points": ["关键点 1", "关键点 2", "关键点 3"],
        "confidence": 0.85
    }}
]
```

**要求**:
1. 概念名称要准确、简洁，适合作为双向链接 [[目标]]
2. 定义要精炼，能一句话说明白
3. 相关概念应该是材料中提到的或常识性的关联
4. confidence 分数反映你对提取准确性的信心

只返回 JSON 数组，不要其他内容。"""

    def _create_wiki_entry(self, concept: dict, source: RawMaterial) -> Optional[Path]:
        """Create a wiki entry for a concept."""
        filename = f"{self._slugify(concept['title'])}.md"
        output_path = self.concepts_dir / filename

        has_english = 'title_en' in concept and concept.get('title_en')

        related_links = [f"[[{r}]]" for r in concept.get("related", [])]
        source_link = f"[[{source.title}]]" if source.title else source.source

        if has_english:
            content = self._build_bilingual_entry(concept, source_link, related_links, source)
        else:
            content = self._build_chinese_entry(concept, source_link, related_links, source)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            logger.info(f"Created wiki entry: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to create wiki entry: {e}")
            return None

    def _build_bilingual_entry(self, concept: dict, source_link: str, related_links: list, source: RawMaterial) -> str:
        """Build a bilingual (Chinese-English) wiki entry."""
        content = f"""---
type: concept
created_from: {source.path.relative_to(self.raw_processor.raw_dir)}
created_at: {datetime.now().isoformat()}
related_topics: {related_links}
confidence: {concept.get('confidence', 0.5)}
tags: {source.tags}
---

# {concept['title']}

> **English**: *{concept.get('title_en', concept['title'])}*

## 定义

{concept['definition']}

> **English**: {concept.get('definition_en', '')}

## 详解

{concept['summary']}

---

### English Explanation

{concept.get('summary_en', '')}

## 关键要点

{self._format_bullet_points(concept.get('key_points', []))}

### Key Points

{self._format_bullet_points(concept.get('key_points_en', []))}

## 相关概念

{chr(10).join(related_links) if related_links else '*暂无相关概念*'}

## 来源

- {source_link}
"""

        if source.user_notes:
            content += f"""
## 备注

{source.user_notes}
"""

        return content

    def _build_chinese_entry(self, concept: dict, source_link: str, related_links: list, source: RawMaterial) -> str:
        """Build a Chinese-only wiki entry."""
        content = f"""---
type: concept
created_from: {source.path.relative_to(self.raw_processor.raw_dir)}
created_at: {datetime.now().isoformat()}
related_topics: {related_links}
confidence: {concept.get('confidence', 0.5)}
tags: {source.tags}
---

# {concept['title']}

## 定义

{concept['definition']}

## 详解

{concept['summary']}

## 关键要点

{self._format_bullet_points(concept.get('key_points', []))}

## 相关概念

{chr(10).join(related_links) if related_links else '*暂无相关概念*'}

## 来源

- {source_link}
"""

        if source.user_notes:
            content += f"""
## 备注

{source.user_notes}
"""

        return content

    def _format_bullet_points(self, points: list[str]) -> str:
        """Format a list of points as markdown bullet points."""
        if not points:
            return ""
        return "\n".join(f"- {p}" for p in points)

    def _slugify(self, text: str) -> str:
        """Convert text to a safe filename slug."""
        slug = text.replace(" ", "_").replace("/", "_")
        slug = "".join(c for c in slug if c.isalnum() or c in "_-")
        return slug

    def compile_all_pending(self, max_workers: int = 1, on_progress: Optional[Callable[[int, int], None]] = None) -> list[Path]:
        """Compile all raw materials with status='raw'.

        Args:
            max_workers: Maximum number of concurrent workers (default: 1 = serial)
            on_progress: Optional callback(current: int, total: int) for progress updates

        Returns:
            List of all created wiki entry paths
        """
        pending = self.raw_processor.list_all(status="raw")

        if not pending:
            return []

        if max_workers <= 1:
            return self._compile_serial(pending, on_progress)
        else:
            return self._compile_parallel(pending, max_workers, on_progress)

    def _compile_serial(self, pending: list[Path], on_progress: Optional[Callable[[int, int], None]] = None) -> list[Path]:
        """Compile files serially."""
        all_created = []
        total = len(pending)

        for i, path in enumerate(pending, 1):
            created = self.compile(path)
            all_created.extend(created)
            if on_progress:
                on_progress(i, total)

        return all_created

    def _compile_parallel(self, pending: list[Path], max_workers: int, on_progress: Optional[Callable[[int, int], None]] = None) -> list[Path]:
        """Compile files in parallel using ThreadPoolExecutor."""
        import concurrent.futures

        all_created = []
        total = len(pending)
        completed = 0

        def _compile_single(path: Path) -> tuple[Path, list[Path]]:
            created = self.compile(path)
            return path, created

        logger.info(f"Starting parallel compilation: {total} files, max_workers={max_workers}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(_compile_single, path): path
                for path in pending
            }

            for future in concurrent.futures.as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    _, created = future.result()
                    all_created.extend(created)
                    logger.info(f"Compiled {path.name} → {len(created)} wiki entries")
                except Exception as e:
                    logger.error(f"Failed to compile {path.name}: {e}", exc_info=True)

                completed += 1
                if on_progress:
                    on_progress(completed, total)

        return all_created
