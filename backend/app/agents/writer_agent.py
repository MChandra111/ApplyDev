"""Generate tailored resume bullets and cover letter from pipeline context."""

import json
import logging

from groq import Groq
from pydantic import BaseModel, Field, ValidationError

from app.agents.research_agent import GROQ_MODEL
from app.config import get_required_env
from app.models.jd_parse import JDParseResult
from app.models.research_summary import ResearchSummary

logger = logging.getLogger(__name__)

RESUME_BULLETS_SYSTEM_PROMPT = """You are a resume writer for a junior/mid software engineer breaking into SWE/AI roles.

Given company research, parsed job requirements, and retrieved resume evidence, write 4-6 tailored resume bullets.

Rules:
- Start each bullet with a strong past-tense verb (Built, Optimized, Designed, …).
- Quantify when the evidence includes numbers; never invent metrics.
- Mirror keywords from the job description naturally.
- Each bullet must be one sentence, <= 28 words.
- Return ONLY valid JSON: {"bullets": ["...", "..."]}"""

RESUME_BULLETS_USER_PROMPT = """Job title: {job_title}
Company context: {company_context}

Company research (JSON):
{research_json}

Matched resume evidence (JSON):
{matches_json}

Write tailored bullets grounded in the evidence."""

COVER_LETTER_SYSTEM_PROMPT = """You write concise, professional cover letters for software engineering applications.

Structure exactly 3 paragraphs:
1) Hook — role + why this company (use research facts)
2) Proof — 2-3 accomplishments tied to JD skills (use provided evidence)
3) Close — enthusiasm + call to action

Tone: confident, specific, not flowery. 220-320 words total.
Return ONLY valid JSON: {"cover_letter": "full letter as one string"}
Use the two-character sequence \\n between paragraphs (no literal line breaks inside the JSON)."""

COVER_LETTER_USER_PROMPT = """Candidate: Maheshwar Chandra — React, Python, FastAPI, RAG/agentic AI, AWS CP

Role: {job_title} at {company_name}

Resume bullets already drafted:
{bullets_json}

Research summary:
{research_json}

Key skill matches:
{matches_json}

Write the cover letter."""


class _BulletsPayload(BaseModel):
    bullets: list[str] = Field(min_length=4, max_length=8)


class _CoverLetterPayload(BaseModel):
    cover_letter: str


class WriterAgent:
    """Produces resume bullets and cover letter from graph state context."""

    def __init__(self) -> None:
        """Create a Groq client using GROQ_API_KEY from the environment."""
        self._client = Groq(api_key=get_required_env("GROQ_API_KEY"))

    def write_resume_bullets(
        self,
        research: ResearchSummary,
        jd_parse: JDParseResult,
    ) -> list[str]:
        """Generate 4-6 tailored resume bullets."""
        logger.debug(
            "WriterAgent.write_resume_bullets job_title=%r",
            jd_parse.job_title,
        )
        messages = [
            {"role": "system", "content": RESUME_BULLETS_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": RESUME_BULLETS_USER_PROMPT.format(
                    job_title=jd_parse.job_title,
                    company_context=jd_parse.company_context,
                    research_json=research.model_dump_json(indent=2),
                    matches_json=jd_parse.model_dump_json(indent=2),
                ),
            },
        ]
        content = self._chat(messages)
        payload = self._parse_json(content, _BulletsPayload)
        logger.debug("WriterAgent bullets count=%s", len(payload.bullets))
        return payload.bullets[:6]

    def write_cover_letter(
        self,
        company_name: str,
        research: ResearchSummary,
        jd_parse: JDParseResult,
        bullets: list[str],
    ) -> str:
        """Draft a three-paragraph cover letter."""
        logger.debug(
            "WriterAgent.write_cover_letter company=%r",
            company_name,
        )
        messages = [
            {"role": "system", "content": COVER_LETTER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": COVER_LETTER_USER_PROMPT.format(
                    job_title=jd_parse.job_title,
                    company_name=company_name,
                    bullets_json=json.dumps(bullets, indent=2),
                    research_json=research.model_dump_json(indent=2),
                    matches_json=jd_parse.model_dump_json(indent=2),
                ),
            },
        ]
        content = self._chat(messages)
        payload = self._parse_json(content, _CoverLetterPayload)
        return payload.cover_letter.strip()

    def _chat(self, messages: list[dict[str, str]]) -> str:
        """Run one Groq completion and return assistant text."""
        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""

    def _parse_json(self, content: str, model: type[BaseModel]) -> BaseModel:
        """Strip markdown fences and validate JSON against a Pydantic model."""
        text = _strip_json_fences(content)
        try:
            return model.model_validate_json(text)
        except ValidationError:
            pass
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = json.loads(_escape_newlines_in_json_strings(text))
        if model is _CoverLetterPayload and isinstance(data.get("cover_letter"), str):
            data["cover_letter"] = data["cover_letter"].replace("\\n", "\n")
        return model.model_validate(data)


def _strip_json_fences(content: str) -> str:
    """Remove markdown code fences around model JSON."""
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            line for line in lines if not line.strip().startswith("```")
        ).strip()
    return text


def _escape_newlines_in_json_strings(raw: str) -> str:
    """Repair LLM JSON where string values contain unescaped line breaks."""
    out: list[str] = []
    in_string = False
    escape = False
    for char in raw:
        if escape:
            out.append(char)
            escape = False
            continue
        if char == "\\" and in_string:
            escape = True
            out.append(char)
            continue
        if char == '"':
            in_string = not in_string
            out.append(char)
            continue
        if in_string and char in "\n\r":
            out.append("\\n" if char == "\n" else "\\r")
            continue
        out.append(char)
    return "".join(out)
