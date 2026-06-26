from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

import requests


DEFAULT_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"


class ChatClient(Protocol):
    def call(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: int = 120,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> str:
        ...


@dataclass
class AnthropicCompatibleChatClient:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    session: requests.Session = field(default_factory=requests.Session)

    def call(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int = 1024,
        temperature: float = 0.7,
        timeout: int = 120,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> str:
        url = f"{self.base_url.rstrip('/')}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            **kwargs,
        }

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = self.session.post(url, headers=headers, json=payload, timeout=timeout)
                data = response.json()
                if response.status_code != 200:
                    error = data.get("error", {}) if isinstance(data, dict) else {}
                    message = error.get("message") if isinstance(error, dict) else str(data)
                    raise RuntimeError(f"LLM API error {response.status_code}: {message}")
                return _text_from_response(data)
            except (requests.exceptions.ConnectionError, requests.exceptions.ProxyError, requests.exceptions.Timeout) as error:
                last_error = error
                if attempt == max_retries - 1:
                    break
                time.sleep(2**attempt)

        raise RuntimeError(f"LLM API request failed after {max_retries} attempts: {last_error}")


def _text_from_response(data: Any) -> str:
    if not isinstance(data, dict):
        return ""

    content = data.get("content")
    if isinstance(content, list):
        chunks: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    chunks.append(text)
            elif isinstance(block, str):
                chunks.append(block)
        return "".join(chunks)

    if isinstance(content, str):
        return content

    text = data.get("text")
    return text if isinstance(text, str) else ""


def chat_client_from_env(env: Mapping[str, str] | None = None) -> AnthropicCompatibleChatClient:
    source = os.environ if env is None else env
    api_key = (
        source.get("PERSONAL_KNOWLEDGE_LLM_API_KEY")
        or source.get("BAILOU_API_KEY")
        or source.get("BAILIAN_API_KEY")
        or source.get("DASHSCOPE_API_KEY")
    )
    if api_key is None or api_key.strip() == "":
        raise ValueError(
            "Missing LLM API key. Set PERSONAL_KNOWLEDGE_LLM_API_KEY, BAILOU_API_KEY, "
            "BAILIAN_API_KEY, or DASHSCOPE_API_KEY."
        )

    return AnthropicCompatibleChatClient(
        api_key=api_key,
        base_url=source.get("PERSONAL_KNOWLEDGE_LLM_BASE_URL") or source.get("BAILOU_BASE_URL") or DEFAULT_BASE_URL,
    )
