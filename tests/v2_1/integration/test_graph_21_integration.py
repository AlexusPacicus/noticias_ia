from __future__ import annotations

from copy import deepcopy

import graph.v2_1.graph_21 as g21


def _mock_summarize_ok(state):
    selected = state.get("hitl_selected_items")
    if selected is None:
        selected = state["selected_items"]
    # Return reverse order to ensure reduce is the only ordering enforcer.
    summary_items = [
        {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "summary": "ok",
            "link": item["link"],
            "source": item["source"],
        }
        for item in reversed(selected)
    ]
    return {
        "summary_items": summary_items,
        "summary_stats": {"ok": len(summary_items), "failed": 0},
    }


def _mock_summarize_all_failed(state):
    selected = state.get("hitl_selected_items")
    if selected is None:
        selected = state["selected_items"]
    return {
        "summary_items": [],
        "summary_stats": {"ok": 0, "failed": len(selected)},
    }


def _mock_summarize_partial(state):
    selected = state.get("hitl_selected_items")
    if selected is None:
        selected = state["selected_items"]
    ok_items = selected[:2]
    summary_items = [
        {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "summary": "ok",
            "link": item["link"],
            "source": item["source"],
        }
        for item in ok_items
    ]
    return {
        "summary_items": summary_items,
        "summary_stats": {"ok": len(summary_items), "failed": len(selected) - len(summary_items)},
    }


def test_happy_path_complete_without_hitl(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_ok)

    out1 = invoke_full(payload_valid)
    out2 = invoke_full(payload_valid)
    retrieval_state = invoke_retrieval(payload_valid)

    assert "abort_reason" not in out1
    assert "output" in out1
    assert out1["hitl_action"] == "accept"
    assert out1["output"]["returned_k"] <= payload_valid["top_k"]

    # Determinismo estructural hasta rank_bm25
    assert out1["ranked_items"] == out2["ranked_items"]

    # Summarize no debe recalcular ranking
    assert out1["ranked_items"] == retrieval_state["ranked_items"]

    # ranking preservado en output publico
    ranks = [item["rank_position"] for item in out1["output"]["results"]]
    assert ranks == sorted(ranks)
    assert_global_invariants(out1)


