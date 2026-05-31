"""CLI: run the full LangGraph pipeline on a job URL (Phase 3)."""

import argparse
import json
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import configure_logging, load_project_env
from app.graph.pipeline import run_pipeline
from app.graph.state import PipelineState

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
    """Run the ApplyDev LangGraph pipeline and print final JSON."""
    parser = argparse.ArgumentParser(
        description="Run full ApplyDev LangGraph pipeline (Phase 3)",
    )
    parser.add_argument(
        "job_url",
        nargs="?",
        default="https://example.com/jobs/sample",
        help="Job posting URL to scrape (optional if --jd-file is used)",
    )
    parser.add_argument(
        "--jd-file",
        type=Path,
        help="Use local JD text instead of scraping (recommended for first test)",
    )
    parser.add_argument(
        "--company",
        default="Cloudflare",
        help="Company name for research when using --jd-file",
    )
    args = parser.parse_args()

    load_project_env()
    configure_logging()

    initial: PipelineState = {
        "job_url": args.job_url,
        "agent_logs": [],
    }

    if args.jd_file:
        initial["jd_text"] = args.jd_file.read_text(encoding="utf-8")
        initial["company_name"] = args.company
        print(f"Using JD file: {args.jd_file} (company={args.company})\n")
    else:
        print(f"Scraping job URL: {args.job_url}\n")
        print(
            "Tip: many sites block bots. If scrape fails, rerun with "
            "--jd-file path/to/jd.txt --company 'Company Name'\n",
        )

    # Offline-friendly default when no args beyond defaults
    if args.job_url == "https://example.com/jobs/sample" and not args.jd_file:
        initial["jd_text"] = SAMPLE_JD.strip()
        initial["company_name"] = args.company
        print("Using built-in sample JD (pass a real URL or --jd-file to override)\n")

    print("Running LangGraph pipeline (6 nodes)...\n")
    final = run_pipeline(initial)

    print("--- Agent logs (in order) ---")
    for entry in final.get("agent_logs", []):
        print(f"  • {entry}")

    print("\n--- Opportunity score ---")
    score = final.get("opportunity_score") or {}
    print(json.dumps(score, indent=2))

    print("\n--- Resume bullets ---")
    for bullet in final.get("resume_bullets") or []:
        print(f"  • {bullet}")

    print("\n--- Cover letter (preview) ---")
    letter = final.get("cover_letter") or ""
    print(letter[:500] + ("..." if len(letter) > 500 else ""))

    print("\n--- Full state (JSON) ---")
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    main()
