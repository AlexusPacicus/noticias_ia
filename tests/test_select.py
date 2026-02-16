"""
Tests contractuales: select.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md
"""

from graph.nodes.select import select


def _state(top_k, n):
    items = [
        {"title": f"Paper {i}", "link": f"http://a.com/{i}", "content": f"Content {i}."}
        for i in range(n)
    ]
    return {
        "input_validated": {"query": "ml", "time_window": "last_7_days", "top_k": top_k},
        "ranked_items": items,
    }


class TestSelect:

    def test_top_k_less_than_n(self):
        result = select(_state(3, 10))
        assert len(result["selected_items"]) == 3

    def test_empty_produces_empty(self):
        result = select(_state(5, 0))
        assert result["selected_items"] == []

    def test_missing_ranked_items_aborts(self):
        state = {"input_validated": {"query": "ml", "time_window": "last_7_days", "top_k": 3}}
        result = select(state)
        assert result["abort_reason"] == "SELECT_MISSING_RANKED_ITEMS"

    def test_ranked_items_not_list_aborts(self):
        state = {
            "input_validated": {"query": "ml", "time_window": "last_7_days", "top_k": 3},
            "ranked_items": "not a list",
        }
        result = select(state)
        assert result["abort_reason"] == "SELECT_MISSING_RANKED_ITEMS"

    def test_topk_invalid_aborts(self):
        state = {
            "input_validated": {"query": "ml", "time_window": "last_7_days", "top_k": 0},
            "ranked_items": [],
        }
        result = select(state)
        assert result["abort_reason"] == "SELECT_TOPK_INVALID"
