"""Tavily web search — the ResearchAgent's only Phase 1 tool."""

import json
import logging
from typing import Any

from tavily import TavilyClient

from app.config import get_required_env

logger = logging.getLogger(__name__)

# OpenAI-compatible tool schema sent to Groq so the model knows when/how to search
TAVILY_TOOL_DEFINITION: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "tavily_web_search",
        "description": (
            "Search the public web for up-to-date information about a company: "
            "size, news, technology stack, and potential red flags. "
            "Call this when you need facts you do not already have."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Specific search query, e.g. 'Stripe company size 2025' "
                        "or 'Anthropic layoffs news'"
                    ),
                },
            },
            "required": ["query"],
        },
    },
}


def tavily_web_search(query: str, max_results: int = 5) -> str:
    """Run a Tavily search and return a compact JSON string for the LLM context."""
    logger.debug("Tavily tool INPUT query=%r max_results=%s", query, max_results)

    client = TavilyClient(api_key=get_required_env("TAVILY_API_KEY"))
    response = client.search(query=query, max_results=max_results, include_answer=True)

    # Keep payload small — the model only needs titles, snippets, and Tavily's summary
    simplified: list[dict[str, str]] = []
    for item in response.get("results", []):
        simplified.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": (item.get("content") or "")[:500],
            },
        )

    payload = {
        "query": query,
        "answer": response.get("answer", ""),
        "results": simplified,
    }
    result_json = json.dumps(payload, indent=2)
    logger.debug("Tavily tool OUTPUT (truncated): %s", result_json[:1500])
    return result_json
