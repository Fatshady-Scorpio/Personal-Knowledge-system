"""Model routing for Alibaba Cloud Bailian API."""

import asyncio
import json
from typing import Any

import dashscope
from dashscope import TextGeneration


class ModelRouter:
    """Route requests to appropriate Bailian models based on task type."""

    def __init__(self, api_key: str):
        """Initialize the model router.

        Args:
            api_key: Alibaba Cloud Bailian API key.
        """
        dashscope.api_key = api_key
        self.api_key = api_key

    def text_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of the given text.

        Args:
            text: The text to summarize.
            max_length: Maximum length of the summary.

        Returns:
            The generated summary.
        """
        prompt = f"""请为以下内容生成一个简洁的摘要（{max_length}字以内）：

{text}

摘要："""

        response = TextGeneration.call(
            model="qwen-max",
            prompt=prompt,
            max_tokens=max_length,
            temperature=0.7,
        )

        if response.status_code == 200:
            return response.output.text
        else:
            raise RuntimeError(f"API error: {response.code} - {response.message}")

    def classify(self, text: str, categories: list[str] | None = None) -> dict[str, Any]:
        """Classify text into categories.

        Args:
            text: The text to classify.
            categories: Optional list of categories. Defaults to AI/Investment/Gaming.

        Returns:
            Dictionary with category and tags.
        """
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

        response = TextGeneration.call(
            model="qwen-turbo",
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
        )

        if response.status_code == 200:
            result = response.output.text.strip()
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            return json.loads(result)
        else:
            raise RuntimeError(f"API error: {response.code} - {response.message}")

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
