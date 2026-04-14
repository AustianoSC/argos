import asyncio
import logging
from urllib.parse import urlparse

from ddgs import DDGS

from argos.config import settings
from argos.graph.state import PipelineState, SearchResult

logger = logging.getLogger(__name__)


def _is_blocked(url: str) -> bool:
    domain = urlparse(url).netloc.lower()
    return any(blocked in domain for blocked in settings.search_blocked_domains)


def _search_sync(query: str, max_results: int) -> list[dict]:
    """Run DuckDuckGo search (sync library, called via executor)."""
    return list(DDGS().text(query, max_results=max_results))


async def search_node(state: PipelineState) -> dict:
    """Search DuckDuckGo for product listings.

    Augments the product name with price-related terms and filters out
    results from blocked domains (forums, video sites, etc.).
    """
    product_name = state["product_name"]
    query = f'"{product_name}" price buy'
    logger.info("Searching DuckDuckGo: %s", query)

    loop = asyncio.get_running_loop()
    try:
        raw_results = await loop.run_in_executor(
            None, _search_sync, query, settings.search_max_results
        )
    except Exception as e:
        logger.error("DuckDuckGo search failed: %s", e)
        return {"search_results": [], "errors": [f"Search failed: {e}"]}

    results: list[SearchResult] = []
    for r in raw_results:
        url = r.get("href", "")
        if not url or _is_blocked(url):
            logger.debug("Filtered out: %s", url)
            continue
        results.append(
            SearchResult(
                url=url,
                title=r.get("title", ""),
                snippet=r.get("body", ""),
            )
        )

    logger.info("Search returned %d results (%d after filtering)", len(raw_results), len(results))
    return {"search_results": results}
