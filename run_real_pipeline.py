import json

from graph.nodes.collect_input import collect_input
from graph.nodes.validate_input import validate_input
from graph.nodes.fetch import fetch
from graph.nodes.normalize import normalize
from graph.nodes.rank import rank
from graph.nodes.select import select
from graph.nodes.summarize import summarize

_PIPELINE = [
    collect_input,
    validate_input,
    fetch,
    normalize,
    rank,
    select,
    summarize,
]

if __name__ == "__main__":
    state = {
        "query": "large language models",
        "time_window": "last_7_days",
        "top_k": 3,
    }

    for node in _PIPELINE:
        try:
            state = node(state)
        except ValueError as e:
            state = {"abort_reason": str(e)}
            break

    if "abort_reason" in state:
        print(f"ABORT: {state['abort_reason']}")
    else:
        print(json.dumps(state["output"], indent=2, ensure_ascii=False))
