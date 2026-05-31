"""Parse a job description and match required skills to resume evidence (RAG)."""

import json
import logging

from groq import Groq
from pydantic import BaseModel, Field, ValidationError

from app.agents.research_agent import GROQ_MODEL
from app.config import get_required_env
from app.models.jd_parse import (
    JDExperienceRequirement,
    JDParseResult,
    JDSkillMatch,
    JDSkillRequirement,
    RetrievedChunkModel,
)
from app.rag.resume_profile import ensure_resume_profile
from app.rag.retrieval import retrieve_experience
from app.services.experience_match import build_full_experience_match

logger = logging.getLogger(__name__)

JD_PARSER_SYSTEM_PROMPT = """You extract hiring requirements from job descriptions.

Return ONLY valid JSON (no markdown) with this shape:
{
  "job_title": "string",
  "company_context": "one sentence about role level or team if known",
  "experience_requirement": null or {
    "min_years": number,
    "max_years": number or null,
    "raw_text": "exact JD phrase, e.g. '3+ years of React experience'"
  },
  "skills": [
    {
      "skill": "short label",
      "priority": "required | preferred | nice_to_have",
      "evidence_query": "phrase to search a resume, e.g. 'React performance optimization'",
      "min_years": null or number,
      "experience_raw_text": "JD phrase for this skill's tenure, or empty string"
    }
  ]
}

Rules:
- List 6-12 skills max, focusing on technical requirements.
- evidence_query should be specific enough to find relevant resume bullets.
- Do not invent skills that are not implied by the job description text.
- experience_requirement: role-level YoE only (e.g. "5+ years software engineering"). null if not stated.
- Per skill: set min_years ONLY when the JD ties years to that skill (e.g. "3+ years React" → min_years 3).
  Different skills may have different min_years. Leave min_years null when no tenure is stated for that skill."""

JD_PARSER_USER_PROMPT = """Parse this job description and extract skills:

---
{job_description}
---"""


class _JDSkillsPayload(BaseModel):
    """Intermediate JSON from the LLM before RAG retrieval."""

    job_title: str = "Unknown role"
    company_context: str = ""
    experience_requirement: JDExperienceRequirement | None = None
    skills: list[JDSkillRequirement] = Field(default_factory=list)


class JDParserAgent:
    """Extracts skills from a JD string, then runs vector search per skill."""

    def __init__(self) -> None:
        """Create a Groq client using GROQ_API_KEY from the environment."""
        self._client = Groq(api_key=get_required_env("GROQ_API_KEY"))

    def parse_and_match(self, job_description: str) -> JDParseResult:
        """Extract skills from raw JD text and retrieve resume chunks for each."""
        logger.debug("JDParserAgent INPUT length=%s chars", len(job_description))

        messages = [
            {"role": "system", "content": JD_PARSER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": JD_PARSER_USER_PROMPT.format(
                    job_description=job_description.strip(),
                ),
            },
        ]
        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        logger.debug("JDParserAgent LLM raw output: %s", content[:800])

        payload = self._parse_skills_payload(content)
        skill_matches: list[JDSkillMatch] = []

        for requirement in payload.skills:
            query = requirement.evidence_query or requirement.skill
            raw_matches = retrieve_experience(query)
            matches = [
                RetrievedChunkModel.model_validate(match) for match in raw_matches
            ]
            skill_matches.append(
                JDSkillMatch(
                    skill=requirement.skill,
                    priority=requirement.priority,
                    matches=matches,
                ),
            )
            logger.info(
                "RAG match for %r → %s chunks (top score=%.3f)",
                requirement.skill,
                len(matches),
                matches[0].score if matches else 0.0,
            )

        profile = ensure_resume_profile(force=False)
        experience_match = build_full_experience_match(
            payload.experience_requirement,
            payload.skills,
            profile,
        )
        logger.info(
            "YoE check: status=%s total=%.1f yrs, %s skill-level checks",
            experience_match.status,
            profile.total_years_professional,
            len(experience_match.skill_checks),
        )

        result = JDParseResult(
            job_title=payload.job_title,
            company_context=payload.company_context,
            skills=payload.skills,
            skill_matches=skill_matches,
            experience_requirement=payload.experience_requirement,
            experience_match=experience_match,
        )
        logger.debug("JDParserAgent OUTPUT skills=%s", len(result.skills))
        return result

    def _parse_skills_payload(self, content: str) -> _JDSkillsPayload:
        """Parse and validate the model's JSON skill list."""
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        try:
            return _JDSkillsPayload.model_validate_json(text)
        except ValidationError as exc:
            logger.warning("JD JSON validation failed: %s", exc)
            data = json.loads(text)
            return _JDSkillsPayload.model_validate(data)
