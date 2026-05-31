"""Stream LangGraph node progress as SSE-friendly events."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.graph.pipeline import get_compiled_graph
from app.graph.state import PipelineState
from app.schemas.api import PipelineEvent

logger = logging.getLogger(__name__)

PARALLEL_NODES = frozenset({"research_company", "parse_jd"})
SEQUENTIAL_AFTER_PARALLEL = (
    "write_bullets",
    "write_cover_letter",
    "evaluate_opportunity",
)


class PipelineStreamError(Exception):
    """Raised when the pipeline cannot continue (scrape, LLM, validation)."""


def _merge_state(current: PipelineState, update: dict[str, Any]) -> PipelineState:
    """Merge a node update into accumulated state (best-effort for streaming)."""
    merged: dict[str, Any] = dict(current)
    for key, value in update.items():
        if key == "agent_logs" and key in merged:
            merged[key] = [*merged.get(key, []), *value]
        else:
            merged[key] = value
    return merged  # type: ignore[return-value]


def _validate_after_scrape(state: PipelineState) -> None:
    """Abort early when scraping failed and no JD text is available."""
    if state.get("jd_text"):
        return
    logs = state.get("agent_logs") or []
    if any("scrape_jd: failed" in entry for entry in logs):
        msg = (
            "Could not scrape job posting (site may block bots). "
            "Retry with jd_text in the request body for testing."
        )
        raise PipelineStreamError(msg)
    if any("missing job_url" in entry for entry in logs):
        raise PipelineStreamError("Missing job_url and no jd_text provided.")


async def stream_pipeline_events(
    job_id: str,
    initial_state: PipelineState,
) -> AsyncIterator[PipelineEvent]:
    """Yield running/done events as LangGraph nodes finish."""
    graph = get_compiled_graph()
    accumulated: PipelineState = dict(initial_state)
    finished_parallel: set[str] = set()
    final_state: PipelineState | None = None

    yield PipelineEvent(
        job_id=job_id,
        node="scrape_jd",
        status="running",
    )

    try:
        async for chunk in graph.astream(
            initial_state,
            stream_mode=["updates", "values"],
        ):
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode, data = chunk
            else:
                mode, data = "updates", chunk

            if mode == "values":
                final_state = data
                continue

            if mode != "updates" or not isinstance(data, dict):
                continue

            for node_name, update in data.items():
                if not isinstance(update, dict):
                    continue

                accumulated = _merge_state(accumulated, update)

                yield PipelineEvent(
                    job_id=job_id,
                    node=node_name,
                    status="done",
                    output=update,
                )

                if node_name == "scrape_jd":
                    _validate_after_scrape(accumulated)
                    for parallel_node in PARALLEL_NODES:
                        yield PipelineEvent(
                            job_id=job_id,
                            node=parallel_node,
                            status="running",
                        )

                if node_name in PARALLEL_NODES:
                    finished_parallel.add(node_name)
                    if finished_parallel == PARALLEL_NODES:
                        yield PipelineEvent(
                            job_id=job_id,
                            node="write_bullets",
                            status="running",
                        )

                if node_name == "write_bullets":
                    yield PipelineEvent(
                        job_id=job_id,
                        node="write_cover_letter",
                        status="running",
                    )
                elif node_name == "write_cover_letter":
                    yield PipelineEvent(
                        job_id=job_id,
                        node="evaluate_opportunity",
                        status="running",
                    )

    except PipelineStreamError:
        raise
    except Exception as exc:
        logger.exception("Pipeline stream failed for job %s", job_id)
        msg = f"Pipeline failed at node: {exc}"
        raise PipelineStreamError(msg) from exc

    if final_state is None:
        msg = "Pipeline finished without final state."
        raise PipelineStreamError(msg)

    yield PipelineEvent(
        job_id=job_id,
        node="pipeline",
        status="done",
        output=dict(final_state),
    )
