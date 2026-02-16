"""
Tests end-to-end.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md

Requieren conexion a arXiv y Ollama con modelo disponible.
Runtime v1.1: graph.invoke() con LangGraph.
"""

import pytest

from graph.graph import graph


@pytest.mark.e2e
class TestE2E:

    def test_happy_path_schema(self):
        result = graph.invoke({
            "query": "artificial intelligence",
            "time_window": "last_7_days",
            "top_k": 3,
        })
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
        inp = {
            "query": "neural networks",
            "time_window": "last_7_days",
            "top_k": 3,
        }
        result_a = graph.invoke(inp)
        result_b = graph.invoke(inp)
        assert "abort_reason" not in result_a
        assert "abort_reason" not in result_b
        titles_a = [r["title"] for r in result_a["output"]["results"]]
        titles_b = [r["title"] for r in result_b["output"]["results"]]
        assert titles_a == titles_b

    def test_abort_writes_reason(self):
        result = graph.invoke({
            "query": "x",
            "time_window": "last_7_days",
            "top_k": 3,
        })
        assert result.get("abort_reason") == "INVALID_QUERY"
        assert "output" not in result
