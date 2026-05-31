"""Pydantic models for agent outputs."""

from app.models.jd_parse import JDParseResult, JDSkillMatch, JDSkillRequirement
from app.models.pipeline_outputs import OpportunityScore
from app.models.research_summary import ResearchSummary

__all__ = [
    "JDParseResult",
    "JDSkillMatch",
    "JDSkillRequirement",
    "OpportunityScore",
    "ResearchSummary",
]
