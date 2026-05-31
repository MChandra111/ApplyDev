"""CLI: parse a sample job description and show per-skill RAG matches."""

import argparse
import json
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.jd_parser_agent import JDParserAgent
from app.config import configure_logging, load_project_env

SAMPLE_JD = """
Senior Frontend Engineer — Cloudflare

We're looking for a frontend engineer to build performant React dashboards used by
thousands of customers. You'll optimize bundle size and load times, collaborate with
API teams on FastAPI services, and deploy via Docker on AWS.

Requirements:
- 3+ years React and TypeScript
- Experience improving Core Web Vitals and load performance
- REST API integration experience
- Familiarity with vector search or RAG is a plus
- AWS and Docker in production

Nice to have: LangGraph, agentic AI systems, technical writing.
"""


def main() -> None:
    """Parse JD from file or built-in sample and print JSON matches."""
    parser = argparse.ArgumentParser(description="Run JDParserAgent (Phase 2)")
    parser.add_argument(
        "--file",
        type=Path,
        help="Path to a .txt job description (optional)",
    )
    args = parser.parse_args()

    load_project_env()
    configure_logging()

    jd_text = args.file.read_text(encoding="utf-8") if args.file else SAMPLE_JD
    print("\nParsing job description and running RAG per skill...\n")

    agent = JDParserAgent()
    result = agent.parse_and_match(jd_text)

    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
