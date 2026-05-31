"""Structured outputs for job-description parsing."""

from typing import Literal

from pydantic import BaseModel, Field

ExperienceMatchStatus = Literal["not_specified", "meets", "short"]


class RetrievedChunkModel(BaseModel):
    """One chunk returned from vector search (API-friendly)."""

    text: str
    source: str
    score: float
    chunk_index: int


class JDExperienceRequirement(BaseModel):
    """Years-of-experience requirement extracted from a JD (null min = not stated)."""

    min_years: float | None = Field(
        default=None,
        description="Minimum years required, e.g. 3 for '3+ years'",
    )
    max_years: float | None = Field(
        default=None,
        description="Upper bound when JD says a range, e.g. 5 for '3-5 years'",
    )
    raw_text: str = Field(
        default="",
        description="Original JD phrase, e.g. '5+ years of professional experience'",
    )


class SkillExperienceCheck(BaseModel):
    """YoE comparison for one JD skill with an explicit years requirement."""

    skill: str
    status: ExperienceMatchStatus
    required_min_years: float | None = None
    candidate_years: float | None = None
    gap_years: float | None = None
    raw_text: str = ""
    summary: str = ""


class ExperienceMatchResult(BaseModel):
    """Aggregate YoE comparison (role-level + per-skill gaps)."""

    status: ExperienceMatchStatus
    required_min_years: float | None
    candidate_years: float
    gap_years: float | None = Field(
        default=None,
        description="Positive when candidate is under the minimum",
    )
    summary: str
    skill_checks: list[SkillExperienceCheck] = Field(default_factory=list)


class JDSkillRequirement(BaseModel):
    """One skill extracted from a job description."""

    skill: str = Field(description="Short skill label, e.g. 'React' or 'FastAPI'")
    priority: str = Field(
        description="required | preferred | nice_to_have",
    )
    evidence_query: str = Field(
        description="Natural-language phrase used to search the resume",
    )
    min_years: float | None = Field(
        default=None,
        description="Years required for this skill when JD states it, e.g. 3 for '3+ years React'",
    )
    experience_raw_text: str = Field(
        default="",
        description="JD phrase for this skill's tenure, e.g. '3+ years of React'",
    )


class JDSkillMatch(BaseModel):
    """Resume evidence retrieved for one JD skill."""

    skill: str
    priority: str
    matches: list[RetrievedChunkModel]


class JDParseResult(BaseModel):
    """Full output of JDParserAgent."""

    job_title: str
    company_context: str
    skills: list[JDSkillRequirement]
    skill_matches: list[JDSkillMatch]
    experience_requirement: JDExperienceRequirement | None = None
    experience_match: ExperienceMatchResult | None = None
