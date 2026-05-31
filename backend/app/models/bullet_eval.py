"""Pydantic schemas for Phase 6 resume-bullet eval harness."""

from pydantic import BaseModel, Field


class BulletJudgeScores(BaseModel):
    """LLM-as-judge scores for one generated bullet set (1-5 each)."""

    relevance: int = Field(ge=1, le=5, description="How well bullets match the role and evidence")
    specificity: int = Field(
        ge=1,
        le=5,
        description="Concrete metrics, tools, and outcomes vs vague claims",
    )
    keyword_match: int = Field(
        ge=1,
        le=5,
        description="Natural use of JD keywords without keyword stuffing",
    )
    reasoning: str = Field(description="2-4 sentences explaining the scores")


class EvalTestCase(BaseModel):
    """One row from evals/test_cases.json."""

    id: str
    name: str
    company_name: str
    job_url: str
    jd_text: str
    ideal_bullets: list[str]
    notes: str = ""


class EvalTestSuite(BaseModel):
    """Root object loaded from evals/test_cases.json."""

    version: int
    description: str
    pass_threshold: float = Field(default=3.5, ge=1.0, le=5.0)
    cases: list[EvalTestCase]


class CaseEvalResult(BaseModel):
    """Pipeline output + judge scores for a single test case."""

    case_id: str
    case_name: str
    company_name: str
    generated_bullets: list[str]
    ideal_bullets: list[str]
    scores: BulletJudgeScores
    average_score: float
    pipeline_error: str | None = None
