from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from argos.api.routes import alerts, products
from argos.logging import setup_logging
from argos.services import fetcher


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    setup_logging()
    yield
    await fetcher.close()


app = FastAPI(
    title="Argos",
    description="Price monitoring API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}
