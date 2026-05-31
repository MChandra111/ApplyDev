"""LLM-as-judge for comparing generated resume bullets to golden examples (Phase 6)."""

import json
import logging

from groq import Groq
from pydantic import ValidationError

from app.agents.research_agent import GROQ_MODEL
from app.config import get_required_env
from app.models.bullet_eval import BulletJudgeScores

logger = logging.getLogger(__name__)

BULLET_JUDGE_SYSTEM_PROMPT = """You are an expert resume coach evaluating AI-generated resume bullets for a junior SWE/AI candidate.

Compare the GENERATED bullets to the IDEAL reference bullets and the job description.
Score each dimension from 1 (poor) to 5 (excellent):

- relevance: Do generated bullets match the role requirements and cite real evidence (not invented)?
- specificity: Are there concrete tools, metrics, and outcomes (avoid vague "worked on" phrasing)?
- keyword_match: Do bullets naturally include important JD keywords without stuffing?

Rules:
- Penalize invented metrics or companies not supported by the ideal bullets / JD context.
- Reward bullets that mirror the ideal bullets' themes even if wording differs.
- Do not score grammar alone; focus on hiring-manager usefulness.

Return ONLY valid JSON:
{
  "relevance": 1-5,
  "specificity": 1-5,
  "keyword_match": 1-5,
  "reasoning": "2-4 sentences"
}"""

BULLET_JUDGE_USER_PROMPT = """Role: {job_title} at {company_name}

Job description excerpt:
{jd_excerpt}

IDEAL reference bullets (human-written gold standard):
{ideal_json}

GENERATED bullets (from the ApplyDev pipeline):
{generated_json}

Score the GENERATED set."""


class BulletJudgeAgent:
    """Scores generated resume bullets against ideal examples using an LLM judge."""

    def __init__(self) -> None:
        """Create a Groq client using GROQ_API_KEY from the environment."""
        self._client = Groq(api_key=get_required_env("GROQ_API_KEY"))

    def score_bullets(
        self,
        job_title: str,
        company_name: str,
        jd_text: str,
        ideal_bullets: list[str],
        generated_bullets: list[str],
    ) -> BulletJudgeScores:
        """Return 1-5 scores on relevance, specificity, and keyword match."""
        logger.debug(
            "BulletJudgeAgent INPUT case=%r generated_count=%s",
            company_name,
            len(generated_bullets),
        )
        jd_excerpt = jd_text.strip()[:1200]
        messages = [
            {"role": "system", "content": BULLET_JUDGE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": BULLET_JUDGE_USER_PROMPT.format(
                    job_title=job_title,
                    company_name=company_name,
                    jd_excerpt=jd_excerpt,
                    ideal_json=json.dumps(ideal_bullets, indent=2),
                    generated_json=json.dumps(generated_bullets, indent=2),
                ),
            },
        ]
        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        logger.debug("BulletJudgeAgent raw output: %s", content[:500])
        scores = self._parse_scores(content)
        logger.debug(
            "BulletJudgeAgent OUTPUT relevance=%s specificity=%s keyword=%s",
            scores.relevance,
            scores.specificity,
            scores.keyword_match,
        )
        return scores

    def _parse_scores(self, content: str) -> BulletJudgeScores:
        """Parse and validate judge JSON."""
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()
        try:
            return BulletJudgeScores.model_validate_json(text)
        except ValidationError as exc:
            logger.warning("Bullet judge JSON validation failed: %s", exc)
            data = json.loads(text)
            return BulletJudgeScores.model_validate(data)
