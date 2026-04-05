"""Model routing for Alibaba Cloud Bailian coding plan API.

Uses Anthropic-compatible API endpoint for Alibaba Cloud Bailian coding plan.
"""

import asyncio
import json
from typing import Any

import requests


class ModelRouter:
    """Route requests to appropriate models based on task type.

    Uses Anthropic-compatible API endpoint for Alibaba Cloud Bailian coding plan.
    """

    # 阿里云百炼 Anthropic 兼容端点 (coding plan)
    BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"

    def __init__(self, api_key: str):
        """Initialize the model router.

        Args:
            api_key: Alibaba Cloud Bailian API key.
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        })

    def _call_anthropic(self, model: str, messages: list[dict], max_tokens: int = 1024, **kwargs) -> str:
        """Call Anthropic-compatible API using /messages endpoint."""
        url = f"{self.BASE_URL}/messages"
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            **kwargs
        }

        response = self.session.post(url, json=data)
        result = response.json()

        if response.status_code == 200:
            # Anthropic format: content is an array of blocks
            content_blocks = result.get("content", [])
            for block in content_blocks:
                if block.get("type") == "text":
                    return block.get("text", "")
            # Fallback: try to get text from first block
            if content_blocks:
                return content_blocks[0].get("text", "")
            return ""
        else:
            error = result.get("error", {})
            raise RuntimeError(f"API error: {error.get('code')} - {error.get('message')}")

    def text_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of the given text."""
        prompt = f"""请为以下内容生成一个简洁的摘要（{max_length}字以内）：

{text}

摘要："""

        return self._call_anthropic(
            model="qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_length,
            temperature=0.7
        )

    def classify(self, text: str, categories: list[str] | None = None) -> dict[str, Any]:
        """Classify text into categories."""
        if categories is None:
            categories = ["AI", "投资", "游戏", "技术", "产品", "其他"]

        prompt = f"""请分析以下内容，将其分类到最合适的类别中，并提取关键词标签。

内容：
{text}

请按照以下 JSON 格式返回结果：
{{
    "category": "类别名称",
    "tags": ["标签 1", "标签 2", ...],
    "confidence": 0.0-1.0
}}

只返回 JSON，不要其他内容。"""

        result = self._call_anthropic(
            model="qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )

        # Extract JSON from response
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        return json.loads(result)

    async def text_summary_async(self, text: str, max_length: int = 500) -> str:
        """Async version of text_summary."""
        return await asyncio.to_thread(self.text_summary, text, max_length)

    async def classify_async(self, text: str, categories: list[str] | None = None) -> dict[str, Any]:
        """Async version of classify."""
        return await asyncio.to_thread(self.classify, text, categories)

    def multimodal_understanding(
        self,
        image_url: str | None = None,
        text: str = ""
    ) -> str:
        """Understand multimodal content (image + text).

        Args:
            image_url: URL or path to image.
            text: Additional text context.

        Returns:
            Description and analysis of the content.
        """
        # This will be implemented in Phase 2 for video frames
        raise NotImplementedError("Multimodal understanding will be implemented in Phase 2")


# Global router instance
_router: ModelRouter | None = None


def get_router() -> ModelRouter:
    """Get the global model router instance."""
    global _router
    if _router is None:
        from .config import get_config
        config = get_config()
        _router = ModelRouter(config.bailian_api_key)
    return _router
