from graph.v2.graph import build_graph

def test_fetchphase_deterministic_5_runs():
    graph = build_graph()

    inp = {"query": "test", "time_window": "last_7_days", "top_k": 2}

    runs = []
    for _ in range(5):
        out = graph.invoke(inp)
        runs.append(out["merged_source_units"])

    first = runs[0]
    for i, r in enumerate(runs[1:], start=1):
        assert r == first, f"Run {i} differs"


def test_merge_order_contractual():
    graph = build_graph()
    out = graph.invoke({"query":"test","time_window":"last_7_days","top_k":2})

    msu = out["merged_source_units"]
    assert [(x["source"], x["source_seq"]) for x in msu] == [
        ("arxiv", 0),
        ("arxiv", 1),
        ("huggingface", 0),
        ("huggingface", 1),
    ]