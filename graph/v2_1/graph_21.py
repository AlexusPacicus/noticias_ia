from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List

from langgraph.graph import END, StateGraph

from graph.v2.nodes.collect_input import collect_input
from graph.v2.nodes.dedupe import dedupe
from graph.v2.nodes.fetch_arxiv import fetch_arxiv, fetch_arxiv_with_mode
from graph.v2.nodes.fetch_huggingface import (
    fetch_huggingface,
    fetch_huggingface_with_mode,
)
from graph.v2.nodes.fetch_router import fetch_router
from graph.v2.nodes.filter_by_time_window import filter_by_time_window
from graph.v2.nodes.merge_source_units import merge_source_units
from graph.v2.nodes.normalize import normalize
from graph.v2.nodes.rank_bm25 import rank_bm25
from graph.v2.nodes.select import select
from graph.v2.nodes.summarize_reduce import summarize_reduce
from graph.v2.nodes.validate_input import validate_input
from graph.v2_1.hitl.graph_21 import hitl_review
from graph.v2_1.state import V21State
from graph.v2_1.summarize.graph_21 import summarize_map_effective, summarize_precheck


ALL_FETCH_SOURCES = ("arxiv", "huggingface")


def _normalize_sources(sources: Iterable[str] | None) -> tuple[str, ...]:
    if sources is None:
        return ALL_FETCH_SOURCES

    provided = tuple(sources)
    unknown = set(provided) - set(ALL_FETCH_SOURCES)
    if unknown:
        raise ValueError(f"Unknown sources: {sorted(unknown)}")

    ordered = tuple(source for source in ALL_FETCH_SOURCES if source in provided)
    if not ordered:
        raise ValueError("At least one source must be enabled")
    return ordered


def _default_decision_provider(_state: Dict[str, Any]) -> Dict[str, Any]:
    return {"action": "accept"}


def apply_hitl_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    if state.get("hitl_action") == "cancel":
        return {}

    selected_items: List[Dict[str, Any]] = state.get("selected_items", []) or []
    action = state.get("hitl_action")

    if action == "subset":
        remove = set(state.get("hitl_remove_keys", []) or [])
        filtered = [
            item
            for item in selected_items
            if item.get("canonical_id") not in remove
        ]
        return {"hitl_selected_items": filtered}

    return {"hitl_selected_items": selected_items}


def build_graph_21(
    *,
    live: bool = False,
    sources: Iterable[str] | None = None,
    decision_provider: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None,
):
    """
    Build the full v2.1 graph:
    Retrieval -> HITL -> Summarize.

    Notes:
    - `decision_provider` is used only by the `hitl_review` node.
    - If not provided, HITL defaults to `accept`.
    """
    mode = "live" if live else "stub"
    active_sources = _normalize_sources(sources)
    get_decision = decision_provider or _default_decision_provider

    builder = StateGraph(V21State)

    def abort_or(next_node):
        def _router(state):
            if state.get("abort_reason"):
                return END
            return next_node

        return _router

    builder.add_node("collect_input", collect_input)
    builder.add_node("validate_input", validate_input)
    builder.add_node("fetch_router", fetch_router)

    if "arxiv" in active_sources:
        if mode == "stub":
            builder.add_node("fetch_arxiv", fetch_arxiv)
        else:
            def _fetch_arxiv_node(state, _mode=mode):
                return fetch_arxiv_with_mode(state, mode=_mode)

            builder.add_node("fetch_arxiv", _fetch_arxiv_node)

    if "huggingface" in active_sources:
        if mode == "stub":
            builder.add_node("fetch_huggingface", fetch_huggingface)
        else:
            def _fetch_huggingface_node(state, _mode=mode):
                return fetch_huggingface_with_mode(state, mode=_mode)

            builder.add_node("fetch_huggingface", _fetch_huggingface_node)

    builder.add_node("merge_source_units", merge_source_units)
    builder.add_node("normalize", normalize)
    builder.add_node("filter_by_time_window", filter_by_time_window)
    builder.add_node("dedupe", dedupe)
    builder.add_node("rank_bm25", rank_bm25)
    builder.add_node("select", select)

    def _hitl_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
        decision = get_decision(state)
        return hitl_review(state, decision)

    builder.add_node("hitl_review", _hitl_review_node)
    builder.add_node("apply_hitl_decision", apply_hitl_decision)
    builder.add_node("summarize_precheck", summarize_precheck)
    builder.add_node("summarize_map", summarize_map_effective)
    builder.add_node("summarize_reduce", summarize_reduce)

    builder.set_entry_point("collect_input")

    builder.add_conditional_edges("collect_input", abort_or("validate_input"))
    builder.add_conditional_edges("validate_input", abort_or("fetch_router"))

    if "arxiv" in active_sources:
        builder.add_edge("fetch_router", "fetch_arxiv")
        builder.add_edge("fetch_arxiv", "merge_source_units")

    if "huggingface" in active_sources:
        builder.add_edge("fetch_router", "fetch_huggingface")
        builder.add_edge("fetch_huggingface", "merge_source_units")

    builder.add_conditional_edges("merge_source_units", abort_or("normalize"))
    builder.add_edge("normalize", "filter_by_time_window")
    builder.add_conditional_edges("filter_by_time_window", abort_or("dedupe"))
    builder.add_conditional_edges("dedupe", abort_or("rank_bm25"))
    builder.add_conditional_edges("rank_bm25", abort_or("select"))
    builder.add_conditional_edges("select", abort_or("hitl_review"))
    builder.add_conditional_edges("hitl_review", abort_or("apply_hitl_decision"))
    builder.add_conditional_edges("apply_hitl_decision", abort_or("summarize_precheck"))
    builder.add_conditional_edges("summarize_precheck", abort_or("summarize_map"))
    builder.add_edge("summarize_map", "summarize_reduce")
    builder.add_conditional_edges("summarize_reduce", abort_or(END))
    return builder.compile()
