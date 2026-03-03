from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

import pytest

from graph.v2_1.hitl.graph_21 import build_hitl_graph, hitl_review


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
        }

    return _make_selected_item


@pytest.fixture
def selected_items_nominal(make_selected_item) -> list[dict[str, Any]]:
    return [
        make_selected_item(
            canonical_id="arxiv:2501.00001",
            rank_position=1,
            title="Agentic AI for X",
            link="https://arxiv.org/abs/2501.00001",
        ),
        make_selected_item(
            canonical_id="arxiv:2501.00002",
            rank_position=2,
            title="Tool Use in LLMs",
            link="https://arxiv.org/abs/2501.00002",
        ),
        make_selected_item(
            canonical_id="hf:2025-01-09:paper-a",
            rank_position=3,
            title="Daily Paper A",
            link="https://huggingface.co/papers/2025-01-09",
            source="huggingface",
        ),
    ]


@pytest.fixture
def state_with_selected(selected_items_nominal) -> dict[str, Any]:
    return {"selected_items": deepcopy(selected_items_nominal)}


@pytest.fixture
def hitl_allowed_new_keys() -> set[str]:
    return {"hitl_action", "hitl_remove_keys", "abort_reason"}


@pytest.fixture
def summarize_forbidden_keys() -> set[str]:
    return {"summary_items", "summary_stats", "output"}


@pytest.fixture
def invoke_hitl():
    def _invoke(state: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        graph = build_hitl_graph(lambda _state: decision)
        return graph.invoke(deepcopy(state))

    return _invoke


@pytest.fixture
def invoke_hitl_node():
    def _invoke(state: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
        merged = deepcopy(state)
        merged.update(hitl_review(merged, decision))
        return merged

    return _invoke


@pytest.fixture
def assert_selected_items_not_mutated():
    def _assert(before: dict[str, Any], after: dict[str, Any]) -> None:
        assert before.get("selected_items") == after.get("selected_items")

    return _assert


@pytest.fixture
def assert_hitl_domain_only(hitl_allowed_new_keys):
    def _assert(before: dict[str, Any], after: dict[str, Any]) -> None:
        before_keys = set(before.keys())
        after_keys = set(after.keys())

        # 1️⃣ No claves nuevas fuera de dominio
        extra_keys = after_keys - before_keys
        assert extra_keys.issubset(hitl_allowed_new_keys)

        # 2️⃣ No modificación de claves previas (excepto las permitidas)
        for key in before_keys:
            if key not in hitl_allowed_new_keys:
                assert after[key] == before[key]

    return _assert

@pytest.fixture
def assert_no_summarize_keys(summarize_forbidden_keys):
    def _assert(state: dict[str, Any]) -> None:
        for key in summarize_forbidden_keys:
            assert key not in state

    return _assert
