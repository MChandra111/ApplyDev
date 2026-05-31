"""CLI: POST /api/analyze and print SSE events (Phase 4 smoke test)."""

import argparse
import json
import sys
from pathlib import Path

import httpx

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

SAMPLE_JD = """
Senior Frontend Engineer — Cloudflare
Requirements: React, TypeScript, Core Web Vitals, FastAPI, AWS, Docker.
Nice to have: LangGraph, RAG.
"""


def main() -> None:
    """Stream analyze endpoint events to stdout."""
    parser = argparse.ArgumentParser(description="Test POST /api/analyze SSE stream")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend base URL",
    )
    parser.add_argument(
        "--job-url",
        default="https://example.com/jobs/sample",
        help="Job URL sent to the API",
    )
    parser.add_argument(
        "--jd-text",
        action="store_true",
        help="Include sample JD text (skips scrape)",
    )
    parser.add_argument(
        "--company",
        default="Cloudflare",
        help="Company name when using --jd-text",
    )
    args = parser.parse_args()

    body: dict[str, str] = {"job_url": args.job_url}
    if args.jd_text:
        body["jd_text"] = SAMPLE_JD.strip()
        body["company_name"] = args.company

    url = f"{args.base_url.rstrip('/')}/api/analyze"
    print(f"POST {url}\n")

    job_id: str | None = None
    with httpx.Client(timeout=300.0) as client:
        with client.stream("POST", url, json=body) as response:
            if response.status_code != 200:
                print(response.read().decode())
                sys.exit(1)

            job_id = response.headers.get("x-job-id")
            print(f"X-Job-Id: {job_id}\n")

            buffer = ""
            for chunk in response.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    block, buffer = buffer.split("\n\n", 1)
                    for line in block.splitlines():
                        if line.startswith("data:"):
                            payload = json.loads(line[5:].strip())
                            node = payload.get("node")
                            status = payload.get("status")
                            print(f"  [{status:7}] {node}")
                            if status == "error":
                                print(f"           {payload.get('error')}")
                                sys.exit(1)

    if job_id:
        get_url = f"{args.base_url.rstrip('/')}/api/jobs/{job_id}"
        summary = httpx.get(get_url, timeout=30.0).json()
        print(f"\nGET {get_url}")
        print(f"  status={summary.get('status')}")
        score = (summary.get("result") or {}).get("opportunity_score") or {}
        if score:
            print(f"  score={score.get('score')}/10 recommendation={score.get('recommendation')}")


if __name__ == "__main__":
    main()
