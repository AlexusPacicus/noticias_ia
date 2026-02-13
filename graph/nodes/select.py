def select(state: dict) -> dict:
    ranked_items = state.get("ranked_items")
    if not isinstance(ranked_items, list):
        raise ValueError("SELECT_MISSING_RANKED_ITEMS")

    top_k = state["input_validated"]["top_k"]
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("SELECT_TOPK_INVALID")

    state["selected_items"] = ranked_items[:top_k]
    return state
