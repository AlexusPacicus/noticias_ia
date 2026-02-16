from __future__ import annotations

from graph.state import PipelineState


def select(state: PipelineState) -> dict:
    """Selecciona los primeros top_k elementos de ranked_items.

    Retorna selected_items o abort_reason.
    """
    ranked_items = state.get("ranked_items")
    if not isinstance(ranked_items, list):
        return {"abort_reason": "SELECT_MISSING_RANKED_ITEMS"}

    top_k = state["input_validated"]["top_k"]
    if not isinstance(top_k, int) or top_k <= 0:
        return {"abort_reason": "SELECT_TOPK_INVALID"}

    return {"selected_items": ranked_items[:top_k]}
