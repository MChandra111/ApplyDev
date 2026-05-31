"""Phase 4 API routes: analyze (SSE) and job retrieval."""

import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.sse import format_sse
from app.graph.state import PipelineState
from app.schemas.api import AnalyzeRequest, JobSummary, PipelineEvent
from app.services.job_store import job_store
from app.services.pipeline_stream import PipelineStreamError, stream_pipeline_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.post("/analyze")
async def analyze_job(body: AnalyzeRequest) -> StreamingResponse:
    """Run the LangGraph pipeline and stream per-node progress as SSE."""
    job_url = str(body.job_url)
    record = job_store.create(job_url)

    initial_state: PipelineState = {
        "job_url": job_url,
        "agent_logs": [],
    }
    if body.company_name:
        initial_state["company_name"] = body.company_name
    if body.jd_text:
        initial_state["jd_text"] = body.jd_text

    async def event_generator() -> AsyncIterator[str]:
        """Yield SSE frames and persist job status for GET /api/jobs/{id}."""
        job_id = record.job_id
        started = PipelineEvent(
            job_id=job_id,
            node="pipeline",
            status="running",
            output={"job_url": job_url},
        )
        job_store.append_event(job_id, started.model_dump())
        yield format_sse(started.model_dump())

        try:
            async for event in stream_pipeline_events(job_id, initial_state):
                payload = event.model_dump()
                job_store.append_event(job_id, payload)
                yield format_sse(payload)

                if event.status == "done" and event.node == "pipeline":
                    job_store.complete(job_id, event.output or {})

        except PipelineStreamError as exc:
            error_event = PipelineEvent(
                job_id=job_id,
                node="pipeline",
                status="error",
                error=str(exc),
            )
            payload = error_event.model_dump()
            job_store.append_event(job_id, payload)
            job_store.fail(job_id, str(exc))
            yield format_sse(payload)

        except Exception as exc:
            logger.exception("Unexpected analyze failure for job %s", job_id)
            message = f"Unexpected server error: {exc}"
            error_event = PipelineEvent(
                job_id=job_id,
                node="pipeline",
                status="error",
                error=message,
            )
            payload = error_event.model_dump()
            job_store.append_event(job_id, payload)
            job_store.fail(job_id, message)
            yield format_sse(payload)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Job-Id": record.job_id,
        },
    )


@router.get("/jobs/{job_id}", response_model=JobSummary)
async def get_job(job_id: str) -> JobSummary:
    """Return a completed (or failed) analysis by job id."""
    record = job_store.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobSummary(
        job_id=record.job_id,
        job_url=record.job_url,
        status=record.status,  # type: ignore[arg-type]
        error=record.error,
        result=record.result,
    )
