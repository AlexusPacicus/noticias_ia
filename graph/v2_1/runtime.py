from __future__ import annotations

from typing import Any, Callable, Dict, Iterable

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
from graph.v2_1.summarize.summarize_map import summarize_map


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


def _normalize_execute_until(execute_until: str) -> str:
    if execute_until not in {"select", "summary"}:
        raise ValueError("execute_until must be 'select' or 'summary'")
    return execute_until


def _abort_or(next_node: str):
    def _router(state: Dict[str, Any]):
        if state.get("abort_reason"):
            return END
        return next_node

    return _router


def _build_fetch_arxiv_node(*, mode: str, enabled: bool):
    if not enabled:
        def _disabled(_state: Dict[str, Any]) -> Dict[str, Any]:
            return {}

        return _disabled

    if mode == "stub":
        return fetch_arxiv

    def _fetch_arxiv_live(state: Dict[str, Any], _mode: str = mode) -> Dict[str, Any]:
        return fetch_arxiv_with_mode(state, mode=_mode)

    return _fetch_arxiv_live


def _build_fetch_hf_node(*, mode: str, enabled: bool):
    if not enabled:
        def _disabled(_state: Dict[str, Any]) -> Dict[str, Any]:
            return {}

        return _disabled

    if mode == "stub":
        return fetch_huggingface

    def _fetch_hf_live(state: Dict[str, Any], _mode: str = mode) -> Dict[str, Any]:
        return fetch_huggingface_with_mode(state, mode=_mode)

    return _fetch_hf_live


def build_graph(
    *,
    live: bool = False,
    sources: Iterable[str] | None = None,
    decision_provider: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None,
):
    mode = "live" if live else "stub"
    active_sources = _normalize_sources(sources)
    get_decision = decision_provider or _default_decision_provider

    builder = StateGraph(V21State)

    builder.add_node("collect_input", collect_input)
    builder.add_node("validate_input", validate_input)
    builder.add_node("fetch_router", fetch_router)
    builder.add_node(
        "fetch_arxiv",
        _build_fetch_arxiv_node(mode=mode, enabled="arxiv" in active_sources),
    )
    builder.add_node(
        "fetch_huggingface",
        _build_fetch_hf_node(mode=mode, enabled="huggingface" in active_sources),
    )
    builder.add_node("merge_source_units", merge_source_units)
    builder.add_node("normalize", normalize)
    builder.add_node("filter_by_time_window", filter_by_time_window)
    builder.add_node("dedupe", dedupe)
    builder.add_node("rank_bm25", rank_bm25)
    builder.add_node("select", select)

    def _hitl_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return hitl_review(state, get_decision(state))

    builder.add_node("hitl_review", _hitl_review_node)
    builder.add_node("summarize_map", summarize_map)
    builder.add_node("summarize_reduce", summarize_reduce)

    builder.set_entry_point("collect_input")

    builder.add_conditional_edges("collect_input", _abort_or("validate_input"))
    builder.add_conditional_edges("validate_input", _abort_or("fetch_router"))
    builder.add_conditional_edges("fetch_router", _abort_or("fetch_arxiv"))
    builder.add_conditional_edges("fetch_arxiv", _abort_or("fetch_huggingface"))
    builder.add_conditional_edges("fetch_huggingface", _abort_or("merge_source_units"))
    builder.add_conditional_edges("merge_source_units", _abort_or("normalize"))
    builder.add_conditional_edges("normalize", _abort_or("filter_by_time_window"))
    builder.add_conditional_edges("filter_by_time_window", _abort_or("dedupe"))
    builder.add_conditional_edges("dedupe", _abort_or("rank_bm25"))
    builder.add_conditional_edges("rank_bm25", _abort_or("select"))
    builder.add_conditional_edges("select", _abort_or("hitl_review"))
    builder.add_conditional_edges("hitl_review", _abort_or("summarize_map"))
    builder.add_conditional_edges("summarize_map", _abort_or("summarize_reduce"))
    builder.add_conditional_edges("summarize_reduce", _abort_or(END))

    return builder.compile()


def build_retrieval_graph(
    *,
    live: bool = False,
    sources: Iterable[str] | None = None,
):
    mode = "live" if live else "stub"
    active_sources = _normalize_sources(sources)

    builder = StateGraph(V21State)

    builder.add_node("collect_input", collect_input)
    builder.add_node("validate_input", validate_input)
    builder.add_node("fetch_router", fetch_router)
    builder.add_node(
        "fetch_arxiv",
        _build_fetch_arxiv_node(mode=mode, enabled="arxiv" in active_sources),
    )
    builder.add_node(
        "fetch_huggingface",
        _build_fetch_hf_node(mode=mode, enabled="huggingface" in active_sources),
    )
    builder.add_node("merge_source_units", merge_source_units)
    builder.add_node("normalize", normalize)
    builder.add_node("filter_by_time_window", filter_by_time_window)
    builder.add_node("dedupe", dedupe)
    builder.add_node("rank_bm25", rank_bm25)
    builder.add_node("select", select)

    builder.set_entry_point("collect_input")

    builder.add_conditional_edges("collect_input", _abort_or("validate_input"))
    builder.add_conditional_edges("validate_input", _abort_or("fetch_router"))
    builder.add_conditional_edges("fetch_router", _abort_or("fetch_arxiv"))
    builder.add_conditional_edges("fetch_arxiv", _abort_or("fetch_huggingface"))
    builder.add_conditional_edges("fetch_huggingface", _abort_or("merge_source_units"))
    builder.add_conditional_edges("merge_source_units", _abort_or("normalize"))
    builder.add_conditional_edges("normalize", _abort_or("filter_by_time_window"))
    builder.add_conditional_edges("filter_by_time_window", _abort_or("dedupe"))
    builder.add_conditional_edges("dedupe", _abort_or("rank_bm25"))
    builder.add_conditional_edges("rank_bm25", _abort_or("select"))
    builder.add_conditional_edges("select", _abort_or(END))

    return builder.compile()


def build_hitl_graph(
    decision_provider: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None,
):
    get_decision = decision_provider or _default_decision_provider
    builder = StateGraph(V21State)

    def _hitl_review_node(state: Dict[str, Any]) -> Dict[str, Any]:
        return hitl_review(state, get_decision(state))

    builder.add_node("hitl_review", _hitl_review_node)
    builder.set_entry_point("hitl_review")
    builder.add_conditional_edges("hitl_review", _abort_or(END))
    return builder.compile()


def build_summarize_graph():
    builder = StateGraph(V21State)
    builder.add_node("summarize_map", summarize_map)
    builder.add_node("summarize_reduce", summarize_reduce)
    builder.set_entry_point("summarize_map")
    builder.add_conditional_edges("summarize_map", _abort_or("summarize_reduce"))
    builder.add_conditional_edges("summarize_reduce", _abort_or(END))
    return builder.compile()


def run_system(
    payload: Dict[str, Any],
    *,
    execute_until: str = "summary",
    live: bool = False,
    sources: Iterable[str] | None = None,
    decision_provider: Callable[[Dict[str, Any]], Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    mode = _normalize_execute_until(execute_until)
    if mode == "select":
        graph = build_retrieval_graph(live=live, sources=sources)
    else:
        graph = build_graph(
            live=live,
            sources=sources,
            decision_provider=decision_provider,
        )
    return graph.invoke(payload)
