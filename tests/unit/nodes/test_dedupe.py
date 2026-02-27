from graph.v2.nodes.dedupe import dedupe


def test_dedupe_basic():
    state = {
        "filtered_items": [
            {"canonical_id": "a"},
            {"canonical_id": "a"},
            {"canonical_id": "b"},
        ]
    }

    result = dedupe(state)

    assert "abort_reason" not in result
    assert [i["canonical_id"] for i in result["deduped_items"]] == ["a", "b"]


def test_dedupe_abort_when_empty():
    state = {
        "filtered_items": []
    }

    result = dedupe(state)

    assert result["abort_reason"] == "NO_ITEMS_AFTER_DEDUPE"
    assert "deduped_items" not in result

def test_dedupe_non_consecutive():
    state = {
        "filtered_items": [
            {"canonical_id": "a"},
            {"canonical_id": "b"},
            {"canonical_id": "a"},
        ]
    }

    result = dedupe(state)

    assert [i["canonical_id"] for i in result["deduped_items"]] == ["a", "b"]

def test_dedupe_no_mutation():
    items = [
        {"canonical_id": "a"},
        {"canonical_id": "a"},
    ]
    original = list(items)

    state = {"filtered_items": items}
    _ = dedupe(state)

    assert items == original