from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import pytest

from graph.v2_1.graph_21 import build_graph_21
from graph.v2_1.retrieval.graph_21 import build_retrieval_graph


FIXED_NOW_UTC = datetime(2026, 3, 3, tzinfo=timezone.utc)
PUBLISHED_AT_IN_WINDOW = "2026-03-02T00:00:00Z"
FETCHED_AT = "2026-03-03T00:00:00Z"


@pytest.fixture
def payload_valid() -> dict[str, Any]:
    return {
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 3,
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
            content="tools agents and workflows",
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
            link="https://huggingface.co/papers/2026-03-02",
        )
    ]


@pytest.fixture
def patch_now_utc(monkeypatch):
    def _patch() -> None:
        monkeypatch.setattr(
            "graph.v2.nodes.filter_by_time_window._now_utc",
            lambda: FIXED_NOW_UTC,
        )

    return _patch


@pytest.fixture
def patch_fetch_snapshot(monkeypatch):
    def _patch(
        *,
        arxiv_items: list[dict[str, Any]] | None = None,
        hf_items: list[dict[str, Any]] | None = None,
        arxiv_status: str = "ok",
        hf_status: str = "ok",
    ) -> None:
        a_items = [] if arxiv_items is None else arxiv_items
        h_items = [] if hf_items is None else hf_items

        def fixed_fetch_arxiv(_state):
            return {
                "source_units": {
                    "arxiv": {
                        "status": arxiv_status,
                        "error": None if arxiv_status == "ok" else {"code": "ARXIV_ERR"},
                        "items": a_items if arxiv_status == "ok" else [],
                    }
                }
            }

        def fixed_fetch_hf(_state):
            return {
                "source_units": {
                    "huggingface": {
                        "status": hf_status,
                        "error": None if hf_status == "ok" else {"code": "HF_ERR"},
                        "items": h_items if hf_status == "ok" else [],
                    }
                }
            }

        monkeypatch.setattr("graph.v2_1.graph_21.fetch_arxiv", fixed_fetch_arxiv)
        monkeypatch.setattr("graph.v2_1.graph_21.fetch_huggingface", fixed_fetch_hf)
        monkeypatch.setattr(
            "graph.v2_1.retrieval.graph_21.fetch_arxiv",
            fixed_fetch_arxiv,
        )
        monkeypatch.setattr(
            "graph.v2_1.retrieval.graph_21.fetch_huggingface",
            fixed_fetch_hf,
        )

    return _patch


@pytest.fixture
def invoke_full():
    def _invoke(
        payload: dict[str, Any],
        *,
        decision_provider=None,
        sources=None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        graph = build_graph_21(live=False, sources=sources, decision_provider=decision_provider)
        return graph.invoke(payload, config=config)

    return _invoke


@pytest.fixture
def invoke_retrieval():
    def _invoke(payload: dict[str, Any], *, sources=None) -> dict[str, Any]:
        graph = build_retrieval_graph(live=False, sources=sources)
        return graph.invoke(payload)

    return _invoke


@pytest.fixture
def assert_global_invariants():
    allowed_keys = {
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
        "hitl_action",
        "hitl_remove_keys",
        "summary_items",
        "summary_stats",
        "output",
        "abort_reason",
    }

    def _assert(state: dict[str, Any]) -> None:
        assert set(state.keys()).issubset(allowed_keys)
        assert not ("output" in state and "abort_reason" in state)

    return _assert
