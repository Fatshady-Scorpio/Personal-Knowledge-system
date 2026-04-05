"""Model routing for Alibaba Cloud Bailian coding plan API.

Supports multiple model providers (Qwen, GLM, Kimi, MiniMax, DeepSeek) via
Anthropic-compatible API endpoint.
"""

import asyncio
import json
from typing import Any

import requests


class ModelRouter:
    """Route requests to appropriate models based on task type.

    Uses Anthropic-compatible API endpoint for Alibaba Cloud Bailian coding plan.
    Supports switching models per task type via configuration.
    """

    def __init__(self, api_key: str, base_url: str = "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"):
        """Initialize the model router.

        Args:
            api_key: Alibaba Cloud Bailian API key.
            base_url: API endpoint URL.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        })

    def call(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Call any model via Anthropic-compatible API.

        Args:
            model: Model name (e.g., "qwen3.5-plus", "glm-4", "kimi-latest")
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            **kwargs: Additional parameters to pass to API

        Returns:
            Model response text
        """
        url = f"{self.base_url}/messages"
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
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
            raise RuntimeError(f"API error ({error.get('code')}): {error.get('message')}")

    def call_with_model(
        self,
        task_type: str,
        prompt: str,
        model_override: str | None = None,
        **kwargs
    ) -> str:
        """Call model based on task type with optional override.

        Args:
            task_type: Task type for model routing (e.g., "text_summary")
            prompt: The prompt to send
            model_override: Override default model for this task type
            **kwargs: Additional parameters

        Returns:
            Model response text
        """
        from .config import get_config
        config = get_config()

        # Get model for task type
        if model_override:
            model = model_override
        else:
            model = config.get_model_for_task(task_type)

        messages = [{"role": "user", "content": prompt}]
        return self.call(model=model, messages=messages, **kwargs)

    def text_summary(self, text: str, max_length: int = 500, model: str | None = None) -> str:
        """Generate a summary of the given text."""
        prompt = f"""请为以下内容生成一个简洁的摘要（{max_length}字以内）：

{text}

摘要："""

        return self.call(
            model=model or "qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_length,
            temperature=0.7
        )

    def classify(self, text: str, categories: list[str] | None = None, model: str | None = None) -> dict[str, Any]:
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

        result = self.call(
            model=model or "qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3
        )

        # Extract JSON from response
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        return json.loads(result)

    def compare_models(
        self,
        prompt: str,
        models: list[str],
        **kwargs
    ) -> dict[str, str]:
        """Call multiple models with the same prompt and compare results.

        Args:
            prompt: The prompt to send to all models
            models: List of model names to test
            **kwargs: Additional parameters

        Returns:
            Dict mapping model name to response text
        """
        results = {}
        messages = [{"role": "user", "content": prompt}]

        for model in models:
            try:
                results[model] = self.call(model=model, messages=messages, **kwargs)
            except Exception as e:
                results[model] = f"Error: {e}"

        return results

    def chat(
        self,
        messages: list[dict],
        model: str = "qwen3.5-plus",
        **kwargs
    ) -> str:
        """Generic chat interface with any model.

        Args:
            messages: List of message dicts (can include conversation history)
            model: Model to use
            **kwargs: Additional parameters

        Returns:
            Model response text
        """
        return self.call(model=model, messages=messages, **kwargs)

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


def get_router(api_key: str | None = None, base_url: str | None = None) -> ModelRouter:
    """Get the global model router instance.

    Args:
        api_key: Optional override for API key
        base_url: Optional override for base URL

    Returns:
        ModelRouter instance
    """
    global _router
    if _router is None or api_key is not None or base_url is not None:
        from .config import get_config
        config = get_config()
        _router = ModelRouter(
            api_key=api_key or config.bailian_api_key,
            base_url=base_url or config.settings.get("bailian", {}).get("base_url")
        )
    return _router


def quick_call(prompt: str, model: str = "qwen3.5-plus") -> str:
    """Quick one-line model call without managing router instance.

    Args:
        prompt: The prompt to send
        model: Model name to use

    Returns:
        Model response text

    Example:
        >>> from src.utils.model_router import quick_call
        >>> response = quick_call("你好", model="qwen3.5-plus")
    """
    router = get_router()
    return router.chat(messages=[{"role": "user", "content": prompt}], model=model)
