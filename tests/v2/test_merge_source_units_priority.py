import pytest
from graph.v2.nodes.merge_source_units import merge_source_units


def _ok_unit(source, seq=0):
    return {
        "status": "ok",
        "error": None,
        "items": [
            {
                "source": source,
                "source_seq": seq,
                "payload": {}
            }
        ]
    }


def test_abort_on_unknown_source_priority():
    state = {
        "source_units": {
            "arxiv": _ok_unit("arxiv"),
            "huggingface": _ok_unit("huggingface"),
            "rogue": _ok_unit("rogue"),
        }
    }

    result = merge_source_units(state)

    assert result["abort_reason"] == "UNKNOWN_SOURCE_PRIORITY"
    assert "merged_source_units" not in result

def _failed_unit():
    return {
        "status": "failed",
        "error": {"code": "X", "message": "fail"},
        "items": []
    }


def test_abort_when_all_sources_failed():
    state = {
        "source_units": {
            "arxiv": _failed_unit(),
            "huggingface": _failed_unit(),
        }
    }

    result = merge_source_units(state)

    assert result["abort_reason"] == "FETCH_ALL_SOURCES_FAILED"
    assert "merged_source_units" not in result

def test_merge_order_respects_source_priority_and_seq():
    state = {
        "source_units": {
            "huggingface": {
                "status": "ok",
                "error": None,
                "items": [
                    {"source": "huggingface", "source_seq": 1, "payload": {}},
                    {"source": "huggingface", "source_seq": 0, "payload": {}},
                ],
            },
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": [
                    {"source": "arxiv", "source_seq": 1, "payload": {}},
                    {"source": "arxiv", "source_seq": 0, "payload": {}},
                ],
            },
        }
    }

    result = merge_source_units(state)
    merged = result["merged_source_units"]

    # Orden esperado:
    # arxiv seq 0
    # arxiv seq 1
    # huggingface seq 0
    # huggingface seq 1

    assert [(x["source"], x["source_seq"]) for x in merged] == [
        ("arxiv", 0),
        ("arxiv", 1),
        ("huggingface", 0),
        ("huggingface", 1),
    ]