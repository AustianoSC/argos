import logging
import uuid
from http import HTTPStatus

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from argos.api.schemas import (
    PriceRecordResponse,
    ProductCreate,
    ProductDetailResponse,
    ProductResponse,
    ProductSourceResponse,
    ProductUpdate,
)
from argos.db import repositories as repo
from argos.db.engine import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


async def _run_pipeline(product_id: str, product_name: str) -> None:
    """Run the LangGraph pipeline in the background."""
    from argos.graph.orchestrator import compile_graph

    graph = compile_graph()
    try:
        await graph.ainvoke(
            {
                "product_name": product_name,
                "product_id": product_id,
                "search_results": [],
                "match_results": [],
                "extracted_prices": [],
                "errors": [],
            }
        )
        logger.info("Pipeline completed for product %s", product_id)
    except Exception:
        logger.exception("Pipeline failed for product %s", product_id)


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    body: ProductCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> ProductResponse:
    """Create a new product watch and trigger the search pipeline."""
    product = await repo.create_product(
        session,
        name=body.name,
        target_price=body.target_price,
        currency=body.currency,
    )
    await session.commit()

    background_tasks.add_task(_run_pipeline, str(product.id), product.name)

    return ProductResponse.model_validate(product)


@router.get("", response_model=list[ProductResponse])
async def list_products(
    session: AsyncSession = Depends(get_session),
) -> list[ProductResponse]:
    """List all active products."""
    products = await repo.list_active_products(session)
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(
    product_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ProductDetailResponse:
    """Get product details with sources and price history."""
    product = await repo.get_product_with_sources(session, product_id)
    if product is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Product not found")

    price_history = await repo.get_price_history(session, product_id)

    return ProductDetailResponse(
        **ProductResponse.model_validate(product).model_dump(),
        sources=[ProductSourceResponse.model_validate(s) for s in product.sources],
        price_history=[PriceRecordResponse.model_validate(p) for p in price_history],
    )


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProductResponse:
    """Update a product (target price, active status)."""
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="No fields to update")

    product = await repo.update_product(session, product_id, **update_data)
    if product is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Product not found")

    await session.commit()
    return ProductResponse.model_validate(product)


@router.post("/{product_id}/check", status_code=202)
async def trigger_check(
    product_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger a manual price re-check for a product."""
    product = await repo.get_product(session, product_id)
    if product is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Product not found")

    background_tasks.add_task(_run_pipeline, str(product.id), product.name)

    return {"status": "check_queued", "product_id": str(product_id)}
