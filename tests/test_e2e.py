"""
Tests end-to-end.
Ref: Contrato_Sistema_v1.md

Requieren conexión a arXiv y Ollama con modelo disponible.
Runtime contractual: pipeline manual con abort por ValueError.
"""

import pytest

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


def _run(query, time_window="last_7_days", top_k=5):
    state = {"query": query, "time_window": time_window, "top_k": top_k}
    for node in _PIPELINE:
        try:
            state = node(state)
        except ValueError as e:
            state = {"abort_reason": str(e)}
            break
    return state


@pytest.mark.e2e
class TestE2E:

    def test_happy_path_schema(self):
        result = _run("artificial intelligence", top_k=3)
        assert "abort_reason" not in result
        output = result["output"]
        assert set(output.keys()) == {"topic", "time_window", "results"}
        assert output["topic"] == "artificial intelligence"
        assert output["time_window"] == "last_7_days"
        assert len(output["results"]) <= 3
        for r in output["results"]:
            assert set(r.keys()) == {"title", "idea_clave", "relacion_con_query", "link"}
            assert len(r["idea_clave"].split()) <= 80
            assert len(r["relacion_con_query"].split()) <= 30

    def test_determinism(self):
        result_a = _run("neural networks", top_k=3)
        result_b = _run("neural networks", top_k=3)
        assert "abort_reason" not in result_a
        assert "abort_reason" not in result_b
        titles_a = [r["title"] for r in result_a["output"]["results"]]
        titles_b = [r["title"] for r in result_b["output"]["results"]]
        assert titles_a == titles_b

    def test_abort_writes_reason(self):
        result = _run("x", top_k=3)
        assert "abort_reason" in result
        assert result["abort_reason"] == "INVALID_QUERY"
        assert "output" not in result
