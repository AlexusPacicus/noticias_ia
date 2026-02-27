import argparse
import json
from graph.v2.graph import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--live",
        action="store_true",
        help="Ejecuta el grafo v2 en modo live (default).",
    )
    mode_group.add_argument(
        "--stub",
        action="store_true",
        help="Ejecuta con snapshot determinista de fetch (fechas fijas).",
    )
    parser.add_argument("--query", default="llm")
    parser.add_argument(
        "--time-window",
        default="last_3_days",
        choices=["last_24h", "last_3_days", "last_7_days"],
    )
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument(
        "--source",
        default="both",
        choices=["both", "arxiv", "huggingface"],
        help="Filtra fuentes de fetch: both (default), arxiv o huggingface.",
    )
    args = parser.parse_args()

    input_payload = {
        "query": args.query,
        "time_window": args.time_window,
        "top_k": args.top_k,
    }

    live_mode = not args.stub
    sources = ("arxiv", "huggingface") if args.source == "both" else (args.source,)
    graph = build_graph(live=live_mode, sources=sources)
    result = graph.invoke(input_payload)

    if args.debug:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if "abort_reason" in result:
        print({"abort_reason": result["abort_reason"]})
    else:
        print(result["output"])


if __name__ == "__main__":
    main()
