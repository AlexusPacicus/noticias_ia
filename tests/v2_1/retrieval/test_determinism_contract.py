import pytest
from datetime import datetime, timezone

from graph.v2_1.retrieval.graph_21 import build_retrieval_graph


FIXED_NOW_UTC = datetime(2025, 1, 10, tzinfo=timezone.utc)
PUBLISHED_AT_IN_WINDOW = "2025-01-09T00:00:00Z"
FETCHED_AT = "2025-01-10T00:00:00Z"


PAYLOAD = {
    "query": "agentic ai",
    "time_window": "last_7_days",
    "top_k": 2,
}

ARXIV_ITEMS = [
    {
        "source": "arxiv",
        "source_seq": 0,
        "fetched_at": FETCHED_AT,
        "payload": {
            "title": "Agentic AI for X",
            "content": "agentic systems and planning",
            "published_at": PUBLISHED_AT_IN_WINDOW,
            "link": "https://arxiv.org/abs/2501.00001",
        },
    },
    {
        "source": "arxiv",
        "source_seq": 1,
        "fetched_at": FETCHED_AT,
        "payload": {
            "title": "Tool Use in LLMs",
            "content": "tools, agents, calling",
            "published_at": PUBLISHED_AT_IN_WINDOW,
            "link": "https://arxiv.org/abs/2501.00002",
        },
    },
]

HF_ITEMS = [
    {
        "source": "huggingface",
        "source_seq": 0,
        "fetched_at": FETCHED_AT,
        "payload": {
            "title": "Daily Paper A",
            "content": "agentic ai overview",
            "published_at": PUBLISHED_AT_IN_WINDOW,
            "link": "https://huggingface.co/papers/2026-02-22",
        },
    }
]


def _patch_fixed_fetch_snapshot(monkeypatch):
    def fixed_fetch_arxiv(_state):
        return {
            "source_units": {
                "arxiv": {
                    "status": "ok",
                    "error": None,
                    "items": ARXIV_ITEMS,
                }
            }
        }

    def fixed_fetch_huggingface(_state):
        return {
            "source_units": {
                "huggingface": {
                    "status": "ok",
                    "error": None,
                    "items": HF_ITEMS,
                }
            }
        }

    monkeypatch.setattr(
        "graph.v2_1.retrieval.graph_21.fetch_arxiv",
        fixed_fetch_arxiv,
    )
    monkeypatch.setattr(
        "graph.v2_1.retrieval.graph_21.fetch_huggingface",
        fixed_fetch_huggingface,
    )

    monkeypatch.setattr(
        "graph.v2.nodes.filter_by_time_window._now_utc",
        lambda: FIXED_NOW_UTC,
    )


@pytest.mark.parametrize(
    "sources",
    [
        None,
        ("arxiv",),
        ("huggingface",),
    ],
)
def test_determinism_same_snapshot_same_output(monkeypatch, sources):
    _patch_fixed_fetch_snapshot(monkeypatch)

    retrieval_graph = build_retrieval_graph(live=False, sources=sources)

    out1 = retrieval_graph.invoke(PAYLOAD)
    out2 = retrieval_graph.invoke(PAYLOAD)

    assert "abort_reason" not in out1
    assert "abort_reason" not in out2
    assert out1 == out2
