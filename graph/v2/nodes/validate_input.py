from typing import Dict
from graph.v2.state import V2State


def validate_input(state: V2State) -> Dict:
    raw = state.get("input_raw", {})

    query = raw.get("query")
    time_window = raw.get("time_window")
    top_k = raw.get("top_k") or 3

    if not query or not isinstance(query, str):
        return {"abort_reason": "INVALID_QUERY"}

    return {
        "input_validated": {
            "query": query,
            "time_window": time_window,
            "top_k": top_k,
        }
    }
