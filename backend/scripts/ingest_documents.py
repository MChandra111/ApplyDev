"""Ingest documents/*.txt into Pinecone (chunk → embed → upsert)."""

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import configure_logging, get_documents_dir, load_project_env
from app.rag.chunking import chunk_text
from app.rag.pinecone_store import ensure_index_exists, upsert_chunks


def load_text_files(documents_dir: Path) -> list[tuple[str, str]]:
    """Read every .txt file in the documents folder."""
    files = sorted(documents_dir.glob("*.txt"))
    if not files:
        msg = f"No .txt files found in {documents_dir}"
        raise FileNotFoundError(msg)
    return [(path.name, path.read_text(encoding="utf-8")) for path in files]


def main() -> None:
    """Chunk all documents, embed them, and upsert vectors to Pinecone."""
    load_project_env()
    configure_logging()

    documents_dir = get_documents_dir()
    print(f"\nIngesting from: {documents_dir}\n")

    ensure_index_exists()

    all_chunks = []
    for filename, content in load_text_files(documents_dir):
        chunks = chunk_text(filename, content)
        print(f"  {filename}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    total = upsert_chunks(all_chunks)
    print(f"\nDone — upserted {total} vectors.\n")


if __name__ == "__main__":
    main()
