import asyncio
import logging
import time
from urllib.parse import urlparse

import httpx
import trafilatura
from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

from argos.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory TTL cache: {url: (content, timestamp)}
_cache: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 600  # 10 minutes

# Reusable httpx client
_http_client: httpx.AsyncClient | None = None

# Reusable Crawl4AI crawler
_crawler: AsyncWebCrawler | None = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=settings.fetch_timeout,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
            },
        )
    return _http_client


async def _get_crawler() -> AsyncWebCrawler:
    global _crawler
    if _crawler is None or not _crawler.ready:
        _crawler = AsyncWebCrawler()
        await _crawler.start()
    return _crawler


def _is_js_heavy(url: str) -> bool:
    domain = urlparse(url).netloc.lower()
    return any(d in domain for d in settings.js_heavy_domains)


def _check_cache(url: str) -> str | None:
    if url in _cache:
        content, ts = _cache[url]
        if time.time() - ts < _CACHE_TTL:
            return content
        del _cache[url]
    return None


def _set_cache(url: str, content: str) -> None:
    _cache[url] = (content, time.time())


async def _fetch_with_httpx(url: str) -> str | None:
    """ httpx GET + trafilatura text extraction."""
    try:
        client = _get_http_client()
        response = await client.get(url)
        response.raise_for_status()
        html = response.text
    except httpx.HTTPError as e:
        logger.warning("httpx fetch failed for %s: %s", url, e)
        return None

    # trafilatura is sync — run in executor to avoid blocking
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(
        None,
        lambda: trafilatura.extract(html, url=url, include_tables=True, include_links=True),
    )

    if not text or len(text) < 50:
        logger.debug("trafilatura extracted too little content from %s", url)
        return None

    return text


async def _fetch_with_crawl4ai(url: str) -> str | None:
    """ Headless browser via Crawl4AI for JS-rendered pages."""
    try:
        crawler = await _get_crawler()
        config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        result = await crawler.arun(url=url, config=config)

        if not result.success:
            logger.warning("Crawl4AI failed for %s: %s", url, result.error_message)
            return None

        text = str(result.markdown) if result.markdown else None
        if not text or len(text) < 50:
            logger.debug("Crawl4AI extracted too little content from %s", url)
            return None

        return text
    except Exception:
        logger.exception("Crawl4AI error for %s", url)
        return None


async def fetch_page(url: str, force_browser: bool = False) -> str | None:
    """Fetch and extract text content from a URL.

    Fast path: httpx + trafilatura (no browser).
    Fallback: Crawl4AI headless browser (JS-heavy sites or when fast path fails).

    Results are cached for 10 minutes to avoid re-fetching within a pipeline run.

    Returns extracted text, or None on failure.
    """
    cached = _check_cache(url)
    if cached is not None:
        logger.debug("Cache hit for %s", url)
        return cached

    text: str | None = None

    if not force_browser and not _is_js_heavy(url):
        text = await _fetch_with_httpx(url)

    if text is None:
        text = await _fetch_with_crawl4ai(url)

    if text is not None:
        _set_cache(url, text)

    return text


async def close() -> None:
    """Cleanup resources. Call on application shutdown."""
    global _http_client, _crawler
    if _http_client is not None and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
    if _crawler is not None:
        await _crawler.close()
        _crawler = None
