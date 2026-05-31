"""Shared LangGraph pipeline state (Phase 3)."""

import operator
from typing import Annotated, Any, TypedDict


class PipelineState(TypedDict, total=False):
    """State passed between every node in the ApplyDev job analysis graph."""

    job_url: str
    company_name: str
    jd_text: str
    research_summary: dict[str, Any]
    matched_experience: dict[str, Any]
    resume_bullets: list[str]
    cover_letter: str
    opportunity_score: dict[str, Any]
    agent_logs: Annotated[list[str], operator.add]
