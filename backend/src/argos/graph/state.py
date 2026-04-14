from operator import add
from typing import Annotated, TypedDict

from pydantic import BaseModel


class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str


class MatchResult(BaseModel):
    url: str
    title: str
    is_match: bool
    confidence: float
    reasoning: str


class ExtractedPrice(BaseModel):
    url: str
    price: float
    currency: str
    in_stock: bool | None = None
    seller: str | None = None
    raw_text: str


# -- Main orchestrator state --
class PipelineState(TypedDict):
    # Input
    product_name: str
    product_id: str  # UUID as string

    # Search phase output (overwritten by search node)
    search_results: list[SearchResult]

    # Match phase output (accumulated via reducer)
    match_results: Annotated[list[MatchResult], add]

    # Extract phase output (accumulated via reducer)
    extracted_prices: Annotated[list[ExtractedPrice], add]

    # Error tracking
    errors: Annotated[list[str], add]


# -- Worker sub-states for Send() fan-out --
class MatchWorkerInput(TypedDict):
    product_name: str
    product_id: str
    search_result: SearchResult


class ExtractWorkerInput(TypedDict):
    product_name: str
    product_id: str
    match_result: MatchResult
