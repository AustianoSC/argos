import logging

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from argos.graph.nodes.extract import extract_worker_node
from argos.graph.nodes.match import match_worker_node
from argos.graph.nodes.save import save_results_node
from argos.graph.nodes.search import search_node
from argos.graph.state import (
    ExtractWorkerInput,
    MatchWorkerInput,
    PipelineState,
)

logger = logging.getLogger(__name__)


def fan_out_to_matchers(state: PipelineState) -> list[Send]:
    """Dynamic fan-out: create one match worker per search result."""
    results = state.get("search_results", [])
    if not results:
        logger.warning("No search results to match")
        return [Send("save_results", state)]

    logger.info("Fanning out to %d match workers", len(results))
    return [
        Send(
            "match_worker",
            MatchWorkerInput(
                product_name=state["product_name"],
                product_id=state["product_id"],
                search_result=result,
            ),
        )
        for result in results
    ]


def fan_out_to_extractors(state: PipelineState) -> list[Send]:
    """Dynamic fan-out: create one extract worker per confirmed match."""
    matched = [m for m in state.get("match_results", []) if m.is_match]

    if not matched:
        logger.info("No confirmed matches, skipping extraction")
        return [Send("save_results", state)]

    logger.info("Fanning out to %d extract workers", len(matched))
    return [
        Send(
            "extract_worker",
            ExtractWorkerInput(
                product_name=state["product_name"],
                product_id=state["product_id"],
                match_result=m,
            ),
        )
        for m in matched
    ]


def build_graph() -> StateGraph:
    """Build the LangGraph pipeline.

    Flow: START → search → [match_worker x N] → [extract_worker x M] → save_results → END
    """
    builder = StateGraph(PipelineState)

    # Register nodes
    builder.add_node("search", search_node)
    builder.add_node("match_worker", match_worker_node)
    builder.add_node("extract_worker", extract_worker_node)
    builder.add_node("save_results", save_results_node)

    # Edges
    builder.add_edge(START, "search")
    builder.add_conditional_edges("search", fan_out_to_matchers)
    builder.add_conditional_edges("match_worker", fan_out_to_extractors)
    builder.add_edge("extract_worker", "save_results")
    builder.add_edge("save_results", END)

    return builder


def compile_graph(checkpointer=None):  # type: ignore[no-untyped-def]
    """Compile the graph, optionally with a checkpointer for persistence."""
    builder = build_graph()
    return builder.compile(checkpointer=checkpointer)
