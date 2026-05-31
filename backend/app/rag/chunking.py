"""Split long documents into retrieval-friendly chunks."""

import re
from dataclasses import dataclass

from app.config import get_env

DEFAULT_CHUNK_SIZE = 600
DEFAULT_CHUNK_OVERLAP = 100


@dataclass(frozen=True)
class DocumentChunk:
    """One slice of a source file ready for embedding."""

    source: str
    chunk_index: int
    text: str


def get_chunk_settings() -> tuple[int, int]:
    """Read chunk size and overlap from environment variables."""
    size = int(get_env("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)) or DEFAULT_CHUNK_SIZE)
    overlap = int(
        get_env("CHUNK_OVERLAP", str(DEFAULT_CHUNK_OVERLAP)) or DEFAULT_CHUNK_OVERLAP,
    )
    return size, overlap


def chunk_text(source: str, text: str) -> list[DocumentChunk]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    chunk_size, overlap = get_chunk_settings()
    normalized = re.sub(r"\n{3,}", "\n\n", text.strip())
    if not normalized:
        return []

    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    raw_chunks: list[str] = []
    buffer = ""

    for paragraph in paragraphs:
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= chunk_size:
            buffer = candidate
            continue

        if buffer:
            raw_chunks.append(buffer)
        # Paragraph alone may still exceed chunk_size — hard-split long blocks
        if len(paragraph) > chunk_size:
            raw_chunks.extend(_hard_split(paragraph, chunk_size, overlap))
            buffer = ""
        else:
            buffer = paragraph

    if buffer:
        raw_chunks.append(buffer)

    if not raw_chunks:
        raw_chunks = _hard_split(normalized, chunk_size, overlap)

    return [
        DocumentChunk(source=source, chunk_index=index, text=chunk)
        for index, chunk in enumerate(raw_chunks)
    ]


def _hard_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Fall back to fixed-size windows when paragraphs are too large."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]
