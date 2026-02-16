from __future__ import annotations

from graph.state import PipelineState


def collect_input(state: PipelineState) -> dict:
    """Captura el input bruto del usuario como input_raw.

    Retorna abort_reason si no hay payload.
    """
    raw = {}
    for k in ("query", "time_window", "top_k"):
        if k in state:
            raw[k] = state[k]

    if not raw:
        return {"abort_reason": "EMPTY_INPUT_PAYLOAD"}

    return {"input_raw": raw}
