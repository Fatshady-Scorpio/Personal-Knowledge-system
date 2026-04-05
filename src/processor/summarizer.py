"""Text summarization processor."""

import json
from datetime import datetime
from pathlib import Path

from ..utils.model_router import get_router


class Summarizer:
    """Process raw content and generate summaries with metadata."""

    def __init__(self, output_dir: str | Path | None = None):
        """Initialize the summarizer.

        Args:
            output_dir: Directory for processed markdown files.
        """
        self.router = get_router()
        self.output_dir = Path(output_dir) if output_dir else None

    def process(self, text: str, source_url: str | None = None) -> dict:
        """Process raw text and generate summary with metadata.

        Args:
            text: The raw text content.
            source_url: Optional source URL.

        Returns:
            Dictionary with summary, category, tags, and metadata.
        """
        # Generate summary
        summary = self.router.text_summary(text, max_length=300)

        # Classify content
        classification = self.router.classify(text)

        # Build result
        result = {
            "summary": summary,
            "category": classification.get("category", "其他"),
            "tags": classification.get("tags", []),
            "confidence": classification.get("confidence", 0.0),
            "source_url": source_url,
            "processed_at": datetime.now().isoformat(),
            "original_length": len(text),
            "summary_length": len(summary),
        }

        return result

    def process_to_markdown(
        self,
        text: str,
        title: str | None = None,
        source_url: str | None = None
    ) -> str:
        """Process text and return as markdown format.

        Args:
            text: The raw text content.
            title: Optional title for the note.
            source_url: Optional source URL.

        Returns:
            Markdown formatted string.
        """
        result = self.process(text, source_url)

        # Generate title if not provided
        if not title:
            # Use first line or first 50 chars of summary
            first_line = text.split("\n")[0][:50]
            title = first_line.strip() or "Untitled"

        # Build markdown
        tags_str = ", ".join(result["tags"])
        source_line = f"\n\nSource: {source_url}" if source_url else ""

        markdown = f"""---
title: {title}
category: {result["category"]}
tags: [{tags_str}]
processed_at: {result["processed_at"]}
source_url: {source_url or "N/A"}
---

# {title}

## 摘要

{result["summary"]}

## 标签

{', '.join(result["tags"])}

## 分类

{result["category"]} (置信度：{result["confidence"]:.0%})
{source_line}

---

## 原始内容

{text}
"""

        return markdown

    def save_to_file(
        self,
        text: str,
        title: str | None = None,
        source_url: str | None = None,
        output_dir: str | Path | None = None
    ) -> Path:
        """Process text and save to markdown file.

        Args:
            text: The raw text content.
            title: Optional title for the note.
            source_url: Optional source URL.
            output_dir: Override output directory.

        Returns:
            Path to the saved file.
        """
        markdown = self.process_to_markdown(text, title, source_url)

        # Determine output directory
        out_dir = Path(output_dir) if output_dir else self.output_dir
        if out_dir is None:
            from ..utils.config import get_config
            config = get_config()
            out_dir = Path(config.paths.get("knowledge_root", "./knowledge")) / "20-Processed"

        out_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title[:50])
        filename = f"{safe_title}.md"
        filepath = out_dir / filename

        # Save file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)

        return filepath
