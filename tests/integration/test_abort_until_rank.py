import pytest
from graph.v2.graph import build_graph


def fake_fetch_empty(state):
    return {
        "source_units": {
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": [],   # ← fuerza filtro vacío
            }
        }
    }


def test_abort_stops_after_filter(monkeypatch):
    monkeypatch.setattr(
        "graph.v2.graph.fetch_arxiv",
        fake_fetch_empty,
    )
    monkeypatch.setattr(
        "graph.v2.graph.fetch_huggingface",
        fake_fetch_empty,
    )

    g = build_graph()

    result = g.invoke({
        "query": "reinforcement learning",
        "time_window": "last_7_days",
        "top_k": 3,
    })

    # Debe abortar
    assert result.get("abort_reason") == "NO_ITEMS_IN_TIME_WINDOW"

    # Y NO debe existir nada posterior
    assert "deduped_items" not in result
    assert "ranked_items" not in result