"""Pinecone index lifecycle: create, upsert chunks, and query vectors."""

import logging
import time

from pinecone import Pinecone, ServerlessSpec

from app.config import get_env, get_required_env
from app.rag.chunking import DocumentChunk
from app.rag.embeddings import embed_texts, get_embedding_dimension, get_embedding_model

logger = logging.getLogger(__name__)


def get_index_name() -> str:
    """Return the Pinecone index name from the environment."""
    return get_env("PINECONE_INDEX_NAME", "applydev-resume") or "applydev-resume"


def get_pinecone_client() -> Pinecone:
    """Create a Pinecone client using PINECONE_API_KEY."""
    return Pinecone(api_key=get_required_env("PINECONE_API_KEY"))


def ensure_index_exists() -> None:
    """Create the serverless index if this project has not created it yet."""
    client = get_pinecone_client()
    name = get_index_name()
    if client.has_index(name):
        logger.info("Pinecone index already exists: %s", name)
        return

    cloud = get_env("PINECONE_CLOUD", "aws") or "aws"
    region = get_env("PINECONE_REGION", "us-east-1") or "us-east-1"
    dimension = get_embedding_dimension()

    logger.info(
        "Creating Pinecone index %s (dim=%s, model=%s, region=%s)",
        name,
        dimension,
        get_embedding_model(),
        region,
    )
    client.create_index(
        name=name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud=cloud, region=region),
    )
    _wait_until_ready(client, name)


def _wait_until_ready(client: Pinecone, name: str, timeout_seconds: int = 120) -> None:
    """Poll until Pinecone reports the new index is ready for upserts."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        description = client.describe_index(name)
        if description.status.get("ready"):
            return
        time.sleep(2)
    msg = f"Timed out waiting for Pinecone index '{name}' to become ready."
    raise TimeoutError(msg)


def get_index():
    """Return a handle to the Pinecone index for upsert/query operations."""
    client = get_pinecone_client()
    return client.Index(get_index_name())


def upsert_chunks(chunks: list[DocumentChunk]) -> int:
    """Embed document chunks and upsert them into Pinecone with metadata."""
    if not chunks:
        return 0

    texts = [chunk.text for chunk in chunks]
    vectors = embed_texts(texts, input_type="passage")
    index = get_index()

    records: list[dict] = []
    for chunk, values in zip(chunks, vectors, strict=True):
        records.append(
            {
                "id": f"{chunk.source}::chunk-{chunk.chunk_index}",
                "values": values,
                "metadata": {
                    "source": chunk.source,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                },
            },
        )

    # Pinecone recommends batching large upserts
    batch_size = 50
    for start in range(0, len(records), batch_size):
        index.upsert(vectors=records[start : start + batch_size])

    logger.info("Upserted %s vectors into index %s", len(records), get_index_name())
    return len(records)
