"""Local embedder using Ollama."""

import requests
from typing import Optional


class LocalEmbedder:
    """Generate embeddings using local Ollama model."""

    def __init__(self, model: str = "qwen2.5-coder:7b", ollama_url: str = "http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        self.session = requests.Session()

    def check_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = self.session.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text using Ollama.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        url = f"{self.ollama_url}/api/embeddings"
        data = {
            "model": self.model,
            "prompt": text
        }

        response = self.session.post(url, json=data, timeout=60)
        result = response.json()

        if response.status_code == 200:
            return result.get("embedding", [])
        else:
            raise RuntimeError(f"Ollama error: {result}")

    def embed_batch(self, texts: list[str], batch_size: int = 5) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (smaller for local)

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for text in texts:
            try:
                embedding = self.embed(text)
                if embedding:
                    all_embeddings.append(embedding)
            except Exception as e:
                print(f"Error embedding text: {e}")
                continue

        return all_embeddings
