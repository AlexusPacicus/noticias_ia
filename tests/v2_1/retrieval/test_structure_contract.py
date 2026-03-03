from __future__ import annotations

import pytest

import graph.v2_1.retrieval.graph_21 as graph_21


TRACE_NODES = [
    "collect_input",
    "validate_input",
    "fetch_router",
    "fetch_arxiv",
    "fetch_huggingface",
    "merge_source_units",
    "normalize",
    "filter_by_time_window",
    "dedupe",
    "rank_bm25",
    "select",
]


def _patch_trace(monkeypatch, events):
    for node_name in TRACE_NODES:
        original = getattr(graph_21, node_name)

        def wrapped(state, _original=original, _node_name=node_name):
            events.append(_node_name)
            return _original(state)

        monkeypatch.setattr(graph_21, node_name, wrapped)


def _expected_trace_for_sources(sources):
    if sources is None:
        fetch_nodes = ["fetch_arxiv", "fetch_huggingface"]
    else:
        fetch_nodes = []
        if "arxiv" in sources:
            fetch_nodes.append("fetch_arxiv")
        if "huggingface" in sources:
            fetch_nodes.append("fetch_huggingface")

    return [
        "collect_input",
        "validate_input",
        "fetch_router",
        *fetch_nodes,
        "merge_source_units",
        "normalize",
        "filter_by_time_window",
        "dedupe",
        "rank_bm25",
        "select",
    ]


@pytest.mark.parametrize(
    "sources",
    [
        None,
        ("arxiv",),
        ("huggingface",),
    ],
)
def test_execution_trace_nominal(
    sources,
    monkeypatch,
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    fixed_now_utc,
):
    patch_now_utc(fixed_now_utc)
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    events = []
    _patch_trace(monkeypatch, events)

    state = invoke_retrieval(payload_valid, sources=sources)

    assert "abort_reason" not in state
    assert events == _expected_trace_for_sources(sources)


def test_execution_trace_abort_gate_c(
    monkeypatch,
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    make_source_item,
    fixed_now_utc,
):
    patch_now_utc(fixed_now_utc)

    stale_arxiv_items = [
        make_source_item(
            source="arxiv",
            source_seq=0,
            title="Old Paper 1",
            content="agentic ai",
            published_at="2024-01-01T00:00:00Z",
            link="https://arxiv.org/abs/2401.00001",
        )
    ]
    stale_hf_items = [
        make_source_item(
            source="huggingface",
            source_seq=0,
            title="Old Paper 2",
            content="agentic ai",
            published_at="2024-01-01T00:00:00Z",
            link="https://huggingface.co/papers/2024-01-01",
        )
    ]
    patch_fetch_snapshot(arxiv_items=stale_arxiv_items, hf_items=stale_hf_items)

    events = []
    _patch_trace(monkeypatch, events)

    state = invoke_retrieval(payload_valid)

    assert state.get("abort_reason") == "NO_ITEMS_IN_TIME_WINDOW"
    assert events == [
        "collect_input",
        "validate_input",
        "fetch_router",
        "fetch_arxiv",
        "fetch_huggingface",
        "merge_source_units",
        "normalize",
        "filter_by_time_window",
    ]
    assert "dedupe" not in events
    assert "rank_bm25" not in events
    assert "select" not in events
