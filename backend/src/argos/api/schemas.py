import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

# -- Request schemas --


class ProductCreate(BaseModel):
    name: str
    target_price: Decimal | None = None
    currency: str = "USD"


class ProductUpdate(BaseModel):
    target_price: Decimal | None = None
    is_active: bool | None = None


# -- Response schemas --


class ProductSourceResponse(BaseModel):
    id: uuid.UUID
    url: str
    domain: str
    title: str | None
    match_confidence: float
    is_active: bool
    last_checked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PriceRecordResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    source_id: uuid.UUID
    price: Decimal
    currency: str
    in_stock: bool | None
    raw_text: str | None
    extracted_at: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    price_record_id: uuid.UUID
    alert_type: str
    channel: str
    message: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: uuid.UUID
    name: str
    search_query: str
    target_price: Decimal | None
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductDetailResponse(ProductResponse):
    sources: list[ProductSourceResponse] = []
    price_history: list[PriceRecordResponse] = []
