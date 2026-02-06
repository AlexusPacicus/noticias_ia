from graph.nodes.collect_input import collect_input
from graph.nodes.validate_input import validate_input
from graph.nodes.fetch import fetch
from graph.nodes.normalize import normalize
from graph.nodes.rank import rank
from graph.nodes.select import select
from graph.nodes.summarize import summarize

_VALID_KINDS = {"paper", "news", "release"}


def _run_pipeline():
    state = {
        "query": "llm safety",
        "time_window": "last_7_days",
        "top_k": 5,
    }
    state = collect_input(state)
    state = validate_input(state)
    state = fetch(state)
    state = normalize(state)
    state = rank(state)
    state = select(state)
    state = summarize(state)
    return state["results"]


def test_order_is_identical():
    results_a = _run_pipeline()
    results_b = _run_pipeline()

    titles_a = [r["title"] for r in results_a]
    titles_b = [r["title"] for r in results_b]
    assert titles_a == titles_b


def test_links_are_identical():
    results_a = _run_pipeline()
    results_b = _run_pipeline()

    links_a = [r["link"] for r in results_a]
    links_b = [r["link"] for r in results_b]
    assert links_a == links_b


def test_results_within_top_k():
    results = _run_pipeline()
    assert len(results) <= 5


def test_result_schema():
    results = _run_pipeline()
    for r in results:
        assert r["kind"] in _VALID_KINDS
        assert isinstance(r["title"], str) and r["title"]
        assert isinstance(r["idea_clave"], str) and r["idea_clave"]
        assert isinstance(r["por_que_importa"], str) and r["por_que_importa"]
        assert isinstance(r["link"], str) and r["link"]
