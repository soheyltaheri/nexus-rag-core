import hashlib
import logging
from abc import ABC, abstractmethod
from typing import cast

import httpx

from app.core.config import settings
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)


class LLMProviderInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, context: str) -> str:
        """Generate response given prompt and retrieved context."""
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> list[float]:
        """Generate dense vector embedding for text."""
        pass


def deterministic_mock_embedding(text: str, dim: int = 1536) -> list[float]:
    """Generate normalized pseudo-random embedding vector from text hash."""
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
    vector = []
    for _i in range(dim):
        # Linear congruential generation
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        vector.append((seed / 0x7FFFFFFF) * 2 - 1)
    # Normalize vector to unit length
    norm = sum(x * x for x in vector) ** 0.5
    return [x / norm for x in vector] if norm > 0 else vector


class OpenAILLMProvider(LLMProviderInterface):
    """OpenAI API integration with resilience and test-mode simulation."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_embedding(self, text: str) -> list[float]:
        if settings.APP_ENV == "testing" or self.api_key in ("mock-key", "mock-test-key", None):
            return deterministic_mock_embedding(text, settings.EMBEDDING_DIMENSION)

        try:
            response = await self.client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.EMBEDDING_MODEL,
                    "input": text,
                },
            )
            response.raise_for_status()
            data = response.json()
            return cast(list[float], data["data"][0]["embedding"])
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise LLMServiceError(f"Embedding generation failed: {e}") from e

    async def generate(self, prompt: str, context: str) -> str:
        if settings.APP_ENV == "testing" or self.api_key in ("mock-key", "mock-test-key", None):
            return f"[Simulated Response] Based on context: '{context[:80]}...', the answer to '{prompt}' is verified."

        try:
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENAI_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are an enterprise AI assistant. Answer accurately "
                                "and strictly based on the provided context.\n\n"
                                f"Context:\n{context}"
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            data = response.json()
            return cast(str, data["choices"][0]["message"]["content"])
        except Exception as e:
            logger.error(f"Failed to generate chat completion: {e}")
            raise LLMServiceError(f"LLM generation failed: {e}") from e

    async def aclose(self) -> None:
        await self.client.aclose()
