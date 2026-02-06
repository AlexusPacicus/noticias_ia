_VALID_TIME_WINDOWS = {"last_24h", "last_3_days", "last_7_days", "last_30_days"}


def validate_input(state: dict) -> dict:
    raw = state["raw_input"]

    query = raw.get("query")
    if not isinstance(query, str) or len(query.strip().split()) < 2:
        raise ValueError("INVALID_QUERY")

    time_window = raw.get("time_window")
    if time_window not in _VALID_TIME_WINDOWS:
        raise ValueError("INVALID_TIME_WINDOW")

    top_k = raw.get("top_k")
    if top_k is None:
        top_k = 5
    if not isinstance(top_k, int) or top_k < 1 or top_k > 10:
        raise ValueError("INVALID_TOP_K")

    state["input"] = {
        "query": query.strip(),
        "time_window": time_window,
        "top_k": top_k,
    }
    return state
