from typing import Dict
from graph.v2.state import V2State


def collect_input(state: V2State) -> Dict:
    return {
        "input_raw": {
            "query": state.get("query"),
            "time_window": state.get("time_window"),
            "top_k": state.get("top_k"),
        }
    }
