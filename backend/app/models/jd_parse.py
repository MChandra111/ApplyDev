"""Structured outputs for job-description parsing."""

from pydantic import BaseModel, Field


class RetrievedChunkModel(BaseModel):
    """One chunk returned from vector search (API-friendly)."""

    text: str
    source: str
    score: float
    chunk_index: int


class JDSkillRequirement(BaseModel):
    """One skill extracted from a job description."""

    skill: str = Field(description="Short skill label, e.g. 'React' or 'FastAPI'")
    priority: str = Field(
        description="required | preferred | nice_to_have",
    )
    evidence_query: str = Field(
        description="Natural-language phrase used to search the resume",
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
