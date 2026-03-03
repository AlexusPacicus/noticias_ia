import pytest

from graph.v2.graph import build_graph
from graph.v2_1.retrieval.graph_21 import build_retrieval_graph


PAYLOAD = {
    "query": "agentic ai",
    "time_window": "last_7_days",
    "top_k": 2,
}

ARXIV_ITEMS = [
    {
        "source": "arxiv",
        "source_seq": 0,
        "fetched_at": "2026-02-23T00:00:00Z",
        "payload": {
            "title": "Agentic AI for X",
            "content": "agentic systems and planning",
            "published_at": "2026-02-22T00:00:00Z",
            "link": "https://arxiv.org/abs/2501.00001",
        },
    },
    {
        "source": "arxiv",
        "source_seq": 1,
        "fetched_at": "2026-02-23T00:00:00Z",
        "payload": {
            "title": "Tool Use in LLMs",
            "content": "tools, agents, calling",
            "published_at": "2026-02-22T00:00:00Z",
            "link": "https://arxiv.org/abs/2501.00002",
        },
    },
]

HF_ITEMS = [
    {
        "source": "huggingface",
        "source_seq": 0,
        "fetched_at": "2026-02-23T00:00:00Z",
        "payload": {
            "title": "Daily Paper A",
            "content": "agentic ai overview",
            "published_at": "2026-02-22T00:00:00Z",
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

    monkeypatch.setattr("graph.v2.graph.fetch_arxiv", fixed_fetch_arxiv)
    monkeypatch.setattr(
        "graph.v2.graph.fetch_huggingface",
        fixed_fetch_huggingface,
    )
    monkeypatch.setattr(
        "graph.v2_1.retrieval.graph_21.fetch_arxiv",
        fixed_fetch_arxiv,
    )
    monkeypatch.setattr(
        "graph.v2_1.retrieval.graph_21.fetch_huggingface",
        fixed_fetch_huggingface,
    )


@pytest.mark.parametrize(
    "sources",
    [
        None,
        ("arxiv",),
        ("huggingface",),
    ],
)
def test_equivalence_execute_until_select(monkeypatch, sources):
    _patch_fixed_fetch_snapshot(monkeypatch)

    full_graph = build_graph(live=False, sources=sources)
    retrieval_graph = build_retrieval_graph(live=False, sources=sources)

    state_full = full_graph.invoke(PAYLOAD, config={"execute_until": "select"})
    state_retrieval = retrieval_graph.invoke(PAYLOAD)

    assert state_full == state_retrieval
