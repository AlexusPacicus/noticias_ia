from __future__ import annotations

from langgraph.graph import END, StateGraph

from graph.v2.nodes.summarize_reduce import summarize_reduce
from graph.v2_1.state import V21State
from graph.v2_1.summarize.summarize_map import summarize_map


def _abort_or(next_node: str):
    def _router(state):
        if state.get("abort_reason"):
            return END
        return next_node

    return _router


def build_summarize_graph():
    builder = StateGraph(V21State)
    builder.add_node("summarize_map", summarize_map)
    builder.add_node("summarize_reduce", summarize_reduce)
    builder.set_entry_point("summarize_map")
    builder.add_conditional_edges("summarize_map", _abort_or("summarize_reduce"))
    builder.add_conditional_edges("summarize_reduce", _abort_or(END))
    return builder.compile()
