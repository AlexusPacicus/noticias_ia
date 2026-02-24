import argparse
from graph.v2.graph import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Ejecuta el grafo v2 en modo live",
    )
    args = parser.parse_args()

    input_payload = {
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 2,
    }

    graph = build_graph(live=args.live)
    result = graph.invoke(input_payload)

    if args.debug:
        print(result)
        return

    if "abort_reason" in result:
        print({"abort_reason": result["abort_reason"]})
    else:
        print(result["output"])


if __name__ == "__main__":
    main()