def normalize(state: dict) -> dict:
    state["normalized_items"] = list(state["items"])
    return state
