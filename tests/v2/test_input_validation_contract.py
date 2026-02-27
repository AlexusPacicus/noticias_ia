from graph.v2.graph import build_graph
from graph.v2.nodes.collect_input import collect_input
from graph.v2.nodes.validate_input import validate_input


def test_collect_input_abort_empty_payload():
    delta = collect_input({})
    assert delta == {
        "input_raw": {"query": None, "time_window": None, "top_k": None},
        "abort_reason": "EMPTY_INPUT_PAYLOAD",
    }


def test_collect_input_passthrough_shape():
    state = {"query": "agentic ai", "time_window": "last_7_days", "top_k": 2}
    delta = collect_input(state)
    assert delta == {
        "input_raw": {
            "query": "agentic ai",
            "time_window": "last_7_days",
            "top_k": 2,
        }
    }


def test_validate_input_happy_path():
    delta = validate_input(
        {"input_raw": {"query": "  agentic ai  ", "time_window": "last_7_days", "top_k": 2}}
    )
    assert delta == {
        "input_validated": {
            "query": "agentic ai",
            "time_window": "last_7_days",
            "top_k": 2,
        }
    }


def test_validate_input_default_top_k():
    delta = validate_input({"input_raw": {"query": "q", "time_window": "last_3_days"}})
    assert delta["input_validated"]["top_k"] == 3


def test_validate_input_invalid_time_window():
    delta = validate_input({"input_raw": {"query": "q", "time_window": "yesterday", "top_k": 2}})
    assert delta == {"abort_reason": "INVALID_TIME_WINDOW"}


def test_validate_input_invalid_top_k():
    for bad in [0, 6, "3", 2.5, True]:
        delta = validate_input({"input_raw": {"query": "q", "time_window": "last_7_days", "top_k": bad}})
        assert delta == {"abort_reason": "INVALID_TOP_K"}


def test_validate_input_invalid_query():
    for bad in ["", "   ", None]:
        delta = validate_input({"input_raw": {"query": bad, "time_window": "last_7_days", "top_k": 2}})
        assert delta == {"abort_reason": "INVALID_QUERY"}


def test_graph_aborts_early_for_invalid_time_window():
    graph = build_graph()
    out = graph.invoke({"query": "agentic ai", "time_window": "bad_window", "top_k": 2})
    assert out.get("abort_reason") == "INVALID_TIME_WINDOW"
    assert "source_units" not in out
    assert "merged_source_units" not in out


def test_graph_aborts_early_for_invalid_top_k():
    graph = build_graph()
    out = graph.invoke({"query": "agentic ai", "time_window": "last_7_days", "top_k": 99})
    assert out.get("abort_reason") == "INVALID_TOP_K"
    assert "source_units" not in out
    assert "merged_source_units" not in out


def test_graph_aborts_for_empty_input_payload():
    graph = build_graph()
    out = graph.invoke({})
    assert out.get("abort_reason") == "EMPTY_INPUT_PAYLOAD"
    assert "input_validated" not in out
    assert "source_units" not in out
