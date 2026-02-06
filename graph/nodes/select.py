def select(state: dict) -> dict:
    top_k = state["input"]["top_k"]
    selected = state["ranked_items"][:top_k]

    if not selected:
        raise ValueError("EMPTY_RESULTS")

    state["selected_items"] = selected
    return state
