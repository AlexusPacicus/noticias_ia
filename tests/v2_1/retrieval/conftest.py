from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import pytest

from graph.v2_1.retrieval.graph_21 import build_retrieval_graph


FIXED_NOW_UTC = datetime(2025, 1, 10, tzinfo=timezone.utc)
FETCHED_AT = "2025-01-10T00:00:00Z"
PUBLISHED_AT_IN_WINDOW = "2025-01-09T00:00:00Z"


@pytest.fixture
def payload_valid() -> dict[str, Any]:
    return {
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 2,
    }


@pytest.fixture
def fixed_now_utc() -> datetime:
    return FIXED_NOW_UTC


@pytest.fixture
def retrieval_allowed_keys() -> set[str]:
    return {
        "query",
        "time_window",
        "top_k",
        "input_raw",
        "input_validated",
        "source_units",
        "merged_source_units",
        "normalized_items",
        "filtered_items",
        "deduped_items",
        "ranked_items",
        "selected_items",
        "abort_reason",
    }


@pytest.fixture
def llm_forbidden_keys() -> set[str]:
    return {
        "summary_items",
        "summary_stats",
        "output",
    }


@pytest.fixture
def make_source_item() -> Callable[..., dict[str, Any]]:
    def _make_source_item(
        *,
        source: str,
        source_seq: int,
        title: str,
        content: str,
        published_at: str,
        link: str,
        fetched_at: str = FETCHED_AT,
    ) -> dict[str, Any]:
        return {
            "source": source,
            "source_seq": source_seq,
            "fetched_at": fetched_at,
            "payload": {
                "title": title,
                "content": content,
                "published_at": published_at,
                "link": link,
            },
        }

    return _make_source_item


@pytest.fixture
def nominal_arxiv_items(make_source_item) -> list[dict[str, Any]]:
    return [
        make_source_item(
            source="arxiv",
            source_seq=0,
            title="Agentic AI for X",
            content="agentic systems and planning",
            published_at=PUBLISHED_AT_IN_WINDOW,
            link="https://arxiv.org/abs/2501.00001",
        ),
        make_source_item(
            source="arxiv",
            source_seq=1,
            title="Tool Use in LLMs",
            content="tools agents and agentic workflows",
            published_at=PUBLISHED_AT_IN_WINDOW,
            link="https://arxiv.org/abs/2501.00002",
        ),
    ]


@pytest.fixture
def nominal_hf_items(make_source_item) -> list[dict[str, Any]]:
    return [
        make_source_item(
            source="huggingface",
            source_seq=0,
            title="Daily Paper A",
            content="agentic ai overview",
            published_at=PUBLISHED_AT_IN_WINDOW,
            link="https://huggingface.co/papers/2025-01-09",
        )
    ]


@pytest.fixture
def patch_fetch_snapshot(monkeypatch):
    def _patch(
        *,
        arxiv_items: list[dict[str, Any]] | None = None,
        hf_items: list[dict[str, Any]] | None = None,
        arxiv_status: str = "ok",
        hf_status: str = "ok",
        arxiv_error: dict[str, Any] | None = None,
        hf_error: dict[str, Any] | None = None,
    ) -> None:
        a_items = [] if arxiv_items is None else arxiv_items
        h_items = [] if hf_items is None else hf_items

        def fixed_fetch_arxiv(_state):
            status = arxiv_status
            error = None
            items = a_items
            if status != "ok":
                items = []
                error = arxiv_error or {"code": "ARXIV_FETCH_ERROR", "message": "forced"}
            return {
                "source_units": {
                    "arxiv": {
                        "status": status,
                        "error": error,
                        "items": items,
                    }
                }
            }

        def fixed_fetch_hf(_state):
            status = hf_status
            error = None
            items = h_items
            if status != "ok":
                items = []
                error = hf_error or {"code": "HF_FETCH_ERROR", "message": "forced"}
            return {
                "source_units": {
                    "huggingface": {
                        "status": status,
                        "error": error,
                        "items": items,
                    }
                }
            }

        monkeypatch.setattr("graph.v2_1.retrieval.graph_21.fetch_arxiv", fixed_fetch_arxiv)
        monkeypatch.setattr(
            "graph.v2_1.retrieval.graph_21.fetch_huggingface",
            fixed_fetch_hf,
        )

    return _patch


@pytest.fixture
def patch_now_utc(monkeypatch):
    def _patch(fixed_now: datetime) -> None:
        monkeypatch.setattr("graph.v2.nodes.filter_by_time_window._now_utc", lambda: fixed_now)

    return _patch


@pytest.fixture
def invoke_retrieval():
    def _invoke(payload: dict[str, Any], *, sources=None) -> dict[str, Any]:
        graph = build_retrieval_graph(live=False, sources=sources)
        return graph.invoke(payload)

    return _invoke


@pytest.fixture
def assert_exact_keys():
    def _assert(state: dict[str, Any], expected_keys: set[str]) -> None:
        assert set(state.keys()) == set(expected_keys)

    return _assert


@pytest.fixture
def assert_no_keys_after():
    def _assert(state: dict[str, Any], forbidden_after_keys: set[str]) -> None:
        for key in forbidden_after_keys:
            assert key not in state

    return _assert


@pytest.fixture
def assert_order_total():
    def _assert(ranked_items: list[dict[str, Any]]) -> None:
        assert isinstance(ranked_items, list)
        tuples = []
        for idx, item in enumerate(ranked_items, start=1):
            assert "bm25_score" in item
            assert "title" in item
            assert "link" in item
            assert item.get("rank_position") == idx
            tuples.append((-item["bm25_score"], item["title"], item["link"]))
        assert tuples == sorted(tuples)

    return _assert


@pytest.fixture
def assert_abort_reason():
    def _assert(state: dict[str, Any], expected: str) -> None:
        assert state.get("abort_reason") == expected

    return _assert


@pytest.fixture
def assert_input_not_overwritten():
    def _assert(state: dict[str, Any], payload: dict[str, Any]) -> None:
        for key in ("query", "time_window", "top_k"):
            assert state.get(key) == payload.get(key)

    return _assert


@pytest.fixture
def assert_allowed_retrieval_keys_only(retrieval_allowed_keys):
    def _assert(state: dict[str, Any]) -> None:
        assert set(state.keys()).issubset(retrieval_allowed_keys)

    return _assert


@pytest.fixture
def assert_no_llm_keys(llm_forbidden_keys):
    def _assert(state: dict[str, Any]) -> None:
        for key in llm_forbidden_keys:
            assert key not in state

    return _assert


@pytest.fixture
def assert_missing_ranked_items_for_select_missing():
    def _assert(state: dict[str, Any]) -> None:
        assert state.get("abort_reason") == "SELECT_MISSING_RANKED_ITEMS"
        assert "ranked_items" not in state

    return _assert
