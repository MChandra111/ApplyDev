"""Request/response models for the Phase 4 HTTP API."""

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class AnalyzeRequest(BaseModel):
    """Body for POST /api/analyze."""

    job_url: HttpUrl
    company_name: str | None = Field(
        default=None,
        description="Optional override when scrape cannot infer company",
    )
    jd_text: str | None = Field(
        default=None,
        description="Optional preloaded JD (skips scrape; useful for testing)",
    )


class PipelineEvent(BaseModel):
    """One Server-Sent Event payload streamed during analysis."""

    job_id: str
    node: str
    status: Literal["running", "done", "error"]
    output: dict[str, Any] | None = None
    error: str | None = None


class JobSummary(BaseModel):
    """Stored job metadata returned by GET /api/jobs/{job_id}."""

    job_id: str
    job_url: str
    status: Literal["running", "completed", "failed"]
    error: str | None = None
    result: dict[str, Any] | None = None
