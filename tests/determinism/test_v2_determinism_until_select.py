import pytest


def _patch_passthrough_time(gmod, monkeypatch):
    def passthrough_filter(state):
        return {"filtered_items": state.get("normalized_items", [])}
    monkeypatch.setattr(gmod, "filter_by_time_window", passthrough_filter)


def _patch_summarize_ok(gmod, monkeypatch):
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

    monkeypatch.setattr(gmod, "summarize_map", summarize_ok)


def _patch_fixed_fetch_snapshot(gmod, monkeypatch):
    arxiv_items = [
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

    hf_items = [
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

    def ok_arxiv(_state):
        return {"source_units": {"arxiv": {"status": "ok", "error": None, "items": arxiv_items}}}

    def ok_hf(_state):
        return {"source_units": {"huggingface": {"status": "ok", "error": None, "items": hf_items}}}

    monkeypatch.setattr(gmod, "fetch_arxiv", ok_arxiv)
    monkeypatch.setattr(gmod, "fetch_huggingface", ok_hf)


def _build_after_patches(gmod):
    return gmod.build_graph()


@pytest.mark.integration
def test_determinism_until_select_same_input_same_snapshot(monkeypatch):
    import graph.v2.graph as gmod

    _patch_fixed_fetch_snapshot(gmod, monkeypatch)
    _patch_passthrough_time(gmod, monkeypatch)
    _patch_summarize_ok(gmod, monkeypatch)

    g = _build_after_patches(gmod)
    inp = {"query": "agentic ai", "time_window": "last_7_days", "top_k": 2}

    out1 = g.invoke(inp)
    out2 = g.invoke(inp)

    assert "abort_reason" not in out1
    assert "abort_reason" not in out2
    assert out1["ranked_items"] == out2["ranked_items"]
    assert out1["selected_items"] == out2["selected_items"]


@pytest.mark.integration
def test_rank_total_order_tie_breaks_title_then_link(monkeypatch):
    import graph.v2.graph as gmod

    _patch_passthrough_time(gmod, monkeypatch)
    _patch_summarize_ok(gmod, monkeypatch)

    items = [
        {
            "source": "arxiv",
            "source_seq": 0,
            "fetched_at": "2026-02-23T00:00:00Z",
            "payload": {
                "title": "B title",
                "content": "agentic ai",
                "published_at": "2026-02-22T00:00:00Z",
                "link": "https://example.com/z",
            },
        },
        {
            "source": "arxiv",
            "source_seq": 1,
            "fetched_at": "2026-02-23T00:00:00Z",
            "payload": {
                "title": "A title",
                "content": "agentic ai",
                "published_at": "2026-02-22T00:00:00Z",
                "link": "https://example.com/a",
            },
        },
    ]

    def ok_arxiv(_state):
        return {"source_units": {"arxiv": {"status": "ok", "error": None, "items": items}}}

    def ok_hf(_state):
        return {"source_units": {"huggingface": {"status": "ok", "error": None, "items": []}}}

    monkeypatch.setattr(gmod, "fetch_arxiv", ok_arxiv)
    monkeypatch.setattr(gmod, "fetch_huggingface", ok_hf)

    g = _build_after_patches(gmod)
    out = g.invoke({"query": "agentic ai", "time_window": "last_7_days", "top_k": 2})

    assert "abort_reason" not in out
    ranked = out["ranked_items"]
    assert ranked[0]["title"] == "A title"
    assert ranked[1]["title"] == "B title"
    assert out["selected_items"] == ranked[:2]
