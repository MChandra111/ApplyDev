"""Single-agent company research with Tavily tool calling (Phase 1)."""

import json
import logging
from typing import Any

from groq import Groq
from pydantic import ValidationError

from app.config import get_required_env
from app.models.research_summary import ResearchSummary
from app.tools.tavily_search import TAVILY_TOOL_DEFINITION, tavily_web_search

logger = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_AGENT_ITERATIONS = 8

RESEARCH_AGENT_SYSTEM_PROMPT = """You are a company research analyst helping a job seeker evaluate employers.

You have one tool: tavily_web_search. Use it to find current facts about the company the user names.
Search multiple times if needed (size, recent news, tech stack, controversies).

When you have enough information, respond with ONLY valid JSON matching this schema (no markdown):
{
  "company_name": "string",
  "company_size": "string — employees, funding stage, or market cap if known",
  "recent_news": ["string", "..."],
  "tech_stack_mentions": ["string", "..."],
  "red_flags": ["string", "..."] 
}

If no red flags exist, use an empty array. Base every field on search results; say "Unknown" rather than inventing."""

RESEARCH_AGENT_USER_PROMPT = """Research this company for a job application: {company_name}

Steps:
1. Search for company size and business overview.
2. Search for recent news (last 12 months).
3. Search for engineering / tech stack mentions.
4. Search for layoffs, lawsuits, or negative press.

Then output the JSON summary."""


class ResearchAgent:
    """Runs an observe → think → act loop with Groq + Tavily until JSON is ready."""

    def __init__(self) -> None:
        """Create a Groq client using GROQ_API_KEY from the environment."""
        self._client = Groq(api_key=get_required_env("GROQ_API_KEY"))
        self._tools = [TAVILY_TOOL_DEFINITION]

    def research(self, company_name: str) -> ResearchSummary:
        """Research a company and return a validated structured summary."""
        logger.debug("ResearchAgent INPUT company_name=%r", company_name)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": RESEARCH_AGENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": RESEARCH_AGENT_USER_PROMPT.format(
                    company_name=company_name,
                ),
            },
        ]

        for iteration in range(1, MAX_AGENT_ITERATIONS + 1):
            logger.debug("Agent loop iteration %s", iteration)
            response = self._client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                tools=self._tools,
                tool_choice="auto",
                temperature=0.2,
            )
            assistant_message = response.choices[0].message
            logger.debug(
                "LLM response: content=%r tool_calls=%s",
                assistant_message.content,
                [tc.function.name for tc in (assistant_message.tool_calls or [])],
            )

            # --- ACT: model requested tool calls ---
            if assistant_message.tool_calls:
                messages.append(self._assistant_message_to_dict(assistant_message))

                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    raw_args = tool_call.function.arguments or "{}"
                    logger.info("Tool call: %s args=%s", tool_name, raw_args)

                    tool_result = self._execute_tool(tool_name, raw_args)
                    logger.info("Tool result length: %s chars", len(tool_result))

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": tool_result,
                        },
                    )
                continue

            # --- DONE: model returned text (hopefully JSON) ---
            if not assistant_message.content:
                msg = "Model finished without content or tool calls."
                raise RuntimeError(msg)

            summary = self._parse_summary(assistant_message.content, company_name)
            logger.debug("ResearchAgent OUTPUT %s", summary.model_dump())
            return summary

        msg = f"Agent exceeded {MAX_AGENT_ITERATIONS} iterations without finishing."
        raise RuntimeError(msg)

    def _execute_tool(self, tool_name: str, raw_args: str) -> str:
        """Dispatch a tool call from the model to the matching Python function."""
        if tool_name != "tavily_web_search":
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

        try:
            args = json.loads(raw_args)
            query = args.get("query", "")
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON in tool arguments"})

        if not query:
            return json.dumps({"error": "Missing required argument: query"})

        return tavily_web_search(query)

    def _assistant_message_to_dict(self, message: Any) -> dict[str, Any]:
        """Convert a Groq assistant message (with tool_calls) into chat history format."""
        tool_calls_payload = []
        for tc in message.tool_calls or []:
            tool_calls_payload.append(
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                },
            )
        return {
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": tool_calls_payload,
        }

    def _parse_summary(self, content: str, company_name: str) -> ResearchSummary:
        """Parse and validate the model's final JSON against ResearchSummary."""
        text = content.strip()
        # Models sometimes wrap JSON in markdown fences despite instructions
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        try:
            return ResearchSummary.model_validate_json(text)
        except ValidationError as exc:
            logger.warning("JSON validation failed, retrying parse: %s", exc)
            data = json.loads(text)
            data.setdefault("company_name", company_name)
            return ResearchSummary.model_validate(data)
