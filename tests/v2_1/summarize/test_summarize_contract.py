from __future__ import annotations

from copy import deepcopy

import graph.v2_1.summarize.graph_21 as summarize_graph_21


def _map_all_ok(state):
    selected = state["selected_items"]
    summary_items = [
        {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "link": item["link"],
            "source": item["source"],
            "summary": "ok",
        }
        for item in selected
    ]
    return {
        "summary_items": summary_items,
        "summary_stats": {"ok": len(summary_items), "failed": 0},
    }


def _map_all_failed(state):
    selected = state["selected_items"]
    return {
        "summary_items": [],
        "summary_stats": {"ok": 0, "failed": len(selected)},
    }


def test_summary_empty_input_aborts_without_map_and_without_llm(
    invoke_summarize,
    input_validated,
    monkeypatch,
):
    calls = {"map": 0}

    def map_spy(state):
        calls["map"] += 1
        return _map_all_ok(state)

    monkeypatch.setattr(summarize_graph_21, "summarize_map", map_spy)
    out = invoke_summarize({"selected_items": [], "input_validated": input_validated})

    assert out.get("abort_reason") == "SUMMARY_EMPTY_INPUT"
    assert "summary_items" not in out
    assert "summary_stats" not in out
    assert "output" not in out
    assert calls["map"] == 0


def test_summary_all_items_failed_aborts_without_output(
    base_state,
    invoke_summarize,
    monkeypatch,
    assert_structural_invariants,
):
    before = deepcopy(base_state)
    monkeypatch.setattr(summarize_graph_21, "summarize_map", _map_all_failed)
    out = invoke_summarize(base_state)

    assert out.get("abort_reason") == "SUMMARY_ALL_ITEMS_FAILED"
    assert out.get("summary_stats") == {"ok": 0, "failed": len(before["selected_items"])}
    assert "output" not in out
    assert_structural_invariants(before, out)


def test_rank_position_is_preserved_and_output_is_sorted(
    base_state,
    invoke_summarize,
    monkeypatch,
    assert_structural_invariants,
):
    before = deepcopy(base_state)
    monkeypatch.setattr(summarize_graph_21, "summarize_map", _map_all_ok)
    out = invoke_summarize(base_state)

    output = out["output"]
    ranks = [item["rank_position"] for item in output["results"]]
    assert ranks == sorted(ranks)
    assert output["returned_k"] == out["summary_stats"]["ok"]
    assert output["failed_summaries"] == out["summary_stats"]["failed"]
    assert_structural_invariants(before, out)


def test_hitl_override_uses_hitl_selected_items_only(
    base_state,
    invoke_summarize,
    monkeypatch,
    assert_structural_invariants,
):
    before = deepcopy(base_state)
    hitl_subset = [before["selected_items"][1]]
    state = {
        **before,
        "hitl_selected_items": hitl_subset,
        "hitl_remove_keys": [
            before["selected_items"][0]["canonical_id"],
            before["selected_items"][2]["canonical_id"],
        ],
    }
    map_calls = {"count": 0}

    def map_ok_counted(state_for_map):
        map_calls["count"] += 1
        return _map_all_ok(state_for_map)

    monkeypatch.setattr(summarize_graph_21, "summarize_map", map_ok_counted)
    out = invoke_summarize(state)

    assert map_calls["count"] == 1
    assert out["summary_stats"]["ok"] + out["summary_stats"]["failed"] == 1
    assert out["output"]["returned_k"] == 1
    assert {r["title"] for r in out["output"]["results"]} == {hitl_subset[0]["title"]}
    assert_structural_invariants(state, out)


def test_structural_invariants_and_no_ranking_recalc(
    base_state,
    invoke_summarize,
    monkeypatch,
    assert_structural_invariants,
):
    before = deepcopy(base_state)
    state = {
        **base_state,
        "ranked_items": [{"rank_position": 999, "title": "should never be read"}],
    }
    map_calls = {"count": 0}

    def map_spy(state_for_map):
        map_calls["count"] += 1
        assert "selected_items" in state_for_map
        assert "ranked_items" not in state_for_map
        return _map_all_ok(state_for_map)

    monkeypatch.setattr(summarize_graph_21, "summarize_map", map_spy)
    out = invoke_summarize(state)

    assert "output" in out
    assert map_calls["count"] == 1
    assert 999 not in [item["rank_position"] for item in out["output"]["results"]]
    assert out["output"]["requested_k"] == before["input_validated"]["top_k"]
    assert_structural_invariants(state, out)
