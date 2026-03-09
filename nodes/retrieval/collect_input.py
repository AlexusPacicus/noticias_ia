from typing import Any, Dict

# Nodo collect_input - Responsabilidad: capturar input bruto y gatear payload vacío.

def collect_input(state: Dict[str, Any]) -> Dict[str, Any]:
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
