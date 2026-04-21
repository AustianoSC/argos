import logging

import httpx

from argos.config import settings
from argos.db import repositories as repo
from argos.db.models import PriceRecord, Product

logger = logging.getLogger(__name__)


async def send_discord_alert(message: str) -> bool:
    """Send an alert message to Discord via webhook."""
    if not settings.discord_webhook_url:
        logger.warning("Discord webhook URL not configured, skipping alert")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.discord_webhook_url,
                json={"content": message},
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Discord alert sent successfully")
            return True
    except httpx.HTTPError as e:
        logger.error("Failed to send Discord alert: %s", e)
        return False


async def evaluate_and_alert(
    session,  # type: ignore[no-untyped-def]
    product: Product,
    new_price: PriceRecord,
    previous_price: PriceRecord | None,
) -> None:
    """Evaluate alert conditions and send notifications if triggered.

    Conditions:
    1. Price dropped below target_price (if set)
    2. Price dropped more than X% from last observation
    3. Product came back in stock
    """
    price = float(new_price.price)
    alerts_to_send: list[tuple[str, str]] = []  # (alert_type, message)

    # 1. Below target price
    if product.target_price is not None and new_price.price < product.target_price:
        alerts_to_send.append((
            "below_target",
            f" {product.name} is now ${price:.2f} — below your target of "
            f"${float(product.target_price):.2f}!",
        ))

    # 2. Significant price drop from last observation
    if previous_price is not None:
        prev_price = float(previous_price.price)
        if prev_price > 0:
            drop_pct = ((prev_price - price) / prev_price) * 100
            if drop_pct >= settings.alert_price_drop_pct:
                alerts_to_send.append((
                    "price_drop",
                    f" {product.name} dropped {drop_pct:.1f}% — "
                    f"from ${prev_price:.2f} to ${price:.2f}",
                ))

    # 3. Back in stock
    if (
        new_price.in_stock is True
        and previous_price is not None
        and previous_price.in_stock is False
    ):
        alerts_to_send.append((
            "back_in_stock",
            f" {product.name} is back in stock at ${price:.2f}!",
        ))

    # Send alerts and persist to DB
    for alert_type, message in alerts_to_send:
        sent = await send_discord_alert(message)
        await repo.create_alert(
            session,
            product_id=product.id,
            price_record_id=new_price.id,
            alert_type=alert_type,
            channel="discord" if sent else "discord_failed",
            message=message,
        )
        logger.info("Alert triggered: %s for %s", alert_type, product.name)
