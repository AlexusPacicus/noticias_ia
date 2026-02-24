import copy
import pytest

from graph.v2.nodes.rank_bm25 import rank_bm25


def _base_state():
    return {
        "input_validated": {
            "query": "reinforcement learning",
            "time_window": "last_7_days",
            "top_k": 3,
        },
        "deduped_items": [
            {
                "title": "Deep Reinforcement Learning",
                "content": "This paper explores reinforcement learning methods.",
                "published_at": "2025-01-01T00:00:00Z",
                "link": "https://a.com/1",
                "source": "arxiv",
                "canonical_id": "arxiv:1",
            },
            {
                "title": "Supervised Learning Overview",
                "content": "A broad overview of supervised methods.",
                "published_at": "2025-01-01T00:00:00Z",
                "link": "https://a.com/2",
                "source": "arxiv",
                "canonical_id": "arxiv:2",
            },
            {
                "title": "Advanced Reinforcement Techniques",
                "content": "Reinforcement learning in robotics.",
                "published_at": "2025-01-01T00:00:00Z",
                "link": "https://a.com/3",
                "source": "arxiv",
                "canonical_id": "arxiv:3",
            },
        ],
    }

def test_rank_happy_path_creates_ranked_items():
    state = _base_state()

    delta = rank_bm25(state)

    assert "ranked_items" in delta
    ranked = delta["ranked_items"]

    assert len(ranked) == len(state["deduped_items"])

    for i, item in enumerate(ranked, start=1):
        assert "bm25_score" in item
        assert "rank_position" in item
        assert item["rank_position"] == i

def test_rank_is_deterministic():
    state1 = _base_state()
    state2 = _base_state()

    delta1 = rank_bm25(state1)
    delta2 = rank_bm25(state2)

    assert delta1["ranked_items"] == delta2["ranked_items"]

def test_rank_tie_break_by_title_and_link():
    state = {
        "input_validated": {
            "query": "robotics",
            "time_window": "last_7_days",
            "top_k": 3,
        },
        "deduped_items": [
            {
                "title": "B Paper",
                "content": "robotics",
                "published_at": "2025-01-01T00:00:00Z",
                "link": "https://a.com/b",
                "source": "arxiv",
                "canonical_id": "id1",
            },
            {
                "title": "A Paper",
                "content": "robotics",
                "published_at": "2025-01-01T00:00:00Z",
                "link": "https://a.com/a",
                "source": "arxiv",
                "canonical_id": "id2",
            },
        ],
    }

    delta = rank_bm25(state)
    ranked = delta["ranked_items"]

    assert ranked[0]["title"] == "A Paper"
    assert ranked[1]["title"] == "B Paper"

def test_rank_abort_if_query_empty_after_preprocessing():
    state = _base_state()
    state["input_validated"]["query"] = "the and of"

    delta = rank_bm25(state)

    assert delta == {
        "abort_reason": "RANK_QUERY_EMPTY_AFTER_NORMALIZATION"
    }

def test_rank_does_not_mutate_input():
    state = _base_state()
    original = copy.deepcopy(state["deduped_items"])

    _ = rank_bm25(state)

    assert state["deduped_items"] == original