def test_hitl_subset_only_selected_items_are_summarized(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    map_calls = {"count": 0, "seen_size": None}

    def summarize_subset_only(state):
        map_calls["count"] += 1
        effective = state.get("hitl_selected_items")
        if effective is None:
            effective = state["selected_items"]
        map_calls["seen_size"] = len(effective)
        return _mock_summarize_ok(state)

    monkeypatch.setattr(g21, "summarize_map_effective", summarize_subset_only)

    def decision_provider(state):
        selected_ids = [item["canonical_id"] for item in state["selected_items"]]
        return {"action": "subset", "remove_keys": selected_ids[1:]}

    out = invoke_full(payload_valid, decision_provider=decision_provider)

    assert out["hitl_action"] == "subset"
    assert len(out["hitl_selected_items"]) == 1
    assert map_calls["count"] == 1
    assert map_calls["seen_size"] == 1
    assert out["output"]["returned_k"] == 1
    assert_global_invariants(out)


def test_hitl_empty_triggers_summary_empty_input_and_skips_summarize(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    map_calls = {"count": 0}

    def summarize_spy(state):
        map_calls["count"] += 1
        return _mock_summarize_ok(state)

    monkeypatch.setattr(g21, "summarize_map_effective", summarize_spy)

    def decision_provider(state):
        selected_ids = [item["canonical_id"] for item in state["selected_items"]]
        return {"action": "subset", "remove_keys": selected_ids}

    out = invoke_full(payload_valid, decision_provider=decision_provider)

    assert out["hitl_action"] == "subset"
    assert out["hitl_selected_items"] == []
    assert out.get("abort_reason") == "SUMMARY_EMPTY_INPUT"
    assert "output" not in out
    assert map_calls["count"] == 0
    assert_global_invariants(out)


def test_abort_dominant_upstream_keeps_abort_and_skips_downstream(
    monkeypatch,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    calls = {"hitl": 0, "summarize": 0}
    original_hitl = g21.hitl_review

    def hitl_spy(state, decision):
        calls["hitl"] += 1
        return original_hitl(state, decision)

    def summarize_spy(state):
        calls["summarize"] += 1
        return _mock_summarize_ok(state)

    monkeypatch.setattr(g21, "hitl_review", hitl_spy)
    monkeypatch.setattr(g21, "summarize_map_effective", summarize_spy)

    out = invoke_full({"query": "   ", "time_window": "last_7_days", "top_k": 3})

    assert out.get("abort_reason") == "INVALID_QUERY"
    assert "output" not in out
    assert calls["hitl"] == 0
    assert calls["summarize"] == 0
    assert "hitl_action" not in out
    assert "summary_items" not in out
    assert "summary_stats" not in out
    assert_global_invariants(out)


def test_equivalence_retrieval_vs_full_until_select(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_retrieval,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    # Determinismo temporal y fetch controlado
    patch_now_utc()
    patch_fetch_snapshot(
        arxiv_items=nominal_arxiv_items,
        hf_items=nominal_hf_items,
    )

    # Evita ruido de fases posteriores para comparar frontera Retrieval.
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_ok)

    # Ejecucion solo de RetrievalPhase
    retrieval_state = invoke_retrieval(payload_valid)

    # Ejecucion del sistema completo hasta "select"
    full_state_until_select = invoke_full(
        payload_valid,
        config={"execute_until": "select"},
    )

    # Comparar ranked_items
    assert retrieval_state["ranked_items"] == full_state_until_select["ranked_items"]
    # Comparar selected_items
    assert retrieval_state["selected_items"] == full_state_until_select["selected_items"]

    # Global invariants no se violan
    assert_global_invariants(full_state_until_select)


def test_all_items_failed_in_full_pipeline_aborts_transversally(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_all_failed)

    out = invoke_full(payload_valid)

    assert out.get("abort_reason") == "SUMMARY_ALL_ITEMS_FAILED"
    assert "output" not in out
    assert out["summary_stats"]["ok"] == 0
    assert out["summary_stats"]["failed"] > 0
    assert_global_invariants(out)


def test_partial_failure_in_full_pipeline_keeps_output_and_counts_failed(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_partial)

    out = invoke_full(payload_valid)

    assert "abort_reason" not in out
    assert "output" in out
    assert out["summary_stats"]["ok"] > 0
    assert out["summary_stats"]["failed"] > 0
    assert out["output"]["returned_k"] == out["summary_stats"]["ok"]
    assert out["output"]["failed_summaries"] == out["summary_stats"]["failed"]
    assert_global_invariants(out)


def test_summarize_does_not_read_prohibited_keys_even_if_malformed(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    original_apply = g21.apply_hitl_decision

    class PoisonValue:
        def __iter__(self):
            raise AssertionError("This key must not be read by SummarizePhase")

        def __len__(self):
            raise AssertionError("This key must not be read by SummarizePhase")

    def apply_with_poison(state):
        delta = original_apply(state)
        delta["normalized_items"] = PoisonValue()
        return delta

    monkeypatch.setattr(g21, "apply_hitl_decision", apply_with_poison)
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_ok)

    out = invoke_full(payload_valid)

    assert "output" in out
    assert "abort_reason" not in out
    assert_global_invariants(out)


def test_selected_items_not_mutated_across_full_pipeline(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    invoke_full,
    nominal_arxiv_items,
    nominal_hf_items,
    assert_global_invariants,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_ok)

    state_until_select = invoke_full(payload_valid, config={"execute_until": "select"})
    selected_snapshot = deepcopy(state_until_select["selected_items"])

    full_out = invoke_full(payload_valid)

    assert full_out["selected_items"] == selected_snapshot
    assert_global_invariants(full_out)
