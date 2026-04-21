import logging
import uuid
from datetime import UTC
from decimal import Decimal

from arq import cron
from arq.connections import RedisSettings

from argos.config import settings
from argos.db import repositories as repo
from argos.db.engine import async_session_factory
from argos.graph.state import ExtractedPrice
from argos.logging import setup_logging
from argos.services.alerts import evaluate_and_alert
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


async def extract_price_from_source(product_name: str, url: str) -> ExtractedPrice | None:
    """Fetch a page and extract price using the LLM. Shared by worker tasks."""
    content = await fetch_page(url)
    if content is None:
        logger.warning("Could not fetch %s for extraction", url)
        return None

    truncated = content[:MAX_CONTENT_LENGTH]
    llm = get_extract_llm().with_structured_output(ExtractedPrice)
    prompt = EXTRACT_PROMPT.format(product_name=product_name, url=url, content=truncated)

    try:
        result = await llm.ainvoke(prompt)
        result.url = url
        return result
    except Exception as e:
        logger.error("LLM extraction failed for %s: %s", url, e)
        return None


async def check_product_prices(ctx: dict, product_id: str) -> None:
    """Re-check prices for a single product's active sources."""
    pid = uuid.UUID(product_id)
    logger.info("Checking prices for product %s", product_id)

    async with async_session_factory() as session:
        product = await repo.get_product(session, pid)
        if product is None or not product.is_active:
            logger.warning("Product %s not found or inactive, skipping", product_id)
            return

        sources = await repo.get_active_sources(session, pid)
        if not sources:
            logger.info("No active sources for product %s", product_id)
            return

        for source in sources:
            try:
                extracted = await extract_price_from_source(product.name, source.url)
                if extracted is None:
                    continue

                previous_price = await repo.get_latest_price(session, source.id)

                price_record = await repo.create_price_record(
                    session,
                    product_id=pid,
                    source_id=source.id,
                    price=Decimal(str(extracted.price)),
                    currency=extracted.currency,
                    in_stock=extracted.in_stock,
                    raw_text=extracted.raw_text,
                    metadata={"seller": extracted.seller} if extracted.seller else None,
                )

                source.last_checked_at = UTC.now()
                await evaluate_and_alert(session, product, price_record, previous_price)

                logger.info(
                    "Updated price for %s from %s: %s %s",
                    product.name,
                    source.domain,
                    extracted.price,
                    extracted.currency,
                )
            except Exception as e:
                logger.error("Failed to check source %s: %s", source.url, e)

        await session.commit()


async def check_all_products(ctx: dict) -> None:
    """Scheduled job: re-check prices for all active products."""
    logger.info("Starting scheduled price check for all products")

    async with async_session_factory() as session:
        products = await repo.list_active_products(session)

    for product in products:
        await check_product_prices(ctx, str(product.id))

    logger.info("Completed scheduled price check for %d products", len(products))


async def startup(ctx: dict) -> None:
    setup_logging()
    logger.info("ARQ worker started")


async def shutdown(ctx: dict) -> None:
    from argos.services.fetcher import close
    await close()
    logger.info("ARQ worker stopped")


class WorkerSettings:
    functions = [check_product_prices]
    cron_jobs = [
        cron(
            check_all_products,
            hour={0, 6, 12, 18},
            run_at_startup=False,
        ),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
