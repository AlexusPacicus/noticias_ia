from __future__ import annotations

from typing import Any, Callable

from langgraph.graph import END, StateGraph

from graph.v2_1.state import V21State
from nodes.hitl.hitl_review import hitl_review


def build_hitl_graph(
    decision_provider: Callable[[dict[str, Any]], dict[str, Any]],
):
    builder = StateGraph(V21State)

    def _hitl_review_node(state: dict[str, Any]) -> dict[str, Any]:
        decision = decision_provider(state)
        return hitl_review(state, decision)

    builder.add_node("hitl_review", _hitl_review_node)
    builder.set_entry_point("hitl_review")
    builder.add_edge("hitl_review", END)
    return builder.compile()
