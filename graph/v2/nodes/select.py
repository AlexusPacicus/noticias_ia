from __future__ import annotations

from typing import Any, Dict

from graph.v2.state import V2State


def select(state: V2State) -> Dict[str, Any]:
    ranked_items = state.get("ranked_items")
    if not isinstance(ranked_items, list):
        return {"abort_reason": "SELECT_MISSING_RANKED_ITEMS"}

    input_validated = state.get("input_validated") or {}
    top_k = input_validated.get("top_k")

    if not isinstance(top_k, int) or not (1 <= top_k <= 5):
        return {"abort_reason": "SELECT_TOPK_INVALID"}

    effective_k = min(top_k, len(ranked_items))
    selected_items = ranked_items[:effective_k]
    return {"selected_items": selected_items}