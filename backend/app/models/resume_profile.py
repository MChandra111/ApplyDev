"""Structured years-of-experience profile extracted from resume documents."""

from pydantic import BaseModel, Field


class SkillExperienceEntry(BaseModel):
    """Estimated hands-on years for one skill or technology area."""

    skill: str = Field(description="Short label, e.g. React or FastAPI")
    years: float = Field(ge=0, description="Estimated years of relevant use")
    evidence: str = Field(
        default="",
        description="One-line citation from resume (role, dates)",
    )


class ResumeExperienceProfile(BaseModel):
    """LLM-generated YoE profile; cached when document content hash is unchanged."""

    source_hash: str = ""
    generated_at: str = ""
    total_years_professional: float = Field(
        ge=0,
        description="Overall professional SWE-relevant experience",
    )
    skill_experience: list[SkillExperienceEntry] = Field(default_factory=list)
    notes: str = ""
