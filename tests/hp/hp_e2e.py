import pytest


@pytest.mark.integration
def test_e2e_happy_path(monkeypatch):
    import graph.v2.graph as gmod

    # 1. Snapshot fijo
    def ok_arxiv(_state):
        return {
            "source_units": {
                "arxiv": {
                    "status": "ok",
                    "error": None,
                    "items": [
                        {
                            "source": "arxiv",
                            "source_seq": 0,
                            "fetched_at": "2026-02-23T00:00:00Z",
                            "payload": {
                                "title": "Agentic AI Systems",
                                "content": "agentic ai reinforcement",
                                "published_at": "2026-02-22T00:00:00Z",
                                "link": "https://arxiv.org/abs/2501.00001",
                            },
                        }
                    ],
                }
            }
        }

    def ok_hf(_state):
        return {
            "source_units": {
                "huggingface": {
                    "status": "ok",
                    "error": None,
                    "items": [],
                }
            }
        }

    monkeypatch.setattr(gmod, "fetch_arxiv", ok_arxiv)
    monkeypatch.setattr(gmod, "fetch_huggingface", ok_hf)

    # 2. Mock summary válido
    def fake_generate_summary(_item):
        return {
            "summary": "Idea. Relacion."
        }

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        fake_generate_summary
    )

    g = gmod.build_graph()

    out = g.invoke({
        "query": "agentic ai",
        "time_window": "last_7_days",
        "top_k": 3,
    })

    # --- ASSERTS CONTRACTUALES ---
    assert "abort_reason" not in out
    assert "output" in out

    output = out["output"]

    assert output["returned_k"] <= output["requested_k"]
    assert len(output["results"]) == output["returned_k"]

    # Lista cerrada de claves
    allowed_keys = {
        "query",
        "time_window",
        "top_k",
        "input_raw",
        "input_validated",
        "source_units",
        "merged_source_units",
        "normalized_items",
        "filtered_items",
        "deduped_items",
        "ranked_items",
        "selected_items",
        "summary_items",
        "summary_stats",
        "output",
    }

    assert set(out.keys()).issubset(allowed_keys)
