"""CLI script to run the Phase 1 ResearchAgent (learning / manual test)."""

import argparse
import json
import sys
from pathlib import Path

# Allow `python scripts/run_research_agent.py` from the backend/ directory
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.research_agent import ResearchAgent
from app.config import configure_logging, load_project_env


def main() -> None:
    """Parse CLI args, run research, and print structured JSON to stdout."""
    parser = argparse.ArgumentParser(
        description="Run ApplyDev ResearchAgent (Phase 1)",
    )
    parser.add_argument(
        "company",
        nargs="?",
        default="Stripe",
        help="Company name to research (default: Stripe)",
    )
    args = parser.parse_args()

    load_project_env()
    configure_logging()

    print(f"\nResearching: {args.company}\n")
    print("Watch the logs below — each 'Tool call' is the LLM choosing to search.\n")

    agent = ResearchAgent()
    summary = agent.research(args.company)

    print("\n--- Final structured output ---\n")
    print(json.dumps(summary.model_dump(), indent=2))


if __name__ == "__main__":
    main()
