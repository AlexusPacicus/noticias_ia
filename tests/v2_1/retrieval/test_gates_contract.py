from __future__ import annotations


def test_gate_a_empty_input_payload(
    invoke_retrieval,
    assert_abort_reason,
    assert_exact_keys,
    assert_no_llm_keys,
):
    payload = {"query": None, "time_window": None, "top_k": None}
    state = invoke_retrieval(payload)

    assert_abort_reason(state, "EMPTY_INPUT_PAYLOAD")
    assert_exact_keys(
        state,
        {"query", "time_window", "top_k", "input_raw", "abort_reason"},
    )
    assert_no_llm_keys(state)


def test_gate_a_invalid_query(
    invoke_retrieval,
    assert_abort_reason,
    assert_exact_keys,
    assert_input_not_overwritten,
    assert_no_llm_keys,
):
    payload = {"query": "   ", "time_window": "last_7_days", "top_k": 2}
    state = invoke_retrieval(payload)

    assert_abort_reason(state, "INVALID_QUERY")
    assert_exact_keys(
        state,
        {"query", "time_window", "top_k", "input_raw", "abort_reason"},
    )
    assert_input_not_overwritten(state, payload)
    assert_no_llm_keys(state)


def test_gate_b_all_sources_failed(
    payload_valid,
    patch_fetch_snapshot,
    invoke_retrieval,
    assert_abort_reason,
    assert_exact_keys,
    assert_no_keys_after,
    assert_input_not_overwritten,
    assert_no_llm_keys,
):
    patch_fetch_snapshot(arxiv_status="failed", hf_status="failed")
    state = invoke_retrieval(payload_valid)

    assert_abort_reason(state, "FETCH_ALL_SOURCES_FAILED")
    assert_exact_keys(
        state,
        {
            "query",
            "time_window",
            "top_k",
            "input_raw",
            "input_validated",
            "source_units",
            "abort_reason",
        },
    )
    assert_no_keys_after(
        state,
        {
            "merged_source_units",
            "normalized_items",
            "filtered_items",
            "deduped_items",
            "ranked_items",
            "selected_items",
        },
    )
    assert_input_not_overwritten(state, payload_valid)
    assert_no_llm_keys(state)


def test_gate_c_no_items_in_time_window(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    make_source_item,
    fixed_now_utc,
    assert_abort_reason,
    assert_exact_keys,
    assert_no_keys_after,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)
    stale_arxiv_items = [
        make_source_item(
            source="arxiv",
            source_seq=0,
            title="Old Paper 1",
            content="agentic ai",
            published_at="2024-01-01T00:00:00Z",
            link="https://arxiv.org/abs/2401.00001",
        )
    ]
    stale_hf_items = [
        make_source_item(
            source="huggingface",
            source_seq=0,
            title="Old Paper 2",
            content="agentic ai",
            published_at="2024-01-01T00:00:00Z",
            link="https://huggingface.co/papers/2024-01-01",
        )
    ]
    patch_fetch_snapshot(arxiv_items=stale_arxiv_items, hf_items=stale_hf_items)
    state = invoke_retrieval(payload_valid)

    assert_abort_reason(state, "NO_ITEMS_IN_TIME_WINDOW")
    assert_exact_keys(
        state,
        {
            "query",
            "time_window",
            "top_k",
            "input_raw",
            "input_validated",
            "source_units",
            "merged_source_units",
            "normalized_items",
            "filtered_items",
            "abort_reason",
        },
    )
    assert state["filtered_items"] == []
    assert_no_keys_after(state, {"deduped_items", "ranked_items", "selected_items"})
    assert_no_llm_keys(state)


def test_gate_c_no_items_after_dedupe_when_dedupe_result_empty(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    make_source_item,
    fixed_now_utc,
    monkeypatch,
    assert_abort_reason,
    assert_exact_keys,
    assert_no_keys_after,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)

    items = [
        make_source_item(
            source="arxiv",
            source_seq=0,
            title="Paper A",
            content="agentic ai",
            published_at="2025-01-09T00:00:00Z",
            link="https://x/paper-a",
        ),
        make_source_item(
            source="arxiv",
            source_seq=1,
            title="Paper B",
            content="agentic ai",
            published_at="2025-01-09T00:00:00Z",
            link="https://x/paper-b",
        ),
    ]
    patch_fetch_snapshot(arxiv_items=items, hf_items=[])

    def dedupe_empty_with_abort(_state):
        return {
            "deduped_items": [],
            "abort_reason": "NO_ITEMS_AFTER_DEDUPE",
        }

    monkeypatch.setattr(
        "graph.v2_1.retrieval.graph_21.dedupe",
        dedupe_empty_with_abort,
    )

    state = invoke_retrieval(payload_valid, sources=("arxiv",))

    # Precondicion contractual del escenario.
    assert state.get("filtered_items"), "filtered_items debe ser no vacio en este escenario"

    assert_abort_reason(state, "NO_ITEMS_AFTER_DEDUPE")
    assert state.get("deduped_items") == []
    assert_exact_keys(
        state,
        {
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
            "abort_reason",
        },
    )
    assert_no_keys_after(state, {"ranked_items", "selected_items"})
    assert_no_llm_keys(state)


def test_gate_d_query_empty_after_preprocessing(
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    fixed_now_utc,
    assert_abort_reason,
    assert_exact_keys,
    assert_no_keys_after,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    payload = {"query": "the and of in", "time_window": "last_7_days", "top_k": 2}
    state = invoke_retrieval(payload)

    assert_abort_reason(state, "RANK_QUERY_EMPTY_AFTER_NORMALIZATION")
    assert_exact_keys(
        state,
        {
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
            "abort_reason",
        },
    )
    assert "ranked_items" not in state
    assert_no_keys_after(state, {"ranked_items", "selected_items"})
    assert_no_llm_keys(state)


def test_gate_e_select_missing_ranked_items(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    fixed_now_utc,
    monkeypatch,
    assert_abort_reason,
    assert_exact_keys,
    assert_missing_ranked_items_for_select_missing,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    def rank_without_output(_state):
        return {}

    monkeypatch.setattr("graph.v2_1.retrieval.graph_21.rank_bm25", rank_without_output)

    state = invoke_retrieval(payload_valid)

    assert_abort_reason(state, "SELECT_MISSING_RANKED_ITEMS")
    assert_exact_keys(
        state,
        {
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
            "abort_reason",
        },
    )
    assert_missing_ranked_items_for_select_missing(state)
    assert "selected_items" not in state
    assert_no_llm_keys(state)


def test_gate_e_select_topk_invalid_with_ranked_present(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    fixed_now_utc,
    monkeypatch,
    assert_abort_reason,
    assert_exact_keys,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    def validate_input_invalid_topk(state):
        raw = state.get("input_raw", {})
        return {
            "input_validated": {
                "query": raw.get("query"),
                "time_window": raw.get("time_window"),
                "top_k": 0,
            }
        }

    monkeypatch.setattr(
        "graph.v2_1.retrieval.graph_21.validate_input",
        validate_input_invalid_topk,
    )

    state = invoke_retrieval(payload_valid)

    assert_abort_reason(state, "SELECT_TOPK_INVALID")
    assert_exact_keys(
        state,
        {
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
            "abort_reason",
        },
    )
    assert "ranked_items" in state
    assert "selected_items" not in state
    assert_no_llm_keys(state)
