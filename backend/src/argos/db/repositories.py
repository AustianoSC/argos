import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from argos.db.models import Alert, PriceRecord, Product, ProductSource

# -- Products --


async def create_product(
    session: AsyncSession,
    name: str,
    search_query: str | None = None,
    target_price: Decimal | None = None,
    currency: str = "USD",
) -> Product:
    product = Product(
        name=name,
        search_query=search_query or name,
        target_price=target_price,
        currency=currency,
    )
    session.add(product)
    await session.flush()
    return product


async def get_product(session: AsyncSession, product_id: uuid.UUID) -> Product | None:
    return await session.get(Product, product_id)


async def get_product_with_sources(
    session: AsyncSession, product_id: uuid.UUID
) -> Product | None:
    stmt = (
        select(Product)
        .where(Product.id == product_id)
        .options(selectinload(Product.sources))
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_active_products(session: AsyncSession) -> list[Product]:
    stmt = select(Product).where(Product.is_active.is_(True)).order_by(Product.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def update_product(
    session: AsyncSession,
    product_id: uuid.UUID,
    **kwargs: Decimal | str | bool | None,
) -> Product | None:
    product = await session.get(Product, product_id)
    if product is None:
        return None
    for key, value in kwargs.items():
        setattr(product, key, value)
    product.updated_at = datetime.utcnow()
    await session.flush()
    return product


# -- Product Sources --


async def create_source(
    session: AsyncSession,
    product_id: uuid.UUID,
    url: str,
    domain: str,
    title: str | None = None,
    match_confidence: float = 0.0,
) -> ProductSource:
    source = ProductSource(
        product_id=product_id,
        url=url,
        domain=domain,
        title=title,
        match_confidence=match_confidence,
    )
    session.add(source)
    await session.flush()
    return source


async def get_active_sources(
    session: AsyncSession, product_id: uuid.UUID
) -> list[ProductSource]:
    stmt = (
        select(ProductSource)
        .where(ProductSource.product_id == product_id, ProductSource.is_active.is_(True))
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def deactivate_source(session: AsyncSession, source_id: uuid.UUID) -> None:
    source = await session.get(ProductSource, source_id)
    if source is not None:
        source.is_active = False
        source.last_checked_at = datetime.utcnow()
        await session.flush()


# -- Price Records --


async def create_price_record(
    session: AsyncSession,
    product_id: uuid.UUID,
    source_id: uuid.UUID,
    price: Decimal,
    currency: str = "USD",
    in_stock: bool | None = None,
    raw_text: str | None = None,
    metadata: dict | None = None,
) -> PriceRecord:
    record = PriceRecord(
        product_id=product_id,
        source_id=source_id,
        price=price,
        currency=currency,
        in_stock=in_stock,
        raw_text=raw_text,
        metadata_=metadata,
    )
    session.add(record)
    await session.flush()
    return record


async def get_latest_price(
    session: AsyncSession, source_id: uuid.UUID
) -> PriceRecord | None:
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.source_id == source_id)
        .order_by(PriceRecord.extracted_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_price_history(
    session: AsyncSession, product_id: uuid.UUID, limit: int = 500
) -> list[PriceRecord]:
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.product_id == product_id)
        .order_by(PriceRecord.extracted_at.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


# -- Alerts --


async def create_alert(
    session: AsyncSession,
    product_id: uuid.UUID,
    price_record_id: uuid.UUID,
    alert_type: str,
    channel: str,
    message: str,
) -> Alert:
    alert = Alert(
        product_id=product_id,
        price_record_id=price_record_id,
        alert_type=alert_type,
        channel=channel,
        message=message,
    )
    session.add(alert)
    await session.flush()
    return alert


async def list_alerts(
    session: AsyncSession,
    product_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[Alert]:
    stmt = select(Alert).order_by(Alert.sent_at.desc()).limit(limit)
    if product_id is not None:
        stmt = stmt.where(Alert.product_id == product_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())
