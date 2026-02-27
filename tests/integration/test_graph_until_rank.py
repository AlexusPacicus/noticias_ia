import pytest
from datetime import datetime, timedelta, timezone
from graph.v2.graph import build_graph


def fake_fetch_arxiv(state):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=1)).isoformat()
    return {
        "source_units": {
            "arxiv": {
                "status": "ok",
                "error": None,
                "items": [
                    {
                        "source": "arxiv",
                        "source_seq": 0,
                        "fetched_at": "2026-02-20T00:00:00Z",
                        "payload": {
                            "title": "Reinforcement Learning Paper",
                            "abstract": "reinforcement learning methods",
                            "published_at": recent,
                            "link": "https://arxiv.org/abs/2401.12345v2",
                        },
                    }
                ],
            }
        }
    }


def fake_fetch_huggingface(state):
    return {
        "source_units": {
            "huggingface": {
                "status": "ok",
                "error": None,
                "items": [],
            }
        }
    }


def _patch_summarize_ok(monkeypatch):
    def summarize_ok(state):
        selected = state.get("selected_items", []) or []
        summary_items = [
            {
                "rank_position": item["rank_position"],
                "title": item["title"],
                "summary": "ok",
                "link": item["link"],
                "source": item["source"],
            }
            for item in selected
        ]
        ok = len(summary_items)
        failed = 0

        return {
            "summary_items": summary_items,
            "summary_stats": {"ok": ok, "failed": failed},
        }

    monkeypatch.setattr("graph.v2.graph.summarize_map", summarize_ok)


def test_graph_executes_until_rank(monkeypatch):
    monkeypatch.setattr(
        "graph.v2.graph.fetch_arxiv",
        fake_fetch_arxiv,
    )
    monkeypatch.setattr(
        "graph.v2.graph.fetch_huggingface",
        fake_fetch_huggingface,
    )
    _patch_summarize_ok(monkeypatch)

    g = build_graph()   # <-- compila DESPUÉS del monkeypatch

    result = g.invoke({
        "query": "reinforcement learning",
        "time_window": "last_7_days",
        "top_k": 3,
    })

    assert "abort_reason" not in result
    assert "deduped_items" in result
    assert "ranked_items" in result
