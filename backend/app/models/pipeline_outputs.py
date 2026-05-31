"""Structured outputs for Phase 3 pipeline writer and eval agents."""

from pydantic import BaseModel, Field


class OpportunityScore(BaseModel):
    """Eval agent score with interview-friendly reasoning breakdown."""

    score: int = Field(ge=1, le=10, description="Overall opportunity score 1-10")
    fit_summary: str = Field(description="How well the role matches skills and experience")
    growth_summary: str = Field(description="Career growth and learning potential")
    red_flags_summary: str = Field(description="Company or role concerns from research")
    recommendation: str = Field(
        description="apply | maybe | pass — short actionable verdict",
    )
