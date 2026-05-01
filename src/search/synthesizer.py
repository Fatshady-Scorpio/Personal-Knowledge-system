"""Synthesizer — Generate answers from retrieved wiki context.

Supports multiple synthesis modes:
- local_only: Answer from wiki content only
- hybrid: Wiki + external web results (injected by CLI/Agent)
"""

import logging
from typing import Optional

from ..utils.model_router import get_router
from .web_search import WebResult

logger = logging.getLogger(__name__)


class Synthesizer:
    """Synthesize answers from retrieved wiki context."""

    def __init__(self, model: str = "qwen3.6-plus"):
        self.model = model
        self.router = get_router()

    def synthesize_hybrid(
        self,
        query: str,
        wiki_results: list[dict],
        web_results: Optional[list[WebResult]] = None,
        domain_name: str = "",
    ) -> str:
        """Generate answer combining wiki + web results.

        Web results are injected externally (by CLI or Agent-level WebSearch).

        Args:
            query: User query
            wiki_results: List of {name, score, content, source}
            web_results: Optional list of WebResult from external search
            domain_name: Domain name for context

        Returns:
            Generated answer string
        """
        wiki_text = self._format_results(wiki_results)
        web_text = ""
        if web_results:
            web_text = self._format_web_results(web_results)

        return self._synthesize_with_sources(
            query=query,
            wiki_text=wiki_text,
            web_text=web_text,
            domain_name=domain_name,
            wiki_count=len(wiki_results),
            web_count=len(web_results) if web_results else 0,
        )

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

    def _format_web_results(self, results: list[WebResult]) -> str:
        """Format web search results for the prompt."""
        if not results:
            return "网络搜索无结果"

        lines = []
        for r in results:
            lines.append(f"#### {r.title}\n- 来源: {r.url}\n- 摘要: {r.snippet}\n")

        return "\n".join(lines)

    def _synthesize_with_sources(
        self,
        query: str,
        wiki_text: str,
        web_text: str,
        domain_name: str,
        wiki_count: int,
        web_count: int,
    ) -> str:
        """Generate answer with both wiki and web sources."""
        has_web = bool(web_text)

        prompt = f"""你是一个知识库助手。请基于以下来源回答用户问题。

## 个人知识库（{domain_name or "未知领域"}，{wiki_count} 个词条）

{wiki_text}

## 网络搜索结果（{web_count} 条）

{web_text if has_web else "未触发网络搜索"}

## 用户问题

{query}

## 回答要求

1. **优先使用个人知识库内容**，标注来源 [[词条名]]
2. 如果知识库不足且**有网络搜索结果**，综合两者回答，标注"来自网络"
3. 如果知识库不足且**没有网络搜索结果**，用通用知识补充，标注"知识库未收录"
4. 明确区分哪些来自 wiki，哪些来自网络，哪些是你的通用知识

## 回答格式

### 来自个人知识库
[基于 wiki 的回答，带 [[链接]]]

### 来自网络（如有）
[基于网络搜索的回答，带来源链接]

### 通用补充（如有）
[标注"知识库未收录"]
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
