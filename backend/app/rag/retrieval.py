"""Retrieve resume/project chunks similar to a skill or JD requirement."""

import logging
from typing import TypedDict

from app.rag.embeddings import embed_texts
from app.rag.pinecone_store import get_index

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 3


class RetrievedChunk(TypedDict):
    """One chunk returned from vector search."""

    text: str
    source: str
    score: float
    chunk_index: int


def retrieve_experience(query: str, top_k: int = DEFAULT_TOP_K) -> list[RetrievedChunk]:
    """Return the top matching resume/project chunks for a skill or requirement."""
    logger.debug("retrieve_experience INPUT query=%r top_k=%s", query, top_k)

    query_vector = embed_texts([query], input_type="query")[0]
    index = get_index()
    response = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True,
    )

    results: list[RetrievedChunk] = []
    for match in response.get("matches", []):
        metadata = match.get("metadata") or {}
        results.append(
            RetrievedChunk(
                text=str(metadata.get("text", "")),
                source=str(metadata.get("source", "unknown")),
                score=float(match.get("score") or 0.0),
                chunk_index=int(metadata.get("chunk_index", -1)),
            ),
        )

    logger.debug("retrieve_experience OUTPUT %s matches", len(results))
    return results
