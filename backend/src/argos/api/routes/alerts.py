import logging
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from argos.api.schemas import AlertResponse
from argos.db import repositories as repo
from argos.db.engine import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    product_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
) -> list[AlertResponse]:
    """List alerts, optionally filtered by product."""
    alerts = await repo.list_alerts(session, product_id=product_id, limit=limit)
    return [AlertResponse.model_validate(a) for a in alerts]
