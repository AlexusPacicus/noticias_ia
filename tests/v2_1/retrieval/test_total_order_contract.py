from __future__ import annotations


def test_total_order_respected_nominal(
    payload_valid,
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    make_source_item,
    fixed_now_utc,
    assert_order_total,
    assert_no_llm_keys,
):
    patch_now_utc(fixed_now_utc)

    arxiv_items = [
        make_source_item(
            source="arxiv",
            source_seq=0,
            title="Gamma Paper",
            content="robotics robotics robotics",
            published_at="2025-01-09T00:00:00Z",
            link="https://example.org/gamma",
        ),
        make_source_item(
            source="arxiv",
            source_seq=1,
            title="Alpha Paper",
            content="robotics",
            published_at="2025-01-09T00:00:00Z",
            link="https://example.org/a2",
        ),
        make_source_item(
            source="arxiv",
            source_seq=2,
            title="Alpha Paper",
            content="robotics",
            published_at="2025-01-09T00:00:00Z",
            link="https://example.org/a1",
        ),
    ]
    patch_fetch_snapshot(arxiv_items=arxiv_items, hf_items=[])

    payload = {
        "query": "robotics",
        "time_window": payload_valid["time_window"],
        "top_k": 3,
    }
    state = invoke_retrieval(payload, sources=("arxiv",))

    assert "abort_reason" not in state
    assert "ranked_items" in state
    assert_order_total(state["ranked_items"])
    assert_no_llm_keys(state)


def test_total_order_triple_tie_title_and_link(
    patch_fetch_snapshot,
    patch_now_utc,
    invoke_retrieval,
    make_source_item,
    fixed_now_utc,
    assert_order_total,
):
    patch_now_utc(fixed_now_utc)

    arxiv_items = [
        make_source_item(
            source="arxiv",
            source_seq=0,
            title="B Title",
            content="robotics",
            published_at="2025-01-09T00:00:00Z",
            link="https://x/z",
        ),
        make_source_item(
            source="arxiv",
            source_seq=1,
            title="A Title",
            content="robotics",
            published_at="2025-01-09T00:00:00Z",
            link="https://x/c",
        ),
        make_source_item(
            source="arxiv",
            source_seq=2,
            title="A Title",
            content="robotics",
            published_at="2025-01-09T00:00:00Z",
            link="https://x/a",
        ),
    ]
    patch_fetch_snapshot(arxiv_items=arxiv_items, hf_items=[])

    payload = {
        "query": "unseen_token",
        "time_window": "last_7_days",
        "top_k": 3,
    }
    state = invoke_retrieval(payload, sources=("arxiv",))

    assert "abort_reason" not in state
    ranked = state["ranked_items"]
    assert [(it["title"], it["link"]) for it in ranked] == [
        ("A Title", "https://x/a"),
        ("A Title", "https://x/c"),
        ("B Title", "https://x/z"),
    ]
    assert_order_total(ranked)
