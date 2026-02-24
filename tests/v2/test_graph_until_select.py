import pytest


def _get_graph_module():
    import graph.v2.graph as gmod

    return gmod


def _get_graph(gmod):
    # Evita depender de un graph precompilado a nivel módulo
    if hasattr(gmod, "build_graph"):
        return gmod.build_graph()
    return gmod.graph


def _patch_passthrough_time(gmod, monkeypatch):
    def passthrough_filter(state):
        normalized = state.get("normalized_items", [])
        return {"filtered_items": normalized}

    monkeypatch.setattr(gmod, "filter_by_time_window", passthrough_filter)


def _patch_summarize_ok(gmod, monkeypatch):
    def summarize_ok(state):
        selected = state.get("selected_items", []) or []
        summary_items = list(selected)
        ok = len(summary_items)
        failed = 0

        return {
            "summary_items": summary_items,
            "summary_stats": {"ok": ok, "failed": failed},
        }

    monkeypatch.setattr(gmod, "summarize_map", summarize_ok)


@pytest.mark.integration
def test_graph_until_select_happy_path_prefix_exact(monkeypatch):
    gmod = _get_graph_module()

    _patch_passthrough_time(gmod, monkeypatch)
    _patch_summarize_ok(gmod, monkeypatch)

    g = _get_graph(gmod)
    out = g.invoke({"query": "agentic ai", "time_window": "last_7_days", "top_k": 2})

    assert "abort_reason" not in out
    ranked = out["ranked_items"]
    selected = out["selected_items"]
    assert selected == ranked[: min(2, len(ranked))]


@pytest.mark.integration
def test_graph_until_select_topk_gt_len_no_abort(monkeypatch):
    gmod = _get_graph_module()

    _patch_passthrough_time(gmod, monkeypatch)
    _patch_summarize_ok(gmod, monkeypatch)

    g = _get_graph(gmod)
    out = g.invoke({"query": "agentic ai", "time_window": "last_7_days", "top_k": 5})

    assert "abort_reason" not in out
    ranked = out["ranked_items"]
    selected = out["selected_items"]
    assert selected == ranked[: min(5, len(ranked))]


@pytest.mark.integration
def test_abort_fetch_all_sources_failed_stops_before_normalize(monkeypatch):
    gmod = _get_graph_module()

    # Ambos fetch_* deben modelar fallo como status="failed" (sin abort_reason)
    def fail_arxiv(_state):
        return {
            "source_units": {
                "arxiv": {
                    "status": "failed",
                    "error": {"code": "X", "message": "x"},
                    "items": [],
                }
            }
        }

    def fail_huggingface(_state):
        return {
            "source_units": {
                "huggingface": {
                    "status": "failed",
                    "error": {"code": "Y", "message": "y"},
                    "items": [],
                }
            }
        }

    monkeypatch.setattr(gmod, "fetch_arxiv", fail_arxiv)
    monkeypatch.setattr(gmod, "fetch_huggingface", fail_huggingface)

    g = _get_graph(gmod)
    out = g.invoke({"query": "agentic ai", "time_window": "last_7_days", "top_k": 2})

    assert out.get("abort_reason") == "FETCH_ALL_SOURCES_FAILED"

    # Si el gate está bien, NO deben existir claves posteriores
    assert "merged_source_units" not in out
    assert "normalized_items" not in out
    assert "filtered_items" not in out
    assert "deduped_items" not in out
    assert "ranked_items" not in out
    assert "selected_items" not in out