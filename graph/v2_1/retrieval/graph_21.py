from langgraph.graph import StateGraph, END

from graph.v2.state import V2State
from graph.v2.nodes.collect_input import collect_input
from graph.v2.nodes.validate_input import validate_input
from graph.v2.nodes.fetch_router import fetch_router
from graph.v2.nodes.fetch_arxiv import fetch_arxiv, fetch_arxiv_with_mode
from graph.v2.nodes.fetch_huggingface import (
    fetch_huggingface,
    fetch_huggingface_with_mode,
)
from graph.v2.nodes.merge_source_units import merge_source_units
from graph.v2.nodes.normalize import normalize
from graph.v2.nodes.filter_by_time_window import filter_by_time_window
from graph.v2.nodes.dedupe import dedupe
from graph.v2.nodes.rank_bm25 import rank_bm25
from graph.v2.nodes.select import select


ALL_FETCH_SOURCES = ("arxiv", "huggingface")


def _normalize_sources(sources):
    if sources is None:
        return ALL_FETCH_SOURCES

    provided = tuple(sources)
    unknown = set(provided) - set(ALL_FETCH_SOURCES)
    if unknown:
        raise ValueError(f"Unknown sources: {sorted(unknown)}")

    ordered = tuple(s for s in ALL_FETCH_SOURCES if s in provided)
    if not ordered:
        raise ValueError("At least one source must be enabled")

    return ordered


def build_retrieval_graph(live: bool = False, sources=None):
    """
    Construye el subgrafo RetrievalPhase (v2.1).

    - live=False (por defecto): comportamiento determinista (nodos stub).
    - live=True: nodos de fetch usan timestamps dinámicos recientes.
    """
    mode = "live" if live else "stub"
    active_sources = _normalize_sources(sources)

    builder = StateGraph(V2State)

    def abort_or(next_node):
        def _router(state):
            if state.get("abort_reason"):
                return END
            return next_node

        return _router

    # Nodos
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

    builder.set_entry_point("collect_input")

    def collect_phase_router(state):
        if state.get("abort_reason"):
            return END
        return "validate_input"

    builder.add_conditional_edges("collect_input", collect_phase_router)

    def input_phase_router(state):
        if state.get("abort_reason"):
            return END
        return "fetch_router"

    builder.add_conditional_edges("validate_input", input_phase_router)

    if "arxiv" in active_sources:
        builder.add_edge("fetch_router", "fetch_arxiv")
        builder.add_edge("fetch_arxiv", "merge_source_units")

    if "huggingface" in active_sources:
        builder.add_edge("fetch_router", "fetch_huggingface")
        builder.add_edge("fetch_huggingface", "merge_source_units")

    # ✅ Gate tras merge (porque puede abortar)
    builder.add_conditional_edges("merge_source_units", abort_or("normalize"))

    builder.add_edge("normalize", "filter_by_time_window")  # ✅ solo una vez

    builder.add_conditional_edges("filter_by_time_window", abort_or("dedupe"))
    builder.add_conditional_edges("dedupe", abort_or("rank_bm25"))
    builder.add_conditional_edges("rank_bm25", abort_or("select"))
    builder.add_conditional_edges("select", abort_or(END))

    return builder.compile()
