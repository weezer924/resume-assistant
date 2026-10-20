from collections.abc import Awaitable, Callable

from openai import AsyncOpenAI

# Any async callable with this shape can stand in for the real embedder in tests.
Embedder = Callable[[list[str]], Awaitable[list[list[float]]]]


class OpenAIEmbedder:
    """Turn texts into vectors with the OpenAI Embeddings API, preserving order."""

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self.client: AsyncOpenAI = client
        self.model: str = model

    async def __call__(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        # Batch
        response = await self.client.embeddings.create(model=self.model, input=texts)

        # Guardrail: The API echoes each input's position as `index`; sort on it rather than
        # trusting response order, so a reordered response cannot mislabel a fact.
        vectors = [
            item.embedding for item in sorted(response.data, key=lambda d: d.index)
        ]
        if len(vectors) != len(texts):
            raise RuntimeError(f"expected {len(texts)} vectors, got {len(vectors)}")

        return vectors
