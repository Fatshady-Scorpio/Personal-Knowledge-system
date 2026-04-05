"""Text embedder using Alibaba Cloud Bailian API."""

import requests
from typing import Optional


class Embedder:
    """Generate text embeddings using Bailian API."""

    def __init__(self, api_key: str, model: str = "text-embedding-v2"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/generation"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        data = {
            "model": self.model,
            "input": {"texts": [text]}
        }

        response = self.session.post(self.base_url, json=data)
        result = response.json()

        if response.status_code == 200:
            embeddings = result.get("output", {}).get("embeddings", [])
            if embeddings:
                return embeddings[0].get("embedding", [])
        else:
            error = result.get("error", {})
            raise RuntimeError(f"API error: {error.get('code')} - {error.get('message')}")

        return []

    def embed_batch(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            data = {
                "model": self.model,
                "input": {"texts": batch}
            }

            response = self.session.post(self.base_url, json=data)
            result = response.json()

            if response.status_code == 200:
                embeddings = result.get("output", {}).get("embeddings", [])
                for emb in embeddings:
                    all_embeddings.append(emb.get("embedding", []))

        return all_embeddings
