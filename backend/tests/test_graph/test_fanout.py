from collections import Counter
from unittest.mock import patch

import pytest

from argos.graph.orchestrator import compile_graph
from argos.graph.state import (
    ExtractedPrice,
    ExtractWorkerInput,
    MatchResult,
    MatchWorkerInput,
    SearchResult,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("n_results", [1, 3, 8])
async def test_each_match_triggers_exactly_one_extract(n_results):
    search_results = [
        SearchResult(url=f"https://example.com/{i}", title=f"Product {i}", snippet="")
        for i in range(n_results)
    ]

    extract_calls: Counter[str] = Counter()

    async def stub_search(state):
        return {"search_results": search_results}

    async def stub_match(state: MatchWorkerInput):
        sr = state["search_result"]
        return {
            "match_results": [
                MatchResult(
                    url=sr.url, title=sr.title, is_match=True,
                    confidence=0.9, reasoning="stub",
                )
            ]
        }

    async def stub_extract(state: ExtractWorkerInput):
        url = state["match_result"].url
        extract_calls[url] += 1
        return {
            "extracted_prices": [
                ExtractedPrice(url=url, price=10.0, currency="USD", raw_text="$10")
            ]
        }

    async def stub_save(state):
        return {}

    with (
        patch("argos.graph.orchestrator.search_node", stub_search),
        patch("argos.graph.orchestrator.match_worker_node", stub_match),
        patch("argos.graph.orchestrator.extract_worker_node", stub_extract),
        patch("argos.graph.orchestrator.save_results_node", stub_save),
    ):
        graph = compile_graph()
        await graph.ainvoke({
            "product_name": "Test",
            "product_id": "00000000-0000-0000-0000-000000000000",
            "search_results": [],
            "match_results": [],
            "extracted_prices": [],
            "errors": [],
        })

    # Each URL should be extracted exactly once.
    assert sum(extract_calls.values()) == n_results, (
        f"Expected {n_results} extract calls, got {sum(extract_calls.values())}: "
        f"{dict(extract_calls)}"
    )
    assert all(c == 1 for c in extract_calls.values()), (
        f"Some URLs extracted multiple times: {dict(extract_calls)}"
    )
