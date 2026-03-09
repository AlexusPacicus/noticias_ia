from typing import Any, Dict

# Nodo validate_input - Responsabilidad: validar query/time_window/top_k y aplicar defaults.

VALID_TIME_WINDOWS = {"last_24h", "last_3_days", "last_7_days"}


def validate_input(state: Dict[str, Any]) -> Dict[str, Any]:
    raw = state.get("input_raw", {})

    query = raw.get("query")
    time_window = raw.get("time_window")
    top_k_raw = raw.get("top_k")

    if not isinstance(query, str) or not query.strip():
        return {"abort_reason": "INVALID_QUERY"}

    if not isinstance(time_window, str) or time_window not in VALID_TIME_WINDOWS:
        return {"abort_reason": "INVALID_TIME_WINDOW"}

    if top_k_raw is None:
        top_k = 3
    else:
        if isinstance(top_k_raw, bool) or not isinstance(top_k_raw, int):
            return {"abort_reason": "INVALID_TOP_K"}
        if not (1 <= top_k_raw <= 5):
            return {"abort_reason": "INVALID_TOP_K"}
        top_k = top_k_raw

    return {
        "input_validated": {
            "query": query.strip(),
            "time_window": time_window,
            "top_k": top_k,
        }
    }
