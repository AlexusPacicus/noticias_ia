from __future__ import annotations

from copy import deepcopy


def test_accept_sets_action_and_empty_remove_keys(
    state_with_selected,
    invoke_hitl_node,
    assert_selected_items_not_mutated,
    assert_hitl_domain_only,
):
    before = deepcopy(state_with_selected)
    decision = {"action": "accept"}

    state = invoke_hitl_node(state_with_selected, decision)

    assert state.get("hitl_action") == "accept"
    assert state.get("hitl_remove_keys") == []
    assert "abort_reason" not in state
    assert_selected_items_not_mutated(before, state)
    assert_hitl_domain_only(before, state)


def test_subset_single_remove_key(
    state_with_selected,
    invoke_hitl_node,
    assert_selected_items_not_mutated,
    assert_hitl_domain_only,
):
    before = deepcopy(state_with_selected)
    remove_key = state_with_selected["selected_items"][0]["canonical_id"]
    decision = {"action": "subset", "remove_keys": [remove_key]}

    state = invoke_hitl_node(state_with_selected, decision)

    assert state.get("hitl_action") == "subset"
    assert state.get("hitl_remove_keys") == [remove_key]
    assert "abort_reason" not in state
    assert_selected_items_not_mutated(before, state)
    assert_hitl_domain_only(before, state)


def test_subset_multiple_remove_keys(
    state_with_selected,
    invoke_hitl_node,
    assert_selected_items_not_mutated,
    assert_hitl_domain_only,
):
    before = deepcopy(state_with_selected)
    remove_keys = [
        state_with_selected["selected_items"][0]["canonical_id"],
        state_with_selected["selected_items"][2]["canonical_id"],
    ]
    decision = {"action": "subset", "remove_keys": remove_keys}

    state = invoke_hitl_node(state_with_selected, decision)

    assert state.get("hitl_action") == "subset"
    assert state.get("hitl_remove_keys") == remove_keys
    assert "abort_reason" not in state
    assert_selected_items_not_mutated(before, state)
    assert_hitl_domain_only(before, state)


def test_subset_total_is_allowed_without_abort(
    state_with_selected,
    invoke_hitl_node,
    assert_selected_items_not_mutated,
    assert_hitl_domain_only,
):
    before = deepcopy(state_with_selected)
    remove_keys = [item["canonical_id"] for item in state_with_selected["selected_items"]]
    decision = {"action": "subset", "remove_keys": remove_keys}

    state = invoke_hitl_node(state_with_selected, decision)

    assert state.get("hitl_action") == "subset"
    assert state.get("hitl_remove_keys") == remove_keys
    assert "abort_reason" not in state
    assert_selected_items_not_mutated(before, state)
    assert_hitl_domain_only(before, state)


def test_cancel_sets_user_abort_and_omits_remove_keys(
    state_with_selected,
    invoke_hitl_node,
    assert_selected_items_not_mutated,
    assert_hitl_domain_only,
    assert_no_summarize_keys,
):
    before = deepcopy(state_with_selected)
    decision = {"action": "cancel"}

    state = invoke_hitl_node(state_with_selected, decision)

    assert state.get("hitl_action") == "cancel"
    assert state.get("abort_reason") == "USER_ABORT"
    assert "hitl_remove_keys" not in state
    assert_selected_items_not_mutated(before, state)
    assert_hitl_domain_only(before, state)
    assert_no_summarize_keys(state)


def test_result_is_deterministic_for_same_input_and_decision(
    state_with_selected,
    invoke_hitl_node,
):
    decision = {
        "action": "subset",
        "remove_keys": [state_with_selected["selected_items"][1]["canonical_id"]],
    }

    out1 = invoke_hitl_node(state_with_selected, decision)
    out2 = invoke_hitl_node(state_with_selected, decision)

    assert out1 == out2
