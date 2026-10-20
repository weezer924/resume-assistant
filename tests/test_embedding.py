from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from openai import AsyncOpenAI

from app.services.embedding import OpenAIEmbedder


def fake_response(vectors: list[list[float]]) -> SimpleNamespace:
    # Shape of the real response: response.data[i].embedding, response.data[i].index
    return SimpleNamespace(
        data=[SimpleNamespace(index=i, embedding=v) for i, v in enumerate(vectors)]
    )


def client_with(create: AsyncMock) -> MagicMock:
    client = MagicMock(spec=AsyncOpenAI)
    client.embeddings = SimpleNamespace(create=create)
    return client


async def test_embedder_returns_one_vector_per_text_in_order():
    create = AsyncMock(return_value=fake_response([[1.0, 0.0], [0.0, 1.0]]))
    embedder = OpenAIEmbedder(client_with(create), "test-embedding-model")

    vectors = await embedder(["first", "second"])

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    create.assert_awaited_once_with(
        model="test-embedding-model", input=["first", "second"]
    )


async def test_embedder_sorts_by_index_when_response_is_out_of_order():
    create = AsyncMock(
        return_value=SimpleNamespace(
            data=[
                SimpleNamespace(index=1, embedding=[0.0, 1.0]),
                SimpleNamespace(index=0, embedding=[1.0, 0.0]),
            ]
        )
    )
    embedder = OpenAIEmbedder(client_with(create), "test-embedding-model")

    assert await embedder(["first", "second"]) == [[1.0, 0.0], [0.0, 1.0]]


async def test_embedder_empty_input_skips_api_call():
    create = AsyncMock(return_value=fake_response([]))
    embedder = OpenAIEmbedder(client_with(create), "test-embedding-model")

    assert await embedder([]) == []
    create.assert_not_awaited()


async def test_embedder_rejects_count_mismatch():
    create = AsyncMock(return_value=fake_response([[1.0, 0.0]]))  # 1 vector, 2 texts
    embedder = OpenAIEmbedder(client_with(create), "test-embedding-model")

    with pytest.raises(RuntimeError, match="expected 2 vectors, got 1"):
        _ = await embedder(["a", "b"])


async def test_embedder_propagates_api_errors():
    create = AsyncMock(side_effect=RuntimeError("Synthetic API failure"))
    embedder = OpenAIEmbedder(client_with(create), "test-embedding-model")

    with pytest.raises(RuntimeError, match="Synthetic API failure"):
        _ = await embedder(["a"])
