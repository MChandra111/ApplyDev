"""Generate vector embeddings via Pinecone Inference API."""

import logging
from typing import Literal

from pinecone import Pinecone

from app.config import get_env, get_required_env

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "llama-text-embed-v2"
DEFAULT_EMBEDDING_DIMENSION = 1024
EMBED_BATCH_SIZE = 32

InputType = Literal["query", "passage"]


def get_embedding_model() -> str:
    """Return the Pinecone-hosted embedding model name from the environment."""
    return get_env("EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL) or DEFAULT_EMBEDDING_MODEL


def get_embedding_dimension() -> int:
    """Return vector dimension used when creating the Pinecone index."""
    raw = get_env("EMBEDDING_DIMENSION", str(DEFAULT_EMBEDDING_DIMENSION))
    return int(raw or DEFAULT_EMBEDDING_DIMENSION)


def embed_texts(texts: list[str], input_type: InputType) -> list[list[float]]:
    """Embed a batch of strings; use 'passage' for documents and 'query' for search."""
    if not texts:
        return []

    logger.debug(
        "Embedding %s texts with model=%s input_type=%s",
        len(texts),
        get_embedding_model(),
        input_type,
    )

    client = Pinecone(api_key=get_required_env("PINECONE_API_KEY"))
    model = get_embedding_model()
    all_vectors: list[list[float]] = []

    for start in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[start : start + EMBED_BATCH_SIZE]
        response = client.inference.embed(
            model=model,
            inputs=batch,
            parameters={
                "input_type": input_type,
                "truncate": "END",
                "dimension": get_embedding_dimension(),
            },
        )
        for item in response.data:
            values = item["values"] if isinstance(item, dict) else item.values
            all_vectors.append(list(values))

    return all_vectors
