from __future__ import annotations


def test_no_illegal_keys_created_nominal(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    fixed_now_utc,
    assert_allowed_retrieval_keys_only,
):
    patch_now_utc(fixed_now_utc)
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    state = invoke_retrieval(payload_valid)

    assert_allowed_retrieval_keys_only(state)


def test_no_llm_keys_exist_nominal(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    nominal_arxiv_items,
    nominal_hf_items,
    fixed_now_utc,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)

    state = invoke_retrieval(payload_valid)

    assert_no_llm_keys(state)
