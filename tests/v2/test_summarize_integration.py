import pytest
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
recent = (now - timedelta(days=1)).isoformat()

from graph.v2.graph import build_graph


# -----------------------------------------
# Helpers (fuera de los tests)
# -----------------------------------------

def build_fake_fetchers(now):

    def fake_fetch_arxiv(state):
        return {
            "source_units": {
                "arxiv": {
                    "status": "ok",
                    "error": None,
                    "items": [
                        {
                            "source": "arxiv",
                            "source_seq": 0,
                            "payload": {
                                "title": "Paper A",
                                "content": "Content A",
                                "published_at": now,
                                "link": "a1",
                            },
                        }
                    ],
                }
            }
        }

    def fake_fetch_hf(state):
        return {
            "source_units": {
                "huggingface": {
                    "status": "ok",
                    "error": None,
                    "items": [
                        {
                            "source": "huggingface",
                            "source_seq": 0,
                            "payload": {
                                "title": "Paper B",
                                "content": "Content B",
                                "published_at": now,
                                "link": "b1",
                            },
                        }
                    ],
                }
            }
        }

    return fake_fetch_arxiv, fake_fetch_hf


# -----------------------------------------
# TEST 1 — Happy path completo
# -----------------------------------------

def test_full_pipeline_happy_path(monkeypatch):

    fake_fetch_arxiv, fake_fetch_hf = build_fake_fetchers(recent)
    # Parchear ANTES de build_graph para que el grafo use los fakes
    monkeypatch.setattr("graph.v2.graph.fetch_arxiv", fake_fetch_arxiv)
    monkeypatch.setattr("graph.v2.graph.fetch_huggingface", fake_fetch_hf)

    app = build_graph()

    def fake_generate(item):
        return {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "idea_clave": "x",
            "relacion_con_query": "y",
            "link": item["link"],
            "source": item["source"],
        }

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        fake_generate
    )

    result = app.invoke({
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 2,
    })

    assert "abort_reason" not in result
    assert "output" in result
    assert result["output"]["returned_k"] > 0


# -----------------------------------------
# TEST 2 — Abort en reduce
# -----------------------------------------

def test_full_pipeline_abort_in_reduce(monkeypatch):

    fake_fetch_arxiv, fake_fetch_hf = build_fake_fetchers(recent)
    monkeypatch.setattr("graph.v2.graph.fetch_arxiv", fake_fetch_arxiv)
    monkeypatch.setattr("graph.v2.graph.fetch_huggingface", fake_fetch_hf)

    app = build_graph()

    def always_fail(item):
        raise RuntimeError()

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        always_fail
    )

    result = app.invoke({
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 2,
    })

    assert result["abort_reason"] == "SUMMARY_ALL_ITEMS_FAILED"
    assert "output" not in result