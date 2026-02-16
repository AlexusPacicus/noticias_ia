"""
Tests contractuales: summarize.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md
"""

import json

from unittest.mock import patch, MagicMock

from graph.nodes.summarize import summarize


def _mock_response(idea_clave, relacion_con_query):
    msg = MagicMock()
    msg.content = json.dumps({
        "idea_clave": idea_clave,
        "relacion_con_query": relacion_con_query,
    })
    return msg


def _item(title="Paper", link="http://a.com/1", content="Content."):
    return {"title": title, "link": link, "content": content}


def _state(items, query="machine learning"):
    return {
        "input_validated": {"query": query, "time_window": "last_7_days", "top_k": 5},
        "selected_items": items,
    }


class TestSummarize:

    def test_empty_no_llm_call(self):
        with patch("graph.nodes.summarize._chain") as mock_chain:
            result = summarize(_state([], query="deep learning"))
            mock_chain.invoke.assert_not_called()
        output = result["output"]
        assert output == {"topic": "deep learning", "time_window": "last_7_days", "results": []}

    def test_happy_path_schema(self):
        resp = _mock_response("Summary of paper.", "Related to ML.")
        with patch("graph.nodes.summarize._chain") as mc:
            mc.invoke.return_value = resp
            result = summarize(_state([_item(title="Exact Title", link="http://exact/1")]))
        r = result["output"]["results"][0]
        assert set(r.keys()) == {"title", "idea_clave", "relacion_con_query", "link"}
        assert r["title"] == "Exact Title"
        assert r["link"] == "http://exact/1"

    def test_long_idea_clave_aborts(self):
        long = " ".join(["word"] * 100)
        resp = _mock_response(long, "Related.")
        with patch("graph.nodes.summarize._chain") as mc:
            mc.invoke.return_value = resp
            result = summarize(_state([_item()]))
        assert result["abort_reason"] == "SUMMARY_SCHEMA_VIOLATION"

    def test_llm_runtime_error(self):
        with patch("graph.nodes.summarize._chain") as mc:
            mc.invoke.side_effect = Exception("timeout")
            result = summarize(_state([_item()]))
        assert result["abort_reason"] == "SUMMARY_LLM_RUNTIME_ERROR"

    def test_invalid_json_aborts(self):
        resp = MagicMock()
        resp.content = "not json"
        with patch("graph.nodes.summarize._chain") as mc:
            mc.invoke.return_value = resp
            result = summarize(_state([_item()]))
        assert result["abort_reason"] == "SUMMARY_SCHEMA_VIOLATION"

    def test_missing_field_aborts(self):
        resp = MagicMock()
        resp.content = json.dumps({"idea_clave": "Summary."})
        with patch("graph.nodes.summarize._chain") as mc:
            mc.invoke.return_value = resp
            result = summarize(_state([_item()]))
        assert result["abort_reason"] == "SUMMARY_SCHEMA_VIOLATION"
