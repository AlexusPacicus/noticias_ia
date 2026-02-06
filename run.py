from graph.graph import build_graph

def run(input_dict: dict):
    graph = build_graph()
    return graph.invoke(input_dict)

if __name__ == "__main__":
    out = run({
        "query": "llm safety",
        "time_window": "last_7_days",
        "top_k": 5,
    })
    print(out)
