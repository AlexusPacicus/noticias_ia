"""
Grafo LangGraph del pipeline v1.1.

StateGraph tipado con conditional edges para abort handling nativo.
El grafo compilado ES el runtime: graph.invoke({...}).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from graph.nodes.collect_input import collect_input
from graph.nodes.fetch import fetch
from graph.nodes.normalize import normalize
from graph.nodes.rank import rank
from graph.nodes.select import select
from graph.nodes.summarize import summarize
from graph.nodes.validate_input import validate_input
from graph.state import InputState, OutputState, PipelineState


def _abort_or(next_node: str):
    """Fabrica un router: si hay abort_reason -> END, si no -> next_node."""

    def router(state: PipelineState) -> str:
        if state.get("abort_reason"):
            return END
        return next_node

    return router


def build_graph():
    """Construye y compila el grafo del pipeline."""
    g = StateGraph(
        PipelineState,
        input_schema=InputState,
        output_schema=OutputState,
    )

    g.add_node("collect_input", collect_input)
    g.add_node("validate_input", validate_input)
    g.add_node("fetch", fetch)
    g.add_node("normalize", normalize)
    g.add_node("rank", rank)
    g.add_node("select", select)
    g.add_node("summarize", summarize)

    g.add_edge(START, "collect_input")
    g.add_conditional_edges("collect_input", _abort_or("validate_input"))
    g.add_conditional_edges("validate_input", _abort_or("fetch"))
    g.add_conditional_edges("fetch", _abort_or("normalize"))
    g.add_conditional_edges("normalize", _abort_or("rank"))
    g.add_conditional_edges("rank", _abort_or("select"))
    g.add_conditional_edges("select", _abort_or("summarize"))
    g.add_edge("summarize", END)

    return g.compile()


# Grafo compilado listo para invoke / serve
graph = build_graph()
