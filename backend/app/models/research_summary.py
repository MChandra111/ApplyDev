"""Structured output schema for company research."""

from pydantic import BaseModel, Field


class ResearchSummary(BaseModel):
    """JSON shape the ResearchAgent must produce after searching the web."""

    company_name: str = Field(description="Company researched")
    company_size: str = Field(
        description="Estimated size, e.g. employee count or market cap band",
    )
    recent_news: list[str] = Field(
        description="2-5 bullet-style headlines or developments",
    )
    tech_stack_mentions: list[str] = Field(
        description="Languages, frameworks, clouds, or tools mentioned in sources",
    )
    red_flags: list[str] = Field(
        description="Layoffs, lawsuits, poor reviews, or other concerns; empty if none",
    )
