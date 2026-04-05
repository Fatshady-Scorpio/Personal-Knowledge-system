"""Link analyzer for building knowledge graph connections."""

import json
from ..utils.model_router import get_router


class LinkAnalyzer:
    """Analyze content and build graph connections."""

    def __init__(self):
        self.router = get_router()

    def find_related(
        self,
        content: str,
        existing_notes: list[dict]
    ) -> list[dict]:
        """Find related notes for given content.

        Args:
            content: The content to analyze
            existing_notes: List of existing notes with title, content, tags

        Returns:
            List of related note dicts with relation type
        """
        # Build prompt for LLM
        notes_context = "\n".join([
            f"- {n['title']}: {n.get('tags', [])}"
            for n in existing_notes
        ])

        prompt = f"""分析以下内容，找出与现有笔记的关联：

新内容：
{content[:2000]}

现有笔记：
{notes_context}

请找出相关的笔记（最多 5 个），并说明关联类型。
返回 JSON 格式：
[
    {{"note_title": "笔记标题", "relation": "扩展/反驳/示例/相关"}},
    ...
]
"""

        # Call LLM
        result = self.router.call(
            model="qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Parse JSON
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()

        return json.loads(result)
