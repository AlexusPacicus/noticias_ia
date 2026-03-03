from __future__ import annotations

from copy import deepcopy

import graph.v2_1.hitl.graph_21 as hitl_graph_21


def test_hitl_graph_runs_in_isolation_with_minimal_valid_state(
    state_with_selected,
    invoke_hitl,
    assert_selected_items_not_mutated,
    assert_hitl_domain_only,
):
    before = deepcopy(state_with_selected)
    decision = {"action": "accept"}

    state = invoke_hitl(state_with_selected, decision)

    assert state.get("hitl_action") == "accept"
    assert state.get("hitl_remove_keys") == []
    assert_selected_items_not_mutated(before, state)
    assert_hitl_domain_only(before, state)


def test_subgraph_executes_only_hitl_review_node(
    state_with_selected,
    invoke_hitl,
    monkeypatch,
):
    events = []
    original = hitl_graph_21.hitl_review

    def traced_hitl_review(state, decision):
        events.append("hitl_review")
        return original(state, decision)

    monkeypatch.setattr(hitl_graph_21, "hitl_review", traced_hitl_review)

    decision = {"action": "accept"}
    state = invoke_hitl(state_with_selected, decision)

    assert "abort_reason" not in state
    assert events == ["hitl_review"]
