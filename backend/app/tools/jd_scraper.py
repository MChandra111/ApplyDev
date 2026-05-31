"""Fetch and clean job posting text from a URL (Phase 3 scrape_jd node)."""

import logging
import re

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; ApplyDev/1.0; +https://github.com/applydev)"
    ),
    "Accept": "text/html,application/xhtml+xml",
}


def fetch_job_posting_text(url: str, timeout_seconds: float = 30.0) -> str:
    """Download a job posting URL and return cleaned plain text."""
    logger.debug("Fetching job URL: %s", url)
    with httpx.Client(
        follow_redirects=True,
        timeout=timeout_seconds,
        headers=_DEFAULT_HEADERS,
    ) as client:
        response = client.get(url)
        response.raise_for_status()

    return html_to_plain_text(response.text)


def html_to_plain_text(html: str) -> str:
    """Strip scripts/styles and collapse whitespace from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    collapsed = "\n".join(lines)
    # Cap size sent to LLMs later — most JD signal is in the first ~12k chars
    return collapsed[:12000]


def guess_company_name(url: str, page_text: str) -> str:
    """Infer company name from URL host or common title patterns."""
    host_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if host_match:
        host = host_match.group(1).lower()
        if host not in {"www.linkedin.com", "linkedin.com", "jobs.lever.co"}:
            label = host.split(".")[0]
            if label not in {"jobs", "careers", "apply"}:
                return label.replace("-", " ").title()

    title_line = page_text.split("\n", 1)[0] if page_text else ""
    at_match = re.search(r"\bat\s+([A-Za-z0-9][A-Za-z0-9 .&'-]{1,40})", title_line)
    if at_match:
        return at_match.group(1).strip()

    dash_match = re.search(
        r"^(.{2,60}?)\s+[-–|]\s+",
        title_line,
        re.IGNORECASE,
    )
    if dash_match:
        return dash_match.group(1).strip()

    return "Unknown Company"
