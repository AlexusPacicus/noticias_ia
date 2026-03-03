from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pytest

from graph.v2_1.summarize.graph_21 import build_summarize_graph


@pytest.fixture
def make_selected_item() -> Callable[..., dict[str, Any]]:
    def _make_selected_item(
        *,
        canonical_id: str,
        rank_position: int,
        title: str,
        link: str,
        source: str = "arxiv",
    ) -> dict[str, Any]:
        return {
            "canonical_id": canonical_id,
            "rank_position": rank_position,
            "title": title,
            "link": link,
            "source": source,
            "content": f"content::{canonical_id}",
        }

    return _make_selected_item


@pytest.fixture
def selected_items_nominal(make_selected_item) -> list[dict[str, Any]]:
    return [
        make_selected_item(
            canonical_id="arxiv:2501.00010",
            rank_position=10,
            title="Paper 10",
            link="https://arxiv.org/abs/2501.00010",
        ),
        make_selected_item(
            canonical_id="arxiv:2501.00002",
            rank_position=2,
            title="Paper 2",
            link="https://arxiv.org/abs/2501.00002",
        ),
        make_selected_item(
            canonical_id="hf:2025-01-09:p1",
            rank_position=7,
            title="Paper 7",
            link="https://huggingface.co/papers/2025-01-09",
            source="huggingface",
        ),
    ]


@pytest.fixture
def input_validated() -> dict[str, Any]:
    return {
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 3,
    }


@pytest.fixture
def base_state(selected_items_nominal, input_validated) -> dict[str, Any]:
    return {
        "selected_items": deepcopy(selected_items_nominal),
        "input_validated": deepcopy(input_validated),
    }


@pytest.fixture
def invoke_summarize():
    def _invoke(state: dict[str, Any]) -> dict[str, Any]:
        graph = build_summarize_graph()
        return graph.invoke(deepcopy(state))

    return _invoke


@pytest.fixture
def assert_structural_invariants():
    def _assert(before: dict[str, Any], after: dict[str, Any]) -> None:
        allowed_new = {"summary_items", "summary_stats", "output", "abort_reason"}
        extra_keys = set(after.keys()) - set(before.keys())
        assert extra_keys.issubset(allowed_new)

        assert before.get("selected_items") == after.get("selected_items")
        if "output" in after:
            assert "abort_reason" not in after
        if "abort_reason" in after:
            assert "output" not in after

    return _assert
