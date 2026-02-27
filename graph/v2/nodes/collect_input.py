from typing import Dict
from graph.v2.state import V2State


def collect_input(state: V2State) -> Dict:
    input_raw = {
        "query": state.get("query"),
        "time_window": state.get("time_window"),
        "top_k": state.get("top_k"),
    }

    if all(state.get(k) is None for k in ("query", "time_window", "top_k")):
        return {
            "input_raw": input_raw,
            "abort_reason": "EMPTY_INPUT_PAYLOAD",
        }

    return {"input_raw": input_raw}
