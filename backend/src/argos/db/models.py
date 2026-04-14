import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(500))
    search_query: Mapped[str] = mapped_column(String(500))
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    sources: Mapped[list["ProductSource"]] = relationship(back_populates="product")
    prices: Mapped[list["PriceRecord"]] = relationship(back_populates="product")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="product")

    def __repr__(self) -> str:
        return f"<Product {self.name!r}>"


class ProductSource(Base):
    __tablename__ = "product_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    url: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(200))
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    match_confidence: Mapped[float] = mapped_column()
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="sources")
    prices: Mapped[list["PriceRecord"]] = relationship(back_populates="source")

    __table_args__ = (
        Index("ix_product_sources_product_active", "product_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<ProductSource {self.domain} for {self.product_id}>"


class PriceRecord(Base):
    __tablename__ = "price_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_sources.id"))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(3))
    in_stock: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    product: Mapped["Product"] = relationship(back_populates="prices")
    source: Mapped["ProductSource"] = relationship(back_populates="prices")

    __table_args__ = (
        Index("ix_price_records_product_time", "product_id", "extracted_at"),
        Index("ix_price_records_source_time", "source_id", "extracted_at"),
    )

    def __repr__(self) -> str:
        return f"<PriceRecord {self.price} {self.currency} at {self.extracted_at}>"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"))
    price_record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("price_records.id"))
    alert_type: Mapped[str] = mapped_column(String(50))
    channel: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert {self.alert_type} for {self.product_id}>"
