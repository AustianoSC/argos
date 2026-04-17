import logging

from argos.graph.state import ExtractedPrice, ExtractWorkerInput
from argos.services.fetcher import fetch_page
from argos.services.llm import get_extract_llm

logger = logging.getLogger(__name__)

EXTRACT_PROMPT = """Extract the current price information from this product page.

Product: {product_name}
Page URL: {url}

Page content (truncated):
{content}

Extract the price, currency, stock status, and seller name.
For the raw_text field, include the exact text from the page that contains the price.
If multiple prices are shown, extract the primary/current selling price (not MSRP or list price)."""

MAX_CONTENT_LENGTH = 4000


async def extract_worker_node(state: ExtractWorkerInput) -> dict:
    """Extract structured price data from a confirmed product page.

    Fetches the page, sends content to the LLM for structured extraction.
    Returns a single-element list for the add reducer.
    """
    match_result = state["match_result"]
    product_name = state["product_name"]
    url = match_result.url

    logger.info("Extracting price from: %s", url)

    # Fetch page content (likely cached from match phase)
    content = await fetch_page(url)
    if content is None:
        logger.warning("Could not fetch %s for extraction, skipping", url)
        return {"extracted_prices": []}

    truncated_content = content[:MAX_CONTENT_LENGTH]

    llm = get_extract_llm().with_structured_output(ExtractedPrice)
    prompt = EXTRACT_PROMPT.format(
        product_name=product_name,
        url=url,
        content=truncated_content,
    )

    try:
        result = await llm.ainvoke(prompt)
    except Exception as e:
        logger.error("LLM price extraction failed for %s: %s", url, e)
        return {"extracted_prices": [], "errors": [f"Extract failed for {url}: {e}"]}

    # Ensure URL is set from the source
    result.url = url

    logger.info(
        "Extracted price from %s: %s %s (in_stock=%s)",
        url,
        result.price,
        result.currency,
        result.in_stock,
    )
    return {"extracted_prices": [result]}
