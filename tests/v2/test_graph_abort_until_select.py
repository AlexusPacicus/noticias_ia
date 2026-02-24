import pytest

def _get_graph_module():
    import graph.v2.graph as gmod
    return gmod

def _get_graph(gmod):
    if hasattr(gmod, "build_graph"):
        return gmod.build_graph()
    return gmod.graph


@pytest.mark.integration
def test_abort_fetch_all_sources_failed_stops_before_normalize(monkeypatch):
    gmod = _get_graph_module()

    # Forzamos ambos fetch_* a failed (contrato: no abort, solo status failed)
    def fail_arxiv(_state):
        return {"source_units": {"arxiv": {"status": "failed", "error": {"code": "X", "message": "x"}, "items": []}}}

    def fail_hf(_state):
        return {"source_units": {"huggingface": {"status": "failed", "error": {"code": "Y", "message": "y"}, "items": []}}}

    monkeypatch.setattr(gmod, "fetch_arxiv", fail_arxiv)
    monkeypatch.setattr(gmod, "fetch_huggingface", fail_hf)

    g = _get_graph(gmod)
    out = g.invoke({"query": "agentic ai", "time_window": "last_7_days", "top_k": 2})

    assert out.get("abort_reason") == "FETCH_ALL_SOURCES_FAILED"
    assert "merged_source_units" not in out
    assert "normalized_items" not in out
    assert "selected_items" not in out