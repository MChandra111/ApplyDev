"""Score a job opportunity 1-10 with structured reasoning."""

import json
import logging

from groq import Groq
from pydantic import ValidationError

from app.agents.research_agent import GROQ_MODEL
from app.config import get_required_env
from app.models.jd_parse import JDParseResult
from app.models.pipeline_outputs import OpportunityScore
from app.models.research_summary import ResearchSummary

logger = logging.getLogger(__name__)

EVAL_AGENT_SYSTEM_PROMPT = """You evaluate job opportunities for a recent grad targeting SWE/AI Engineer roles.

Score overall fit from 1 (poor) to 10 (excellent) using:
- Skill overlap with provided resume matches
- Company stability and growth signals from research
- Red flags (layoffs, mismatched seniority, vague JD)

Return ONLY valid JSON:
{
  "score": 1-10,
  "fit_summary": "2-3 sentences",
  "growth_summary": "2-3 sentences",
  "red_flags_summary": "2-3 sentences",
  "recommendation": "apply | maybe | pass"
}"""

EVAL_AGENT_USER_PROMPT = """Role: {job_title} at {company_name}

Research:
{research_json}

Skill matches (resume evidence):
{matches_json}

Resume bullets drafted:
{bullets_json}

Cover letter excerpt (first 400 chars):
{cover_excerpt}

Evaluate this opportunity."""


class EvalAgent:
    """Scores fit, growth, and risk for a job application opportunity."""

    def __init__(self) -> None:
        """Create a Groq client using GROQ_API_KEY from the environment."""
        self._client = Groq(api_key=get_required_env("GROQ_API_KEY"))

    def evaluate(
        self,
        company_name: str,
        research: ResearchSummary,
        jd_parse: JDParseResult,
        bullets: list[str],
        cover_letter: str,
    ) -> OpportunityScore:
        """Return a 1-10 score with reasoning breakdown."""
        logger.debug("EvalAgent INPUT company=%r", company_name)
        messages = [
            {"role": "system", "content": EVAL_AGENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": EVAL_AGENT_USER_PROMPT.format(
                    job_title=jd_parse.job_title,
                    company_name=company_name,
                    research_json=research.model_dump_json(indent=2),
                    matches_json=jd_parse.model_dump_json(indent=2),
                    bullets_json=json.dumps(bullets, indent=2),
                    cover_excerpt=cover_letter[:400],
                ),
            },
        ]
        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.2,
        )
        content = response.choices[0].message.content or ""
        logger.debug("EvalAgent raw output: %s", content[:600])
        score = self._parse_score(content)
        logger.debug("EvalAgent OUTPUT score=%s", score.score)
        return score

    def _parse_score(self, content: str) -> OpportunityScore:
        """Parse and validate eval JSON."""
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()
        try:
            return OpportunityScore.model_validate_json(text)
        except ValidationError as exc:
            logger.warning("Eval JSON validation failed: %s", exc)
            data = json.loads(text)
            return OpportunityScore.model_validate(data)
