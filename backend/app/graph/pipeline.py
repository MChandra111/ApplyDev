"""LangGraph state machine for the full ApplyDev analysis pipeline."""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.config import configure_langsmith
from app.graph import nodes
from app.graph.state import PipelineState

logger = logging.getLogger(__name__)

_compiled_graph: Any | None = None


def build_pipeline_graph() -> Any:
    """Wire nodes: scrape → (research ∥ parse) → bullets → letter → eval."""
    builder = StateGraph(PipelineState)

    builder.add_node("scrape_jd", nodes.scrape_jd)
    builder.add_node("research_company", nodes.research_company)
    builder.add_node("parse_jd", nodes.parse_jd)
    builder.add_node("write_bullets", nodes.write_bullets)
    builder.add_node("write_cover_letter", nodes.write_cover_letter)
    builder.add_node("evaluate_opportunity", nodes.evaluate_opportunity)

    builder.add_edge(START, "scrape_jd")
    # Parallel fan-out after scrape
    builder.add_edge("scrape_jd", "research_company")
    builder.add_edge("scrape_jd", "parse_jd")
    # Fan-in: write_bullets waits for both branches
    builder.add_edge("research_company", "write_bullets")
    builder.add_edge("parse_jd", "write_bullets")
    builder.add_edge("write_bullets", "write_cover_letter")
    builder.add_edge("write_cover_letter", "evaluate_opportunity")
    builder.add_edge("evaluate_opportunity", END)

    return builder.compile()


def get_compiled_graph() -> Any:
    """Return a singleton compiled graph (lazy init)."""
    global _compiled_graph
    if _compiled_graph is None:
        configure_langsmith()
        _compiled_graph = build_pipeline_graph()
        logger.debug("LangGraph pipeline compiled")
    return _compiled_graph


def run_pipeline(initial_state: PipelineState) -> PipelineState:
    """Execute the full graph and return final state."""
    graph = get_compiled_graph()
    result = graph.invoke(initial_state)
    return result
