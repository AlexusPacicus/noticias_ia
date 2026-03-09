import argparse
import json

from graph.v2_1 import run_system


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--live",
        action="store_true",
        help="Ejecuta el grafo v2.1 en modo live.",
    )
    mode_group.add_argument(
        "--stub",
        action="store_true",
        help="Ejecuta v2.1 con fetch determinista local si las fuentes lo soportan.",
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
    parser.add_argument(
        "--execute-until",
        default="summary",
        choices=["select", "summary"],
        help="Permite ejecutar solo retrieval hasta select o el flujo completo.",
    )
    args = parser.parse_args()

    payload = {
        "query": args.query,
        "time_window": args.time_window,
        "top_k": args.top_k,
    }
    live_mode = args.live
    sources = ("arxiv", "huggingface") if args.source == "both" else (args.source,)

    result = run_system(
        payload,
        execute_until=args.execute_until,
        live=live_mode,
        sources=sources,
    )

    if args.debug:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if "abort_reason" in result:
        print({"abort_reason": result["abort_reason"]})
        return

    if args.execute_until == "select":
        print(result["selected_items"])
        return

    print(result["output"])


if __name__ == "__main__":
    main()
