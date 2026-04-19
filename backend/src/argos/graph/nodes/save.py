import logging
import uuid
from decimal import Decimal
from urllib.parse import urlparse

from argos.db import repositories as repo
from argos.db.engine import async_session_factory
from argos.graph.state import PipelineState

logger = logging.getLogger(__name__)


async def save_results_node(state: PipelineState) -> dict:
    """Persist extracted prices to the database.

    For each extracted price:
    1. Create or find the ProductSource
    2. Create a PriceRecord
    All writes are committed atomically.
    """
    product_id_str = state["product_id"]
    extracted_prices = state.get("extracted_prices", [])

    if not extracted_prices:
        logger.info("No prices to save for product %s", product_id_str)
        return {}

    product_id = uuid.UUID(product_id_str)
    saved_count = 0

    async with async_session_factory() as session:
        for price_data in extracted_prices:
            try:
                domain = urlparse(price_data.url).netloc.lower()

                # Find the match result for this URL to get confidence
                match_confidence = 0.0
                for match in state.get("match_results", []):
                    if match.url == price_data.url and match.is_match:
                        match_confidence = match.confidence
                        break

                source = await repo.create_source(
                    session,
                    product_id=product_id,
                    url=price_data.url,
                    domain=domain,
                    title=None,
                    match_confidence=match_confidence,
                )

                await repo.create_price_record(
                    session,
                    product_id=product_id,
                    source_id=source.id,
                    price=Decimal(str(price_data.price)),
                    currency=price_data.currency,
                    in_stock=price_data.in_stock,
                    raw_text=price_data.raw_text,
                    metadata={"seller": price_data.seller} if price_data.seller else None,
                )

                saved_count += 1
            except Exception as e:
                logger.error("Failed to save price for %s: %s", price_data.url, e)

        await session.commit()

    logger.info("Saved %d/%d prices for product %s", saved_count, len(extracted_prices), product_id_str)
    return {}
