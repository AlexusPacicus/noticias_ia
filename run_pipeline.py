"""
Runtime v1.1 — ejecuta el pipeline via graph.invoke().

El grafo LangGraph compilado gestiona el orden de nodos,
el abort handling via conditional edges y el merge de state.
"""

import json

from graph.graph import graph

if __name__ == "__main__":
    result = graph.invoke({
        "query": "large language models",
        "time_window": "last_7_days",
        "top_k": 3,
    })

    if result.get("abort_reason"):
        print(f"ABORT: {result['abort_reason']}")
    else:
        print(json.dumps(result["output"], indent=2, ensure_ascii=False))
