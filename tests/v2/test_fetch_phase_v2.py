import pytest
from langgraph.graph import StateGraph, END

from graph.v2.state import V2State
from graph.v2.nodes.merge_source_units import merge_source_units


# --- Helpers -----------------------------------------------------

def build_test_graph(fetch_arxiv_node, fetch_hf_node):
    builder = StateGraph(V2State)

    builder.add_node("fetch_arxiv", fetch_arxiv_node)
    builder.add_node("fetch_huggingface", fetch_hf_node)
    builder.add_node("merge_source_units", merge_source_units)

    # Fan-out directo (sin collect/validate para aislar fase)
    builder.set_entry_point("fetch_arxiv")
    builder.add_edge("fetch_arxiv", "fetch_huggingface")
    builder.add_edge("fetch_huggingface", "merge_source_units")
    builder.add_edge("merge_source_units", END)

    return builder.compile()


def ok_arxiv(state):
    return {
        "source_units": {
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": [
                    {"source": "arxiv", "source_seq": 0},
                ],
            }
        }
    }


def ok_hf(state):
    return {
        "source_units": {
            "huggingface": {
                "status": "ok",
                "error": None,
                "items": [
                    {"source": "huggingface", "source_seq": 0},
                ],
            }
        }
    }


def failed_arxiv(state):
    return {
        "source_units": {
            "arxiv": {
                "status": "failed",
                "error": "timeout",
                "items": [],
            }
        }
    }


def failed_hf(state):
    return {
        "source_units": {
            "huggingface": {
                "status": "failed",
                "error": "timeout",
                "items": [],
            }
        }
    }


def empty_ok_arxiv(state):
    return {
        "source_units": {
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": [],
            }
        }
    }


# --- Tests -------------------------------------------------------

def test_both_ok():
    graph = build_test_graph(ok_arxiv, ok_hf)
    result = graph.invoke({})

    assert "abort_reason" not in result
    assert len(result["merged_source_units"]) == 2


def test_one_failed_one_ok():
    graph = build_test_graph(failed_arxiv, ok_hf)
    result = graph.invoke({})

    assert "abort_reason" not in result
    assert len(result["merged_source_units"]) == 1


def test_both_failed_abort():
    graph = build_test_graph(failed_arxiv, failed_hf)
    result = graph.invoke({})

    assert result["abort_reason"] == "FETCH_ALL_SOURCES_FAILED"


def test_empty_ok_no_abort():
    graph = build_test_graph(empty_ok_arxiv, ok_hf)
    result = graph.invoke({})

    assert "abort_reason" not in result
    assert len(result["merged_source_units"]) == 1