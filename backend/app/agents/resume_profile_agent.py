"""Extract per-skill and total years of experience from resume text files."""

import json
import logging
from datetime import datetime, timezone

from groq import Groq
from pydantic import BaseModel, Field, ValidationError

from app.agents.research_agent import GROQ_MODEL
from app.config import get_required_env
from app.models.resume_profile import ResumeExperienceProfile, SkillExperienceEntry

logger = logging.getLogger(__name__)

RESUME_PROFILE_SYSTEM_PROMPT = """You analyze a candidate's resume documents and estimate years of hands-on experience per skill or technology.

Return ONLY valid JSON (no markdown):
{
  "total_years_professional": number,
  "skill_experience": [
    {
      "skill": "short label e.g. React, Python, AWS",
      "years": number,
      "evidence": "one line citing role, project, or dates from the text"
    }
  ],
  "notes": "brief assumptions (e.g. how internships were counted)"
}

Rules:
- Use ONLY facts stated in the provided documents; do not invent employers or dates.
- Use fractional years (0.5, 1.5, etc.). A summer internship is typically 0.25–0.5 years unless described as longer.
- List 8–20 skills/technologies with non-zero experience that appear in the documents.
- total_years_professional is overall SWE-relevant professional experience (not the sum of all skill years).
- When the JD would ask "3+ years React", your React years should reflect dedicated React usage time."""

RESUME_PROFILE_USER_PROMPT = """Estimate years of experience from these documents:

---
{documents}
---"""


class _ResumeProfilePayload(BaseModel):
    total_years_professional: float = 0.0
    skill_experience: list[SkillExperienceEntry] = Field(default_factory=list)
    notes: str = ""


class ResumeProfileAgent:
    """Uses an LLM to build a structured YoE profile from resume/project text."""

    def __init__(self) -> None:
        """Create a Groq client using GROQ_API_KEY from the environment."""
        self._client = Groq(api_key=get_required_env("GROQ_API_KEY"))

    def extract(self, documents_text: str, source_hash: str) -> ResumeExperienceProfile:
        """Parse resume documents and return a structured experience profile."""
        logger.debug("ResumeProfileAgent INPUT chars=%s", len(documents_text))

        messages = [
            {"role": "system", "content": RESUME_PROFILE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": RESUME_PROFILE_USER_PROMPT.format(
                    documents=documents_text.strip(),
                ),
            },
        ]
        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=0.1,
        )
        content = response.choices[0].message.content or ""
        logger.debug("ResumeProfileAgent raw output: %s", content[:600])

        payload = self._parse_payload(content)
        profile = ResumeExperienceProfile(
            source_hash=source_hash,
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_years_professional=max(0.0, payload.total_years_professional),
            skill_experience=payload.skill_experience,
            notes=payload.notes,
        )
        logger.info(
            "Resume profile: %.1f yrs total, %s skills",
            profile.total_years_professional,
            len(profile.skill_experience),
        )
        return profile

    def _parse_payload(self, content: str) -> _ResumeProfilePayload:
        """Parse and validate the model's JSON profile."""
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(
                line for line in lines if not line.strip().startswith("```")
            ).strip()

        try:
            return _ResumeProfilePayload.model_validate_json(text)
        except ValidationError as exc:
            logger.warning("Resume profile JSON validation failed: %s", exc)
            data = json.loads(text)
            return _ResumeProfilePayload.model_validate(data)
