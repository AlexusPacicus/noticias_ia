"""
Tests contractuales: validate_input + collect_input.
Ref: Contrato_Validate_Input.md, Contrato_Collect_Input.md
"""

import pytest

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
        with pytest.raises(ValueError, match="INVALID_QUERY"):
            validate_input(_raw(query="AI"))

    def test_invalid_time_window(self):
        with pytest.raises(ValueError, match="INVALID_TIME_WINDOW"):
            validate_input(_raw(tw="last_30_days"))

    def test_invalid_top_k(self):
        with pytest.raises(ValueError, match="INVALID_TOP_K"):
            validate_input(_raw(top_k=0))

    def test_collect_input_none(self):
        with pytest.raises(ValueError, match="EMPTY_INPUT_PAYLOAD"):
            collect_input(None)
