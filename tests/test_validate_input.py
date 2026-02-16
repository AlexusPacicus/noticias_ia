"""
Tests contractuales: validate_input + collect_input.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md
"""

from graph.nodes.collect_input import collect_input
from graph.nodes.validate_input import validate_input


def _raw(query="machine learning", tw="last_7_days", top_k=5):
    return {"input_raw": {"query": query, "time_window": tw, "top_k": top_k}}


class TestValidateInput:

    def test_happy_path(self):
        result = validate_input(_raw())
        v = result["input_validated"]
        assert v == {"query": "machine learning", "time_window": "last_7_days", "top_k": 5}

    def test_default_top_k(self):
        state = {"input_raw": {"query": "machine learning", "time_window": "last_7_days"}}
        assert validate_input(state)["input_validated"]["top_k"] == 5

    def test_invalid_query(self):
        result = validate_input(_raw(query="AI"))
        assert result["abort_reason"] == "INVALID_QUERY"

    def test_invalid_time_window(self):
        result = validate_input(_raw(tw="last_30_days"))
        assert result["abort_reason"] == "INVALID_TIME_WINDOW"

    def test_invalid_top_k(self):
        result = validate_input(_raw(top_k=0))
        assert result["abort_reason"] == "INVALID_TOP_K"

    def test_collect_input_empty(self):
        result = collect_input({})
        assert result["abort_reason"] == "EMPTY_INPUT_PAYLOAD"

    def test_collect_input_happy(self):
        state = {"query": "machine learning", "time_window": "last_7_days", "top_k": 3}
        result = collect_input(state)
        assert result["input_raw"] == state
