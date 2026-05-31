"""LangGraph node functions — each wraps one agent or tool step."""

import logging
from typing import Any

from app.agents.eval_agent import EvalAgent
from app.agents.jd_parser_agent import JDParserAgent
from app.agents.research_agent import ResearchAgent
from app.agents.writer_agent import WriterAgent
from app.graph.state import PipelineState
from app.models.jd_parse import JDParseResult
from app.models.research_summary import ResearchSummary
from app.tools.jd_scraper import fetch_job_posting_text, guess_company_name

logger = logging.getLogger(__name__)


def scrape_jd(state: PipelineState) -> dict[str, Any]:
    """Fetch job posting text from URL or pass through preloaded JD text."""
    if state.get("jd_text"):
        company = state.get("company_name") or "Unknown Company"
        return {
            "agent_logs": [f"scrape_jd: skipped (JD already provided, company={company})"],
        }

    job_url = state.get("job_url", "")
    if not job_url:
        msg = "scrape_jd: missing job_url and jd_text"
        return {"agent_logs": [msg]}

    try:
        jd_text = fetch_job_posting_text(job_url)
        company_name = guess_company_name(job_url, jd_text)
        logger.info("Scraped %s chars from %s", len(jd_text), job_url)
        return {
            "jd_text": jd_text,
            "company_name": company_name,
            "agent_logs": [
                f"scrape_jd: done ({len(jd_text)} chars, company={company_name})",
            ],
        }
    except Exception as exc:
        logger.exception("scrape_jd failed")
        return {"agent_logs": [f"scrape_jd: failed — {exc}"]}


def research_company(state: PipelineState) -> dict[str, Any]:
    """Run Phase 1 ResearchAgent (Tavily + Groq)."""
    company_name = state.get("company_name") or "Unknown Company"
    agent = ResearchAgent()
    summary = agent.research(company_name)
    return {
        "research_summary": summary.model_dump(),
        "agent_logs": [f"research_company: done ({company_name})"],
    }


def parse_jd(state: PipelineState) -> dict[str, Any]:
    """Run Phase 2 JDParserAgent (skills + Pinecone RAG)."""
    jd_text = state.get("jd_text", "")
    if not jd_text:
        return {"agent_logs": ["parse_jd: skipped (no jd_text)"]}

    agent = JDParserAgent()
    result = agent.parse_and_match(jd_text)
    return {
        "matched_experience": result.model_dump(),
        "agent_logs": [
            f"parse_jd: done ({len(result.skills)} skills, "
            f"{len(result.skill_matches)} RAG lookups)",
        ],
    }


def write_bullets(state: PipelineState) -> dict[str, Any]:
    """WriterAgent — tailored resume bullets from research + matches."""
    research = _require_research(state)
    jd_parse = _require_jd_parse(state)
    writer = WriterAgent()
    bullets = writer.write_resume_bullets(research, jd_parse)
    return {
        "resume_bullets": bullets,
        "agent_logs": [f"write_bullets: done ({len(bullets)} bullets)"],
    }


def write_cover_letter(state: PipelineState) -> dict[str, Any]:
    """WriterAgent — three-paragraph cover letter."""
    research = _require_research(state)
    jd_parse = _require_jd_parse(state)
    company_name = state.get("company_name") or research.company_name
    bullets = state.get("resume_bullets") or []
    writer = WriterAgent()
    letter = writer.write_cover_letter(company_name, research, jd_parse, bullets)
    return {
        "cover_letter": letter,
        "agent_logs": ["write_cover_letter: done"],
    }


def evaluate_opportunity(state: PipelineState) -> dict[str, Any]:
    """EvalAgent — score job 1-10 with reasoning."""
    research = _require_research(state)
    jd_parse = _require_jd_parse(state)
    company_name = state.get("company_name") or research.company_name
    bullets = state.get("resume_bullets") or []
    cover_letter = state.get("cover_letter") or ""
    agent = EvalAgent()
    score = agent.evaluate(
        company_name,
        research,
        jd_parse,
        bullets,
        cover_letter,
    )
    return {
        "opportunity_score": score.model_dump(),
        "agent_logs": [f"evaluate_opportunity: score={score.score}/10"],
    }


def _require_research(state: PipelineState) -> ResearchSummary:
    """Load research_summary from state or raise a clear pipeline error."""
    raw = state.get("research_summary")
    if not raw:
        msg = "research_summary missing — research_company may have failed"
        raise RuntimeError(msg)
    return ResearchSummary.model_validate(raw)


def _require_jd_parse(state: PipelineState) -> JDParseResult:
    """Load matched_experience from state or raise a clear pipeline error."""
    raw = state.get("matched_experience")
    if not raw:
        msg = "matched_experience missing — parse_jd may have failed"
        raise RuntimeError(msg)
    return JDParseResult.model_validate(raw)
