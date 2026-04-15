"""Model routing for Alibaba Cloud Bailian API.

Supports multiple models (Qwen, GLM, Kimi, MiniMax) via
Anthropic-compatible API endpoint.
"""

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)


class ModelRouter:
    """Route requests to models via Anthropic-compatible API endpoint."""

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
        max_retries: int = 5,
        timeout: int = 120,
        fallback_model: str = "glm-5",
        **kwargs
    ) -> str:
        """Call any model via Anthropic-compatible API.

        Args:
            model: Model name (e.g., "qwen3.6-plus", "glm-5")
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            max_retries: Maximum retry attempts on connection errors
            timeout: Request timeout in seconds
            fallback_model: Backup model to use if primary fails
            **kwargs: Additional parameters to pass to API

        Returns:
            Model response text
        """
        try:
            return self._call_model(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                max_retries=max_retries,
                timeout=timeout,
                **kwargs
            )
        except RuntimeError as e:
            if fallback_model and fallback_model != model:
                logger.warning(f"Primary model '{model}' failed, falling back to '{fallback_model}'...")
                try:
                    return self._call_model(
                        model=fallback_model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        max_retries=max(1, max_retries // 2),
                        timeout=timeout,
                        **kwargs
                    )
                except RuntimeError:
                    logger.error(f"Fallback model '{fallback_model}' also failed")
                    raise
            raise

    def _call_model(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        max_retries: int = 5,
        timeout: int = 120,
        **kwargs
    ) -> str:
        """Internal model call method (no fallback)."""
        url = f"{self.base_url}/messages"
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs
        }

        last_error = None
        for attempt in range(max_retries):
            try:
                logger.info(f"API call to {model} (attempt {attempt + 1}/{max_retries}, timeout={timeout}s)")
                response = self.session.post(url, json=data, timeout=timeout)
                result = response.json()

                if response.status_code == 200:
                    content_blocks = result.get("content", [])
                    for block in content_blocks:
                        if block.get("type") == "text":
                            return block.get("text", "")
                    if content_blocks:
                        return content_blocks[0].get("text", "")
                    return ""
                else:
                    error = result.get("error", {})
                    raise RuntimeError(f"API error ({error.get('code')}): {error.get('message')}")

            except requests.exceptions.Timeout as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"API timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {max_retries} retries: timeout")
                    raise RuntimeError(f"API timeout after {max_retries} retries")

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ProxyError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(f"Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API call failed after {max_retries} retries: {last_error}")
                    raise RuntimeError(f"Failed after {max_retries} retries: {last_error}")

        return ""

    def text_summary(self, text: str, max_length: int = 500, model: str | None = None, timeout: int | None = None) -> str:
        """Generate a summary of the given text."""
        prompt = f"""请为以下内容生成一个简洁的摘要（{max_length}字以内）：

{text}

摘要："""

        return self.call(
            model=model or "qwen3.6-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_length,
            temperature=0.7,
            timeout=timeout or 120
        )

    def chat(
        self,
        messages: list[dict],
        model: str = "qwen3.6-plus",
        **kwargs
    ) -> str:
        """Generic chat interface with any model."""
        return self.call(model=model, messages=messages, **kwargs)


# Global router instance
_router: ModelRouter | None = None


def get_router(api_key: str | None = None, base_url: str | None = None) -> ModelRouter:
    """Get the global model router instance."""
    global _router
    if _router is None or api_key is not None or base_url is not None:
        from .config import get_config
        config = get_config()
        _router = ModelRouter(
            api_key=api_key or config.bailian_api_key,
            base_url=base_url or "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"
        )
    return _router


def quick_call(prompt: str, model: str = "qwen3.6-plus") -> str:
    """Quick one-line model call without managing router instance."""
    router = get_router()
    return router.chat(messages=[{"role": "user", "content": prompt}], model=model)
