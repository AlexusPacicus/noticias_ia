from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, StateGraph

from graph.v2.nodes.summarize_map import summarize_map
from graph.v2.nodes.summarize_reduce import summarize_reduce
from graph.v2_1.state import V21State


def _effective_selected_items(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    if "hitl_selected_items" in state:
        return state["hitl_selected_items"] or []
    return state.get("selected_items", []) or []


def summarize_precheck(state: Dict[str, Any]) -> Dict[str, Any]:
    effective_items = _effective_selected_items(state)
    if len(effective_items) == 0:
        return {"abort_reason": "SUMMARY_EMPTY_INPUT"}
    return {}


def summarize_map_effective(state: Dict[str, Any]) -> Dict[str, Any]:
    return summarize_map({"selected_items": _effective_selected_items(state)})


def build_summarize_graph():
    builder = StateGraph(V21State)

    def abort_or(next_node):
        def _router(state):
            if state.get("abort_reason"):
                return END
            return next_node

        return _router

    builder.add_node("summarize_precheck", summarize_precheck)
    builder.add_node("summarize_map", summarize_map_effective)
    builder.add_node("summarize_reduce", summarize_reduce)

    builder.set_entry_point("summarize_precheck")
    builder.add_conditional_edges("summarize_precheck", abort_or("summarize_map"))
    builder.add_edge("summarize_map", "summarize_reduce")
    builder.add_conditional_edges("summarize_reduce", abort_or(END))
    return builder.compile()
