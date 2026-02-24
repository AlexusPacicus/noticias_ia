import pytest

from graph.v2.nodes.summarize_reduce import summarize_reduce


def base_input():
    return {
        "input_validated": {
            "query": "agentic ai",
            "time_window": "last_7_days",
            "top_k": 3,
        }
    }


# -------------------------------------------------
# TEST 1 — Happy Path
# -------------------------------------------------

def test_summarize_reduce_happy_path():

    state = {
        **base_input(),
        "summary_items": [
            {
                "rank_position": 1,
                "title": "A",
                "idea_clave": "x",
                "relacion_con_query": "y",
                "link": "l1",
                "source": "arxiv",
            },
            {
                "rank_position": 2,
                "title": "B",
                "idea_clave": "x",
                "relacion_con_query": "y",
                "link": "l2",
                "source": "hf",
            },
        ],
        "summary_stats": {"ok": 2, "failed": 1},
    }

    delta = summarize_reduce(state)

    assert "abort_reason" not in delta
    assert "output" in delta

    output = delta["output"]

    assert output["topic"] == "agentic ai"
    assert output["time_window"] == "last_7_days"
    assert output["requested_k"] == 3
    assert output["returned_k"] == 2
    assert output["failed_summaries"] == 1
    assert len(output["results"]) == 2


# -------------------------------------------------
# TEST 2 — Reordenación obligatoria
# -------------------------------------------------

def test_summarize_reduce_reorders_by_rank_position():

    state = {
        **base_input(),
        "summary_items": [
            {
                "rank_position": 3,
                "title": "C",
                "idea_clave": "x",
                "relacion_con_query": "y",
                "link": "l3",
                "source": "arxiv",
            },
            {
                "rank_position": 1,
                "title": "A",
                "idea_clave": "x",
                "relacion_con_query": "y",
                "link": "l1",
                "source": "arxiv",
            },
        ],
        "summary_stats": {"ok": 2, "failed": 0},
    }

    delta = summarize_reduce(state)
    results = delta["output"]["results"]

    assert results[0]["rank_position"] == 1
    assert results[1]["rank_position"] == 3


# -------------------------------------------------
# TEST 3 — Abort gate
# -------------------------------------------------

def test_summarize_reduce_abort_when_no_valid_summaries():

    state = {
        **base_input(),
        "summary_items": [],
        "summary_stats": {"ok": 0, "failed": 3},
    }

    delta = summarize_reduce(state)

    assert delta["abort_reason"] == "SUMMARY_ALL_ITEMS_FAILED"
    assert "output" not in delta


# -------------------------------------------------
# TEST 4 — Invariante roto (violación estructural)
# -------------------------------------------------

def test_summarize_reduce_invariant_violation():

    state = {
        **base_input(),
        "summary_items": [
            {
                "rank_position": 1,
                "title": "A",
                "idea_clave": "x",
                "relacion_con_query": "y",
                "link": "l1",
                "source": "arxiv",
            }
        ],
        "summary_stats": {"ok": 2, "failed": 0},  # inconsistente
    }

    with pytest.raises(AssertionError):
        summarize_reduce(state)