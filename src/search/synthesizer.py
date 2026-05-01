"""Synthesizer — Generate answers from retrieved wiki context.

Supports multiple synthesis modes:
- local_only: Answer from wiki content only
- hybrid: Wiki + web search (Phase 3)
- web_primary: Web search with wiki as supplement (Phase 3)
"""

import logging
from typing import Optional

from ..utils.model_router import get_router

logger = logging.getLogger(__name__)


class Synthesizer:
    """Synthesize answers from retrieved wiki context."""

    def __init__(self, model: str = "qwen3.6-plus"):
        self.model = model
        self.router = get_router()

    def synthesize_local(
        self,
        query: str,
        results: list[dict],
        domain_name: str = "",
    ) -> str:
        """Generate answer from wiki content only.

        Args:
            query: User query
            results: List of {name, score, content, source} from retriever
            domain_name: Domain name for context

        Returns:
            Generated answer string
        """
        context_text = self._format_results(results)

        prompt = f"""你是一个知识库助手。请基于以下 wiki 知识网络回答用户问题。

## 知识库来源（{domain_name or "未知领域"}）

{context_text}

## 用户问题

{query}

## 回答要求

1. 优先使用 wiki 内容回答，标注来源 [[词条名]]
2. 如果 wiki 内容不足以完整回答，明确说明"知识库未收录"的部分
3. 区分哪些来自 wiki，哪些是你的补充
4. 回答简洁有条理

## 回答格式

### 来自知识库的内容
[基于 wiki 的回答，带 [[链接]]]

### 补充说明（如有）
[如果 wiki 内容不足，这里用通用知识补充，标注"知识库尚未收录"]
"""

        try:
            response = self.router.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.5,
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Failed to synthesize answer: {e}")
            return f"抱歉，生成答案时遇到错误：{e}"

    def _format_results(self, results: list[dict]) -> str:
        """Format retrieved results for the prompt."""
        if not results:
            return "暂无相关内容"

        lines = []
        for r in results:
            name = r["name"]
            content = r.get("content", "")
            source = r.get("source", "bm25")

            # Show first 800 chars of each entry
            preview = content[:800] + "..." if len(content) > 800 else content
            source_tag = " (BM25)" if source == "bm25" else " (相关词条)"
            lines.append(f"#### [[{name}]]{source_tag}\n{preview}\n")

        return "\n".join(lines)
