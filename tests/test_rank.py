"""
Tests contractuales: rank.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md
"""

from graph.nodes.rank import rank


def _item(title, link, content=""):
    return {"title": title, "link": link, "content": content}


def _state(query, items):
    return {
        "input_validated": {"query": query, "time_window": "last_7_days", "top_k": 5},
        "normalized_items": items,
    }


class TestRank:

    def test_higher_match_ranks_first(self):
        items = [
            _item("Deep Robotics", "http://a.com/1", "About robots."),
            _item("Machine Learning Advances", "http://a.com/2", "New approach to learning."),
        ]
        result = rank(_state("machine learning", items))
        assert result["ranked_items"][0]["title"] == "Machine Learning Advances"

    def test_tie_broken_by_title_asc(self):
        items = [
            _item("Zebra Neural Nets", "http://a.com/1", "About neural networks."),
            _item("Alpha Neural Nets", "http://a.com/2", "About neural networks."),
        ]
        result = rank(_state("neural", items))
        assert result["ranked_items"][0]["title"] == "Alpha Neural Nets"

    def test_case_insensitive(self):
        items = [
            _item("machine learning paper", "http://a.com/1", "About ML."),
            _item("Unrelated", "http://a.com/2", "Nothing."),
        ]
        result = rank(_state("MACHINE LEARNING", items))
        assert result["ranked_items"][0]["title"] == "machine learning paper"

    def test_empty_produces_empty(self):
        result = rank(_state("machine learning", []))
        assert result["ranked_items"] == []

    def test_query_empty_after_normalization_aborts(self):
        items = [_item("Paper", "http://a.com/1", "Content.")]
        result = rank(_state("!! ##", items))
        assert result["abort_reason"] == "RANK_QUERY_EMPTY_AFTER_NORMALIZATION"
