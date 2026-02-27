import pytest
from graph.v2.graph import build_graph

@pytest.mark.live
def test_live_smoke_contract():
    graph = build_graph(live=True)

    result = graph.invoke({
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 2,
    })

    assert isinstance(result, dict)

    if "abort_reason" in result:
        assert isinstance(result["abort_reason"], str)
    else:
        assert "output" in result
        assert isinstance(result["output"], dict)
