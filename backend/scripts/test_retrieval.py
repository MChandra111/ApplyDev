"""Phase 2 acceptance test: React performance query should surface Heirmeios."""

import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import configure_logging, load_project_env
from app.rag.retrieval import retrieve_experience

TEST_QUERY = "React performance optimization"
EXPECTED_MARKERS = ("heirmeios", "load time", "38%")


def main() -> None:
    """Run the canonical Phase 2 retrieval test and print results."""
    load_project_env()
    configure_logging()

    print(f'\nQuery: "{TEST_QUERY}"\n')
    results = retrieve_experience(TEST_QUERY)

    if not results:
        print("FAIL — no results returned. Did you run ingest_documents.py?")
        sys.exit(1)

    for rank, item in enumerate(results, start=1):
        preview = item["text"][:160].replace("\n", " ")
        print(f"{rank}. score={item['score']:.3f} source={item['source']}")
        print(f"   {preview}...\n")

    combined = " ".join(item["text"].lower() for item in results)
    if any(marker in combined for marker in EXPECTED_MARKERS):
        print("PASS — retrieval includes Heirmeios / load-time evidence.")
        return

    print("FAIL — expected Heirmeios performance content in top 3 chunks.")
    sys.exit(1)


if __name__ == "__main__":
    main()
