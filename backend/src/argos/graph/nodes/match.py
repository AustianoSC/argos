import logging

from argos.graph.state import MatchResult, MatchWorkerInput
from argos.services.fetcher import fetch_page
from argos.services.llm import get_match_llm

logger = logging.getLogger(__name__)

MATCH_PROMPT = """You are evaluating whether a web page is selling a specific product.

Product to find: {product_name}

Page title: {title}
Page content (truncated):
{content}

Determine if this page is selling the exact product above (not a different model,
not an accessory, not a review-only page). Consider the product name, model number,
and any distinguishing features."""

MAX_CONTENT_LENGTH = 4000


async def match_worker_node(state: MatchWorkerInput) -> dict:
    """Evaluate whether a search result is actually the target product.

    Fetches the page, sends content to the LLM for structured evaluation.
    Returns a single-element list for the add reducer.
    """
    search_result = state["search_result"]
    product_name = state["product_name"]
    url = search_result.url
    title = search_result.title

    logger.info("Matching: %s", url)

    # Fetch page content
    content = await fetch_page(url)
    if content is None:
        logger.warning("Could not fetch %s, skipping", url)
        return {"match_results": []}

    # Truncate to avoid blowing token limits
    truncated_content = content[:MAX_CONTENT_LENGTH]

    # LLM evaluation with structured output
    llm = get_match_llm().with_structured_output(MatchResult)
    prompt = MATCH_PROMPT.format(
        product_name=product_name,
        title=title,
        content=truncated_content,
    )

    try:
        result = await llm.ainvoke(prompt)
    except Exception as e:
        logger.error("LLM match evaluation failed for %s: %s", url, e)
        return {"match_results": [], "errors": [f"Match failed for {url}: {e}"]}

    # Ensure the URL is set from the source (LLM might not return it correctly)
    result.url = url
    result.title = title

    logger.info(
        "Match result for %s: is_match=%s confidence=%.2f",
        url,
        result.is_match,
        result.confidence,
    )
    return {"match_results": [result]}
