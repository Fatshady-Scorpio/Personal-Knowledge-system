import pytest

from personal_knowledge.llm import AnthropicCompatibleChatClient, chat_client_from_env


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self._data = data or {"content": [{"type": "text", "text": "ok"}]}

    def json(self):
        return self._data


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self.response


def test_anthropic_compatible_chat_client_posts_messages():
    session = FakeSession(FakeResponse(data={"content": [{"type": "text", "text": "hello"}]}))
    client = AnthropicCompatibleChatClient(api_key="key", base_url="https://example.test/v1", session=session)

    text = client.call(model="model-a", messages=[{"role": "user", "content": "hi"}], max_tokens=10)

    assert text == "hello"
    assert session.calls[0]["url"] == "https://example.test/v1/messages"
    assert session.calls[0]["headers"]["Authorization"] == "Bearer key"
    assert session.calls[0]["json"]["model"] == "model-a"


def test_chat_client_from_env_uses_personal_knowledge_keys():
    client = chat_client_from_env(
        {
            "PERSONAL_KNOWLEDGE_LLM_API_KEY": "pk-key",
            "PERSONAL_KNOWLEDGE_LLM_BASE_URL": "https://llm.test",
        }
    )

    assert client.api_key == "pk-key"
    assert client.base_url == "https://llm.test"


def test_chat_client_from_env_requires_key():
    with pytest.raises(ValueError, match="Missing LLM API key"):
        chat_client_from_env({})
