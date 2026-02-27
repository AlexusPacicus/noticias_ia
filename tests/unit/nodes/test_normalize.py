from graph.v2.nodes.normalize import normalize

def test_preserves_order():
    state = {
        "merged_source_units": [
            {
                "source": "arxiv",
                "payload": {
                    "title": "A",
                    "abstract": "AA",
                    "published_at": "2025-01-01T00:00:00Z",
                    "link": "https://arxiv.org/abs/1234.0001",
                },
            },
            {
                "source": "huggingface",
                "payload": {
                    "title": "B",
                    "abstract": "BB",
                    "published_at": "2025-01-01T00:00:00Z",
                    "link": "https://huggingface.co/paper/1",
                },
            },
        ]
    }

    out = normalize(state)
    titles = [x["title"] for x in out["normalized_items"]]
    assert titles == ["A", "B"]

def test_discards_invalid_item():
    state = {
        "merged_source_units": [
            {
                "source": "arxiv",
                "payload": {
                    "title": None,
                    "abstract": "AA",
                    "published_at": "2025-01-01T00:00:00Z",
                    "link": "https://arxiv.org/abs/1234.0001",
                },
            }
        ]
    }

    out = normalize(state)
    assert out["normalized_items"] == []

def test_shape_exact():
    state = {
        "merged_source_units": [
            {
                "source": "arxiv",
                "payload": {
                    "title": "A",
                    "abstract": "AA",
                    "published_at": "2025-01-01T00:00:00Z",
                    "link": "https://arxiv.org/abs/1234.0001",
                },
            }
        ]
    }

    out = normalize(state)
    item = out["normalized_items"][0]

    assert set(item.keys()) == {
        "title",
        "content",
        "published_at",
        "link",
        "source",
        "canonical_id",
    }   

def test_does_not_mutate_input():
    original = {
        "merged_source_units": [
            {
                "source": "arxiv",
                "payload": {
                    "title": "A",
                    "abstract": "AA",
                    "published_at": "2025-01-01T00:00:00Z",
                    "link": "https://arxiv.org/abs/1234.0001",
                },
            }
        ]
    }

    import copy
    state = copy.deepcopy(original)

    normalize(state)

    assert state == original


def _su(source: str, seq: int, payload: dict) -> dict:
    return {
        "source": source,
        "source_seq": seq,
        "fetched_at": "2026-02-23T00:00:00Z",
        "payload": payload,
    }


def test_normalize_accepts_payload_abstract_as_content():
    state = {
        "merged_source_units": [
            _su(
                "arxiv",
                0,
                {
                    "title": "Paper A",
                    "abstract": "this is the abstract",
                    "published_at": "2026-02-22T00:00:00Z",
                    "link": "https://arxiv.org/abs/2501.00001",
                },
            )
        ]
    }

    delta = normalize(state)

    assert "abort_reason" not in delta
    items = delta["normalized_items"]
    assert len(items) == 1
    assert items[0]["title"] == "Paper A"
    assert items[0]["content"] == "this is the abstract"


def test_normalize_accepts_payload_content_when_abstract_missing():
    state = {
        "merged_source_units": [
            _su(
                "arxiv",
                0,
                {
                    "title": "Paper B",
                    "content": "this is the content",
                    "published_at": "2026-02-22T00:00:00Z",
                    "link": "https://arxiv.org/abs/2501.00002",
                },
            )
        ]
    }

    delta = normalize(state)

    assert "abort_reason" not in delta
    items = delta["normalized_items"]
    assert len(items) == 1
    assert items[0]["title"] == "Paper B"
    assert items[0]["content"] == "this is the content"


def test_normalize_preserves_order_across_units():
    state = {
        "merged_source_units": [
            _su(
                "arxiv",
                0,
                {
                    "title": "First",
                    "content": "x",
                    "published_at": "2026-02-22T00:00:00Z",
                    "link": "https://arxiv.org/abs/2501.00003",
                },
            ),
            _su(
                "huggingface",
                0,
                {
                    "title": "Second",
                    "abstract": "y",
                    "published_at": "2026-02-22T00:00:00Z",
                    "link": "https://huggingface.co/papers/2026-02-22",
                },
            ),
        ]
    }

    delta = normalize(state)

    assert "abort_reason" not in delta
    items = delta["normalized_items"]
    assert [it["title"] for it in items] == ["First", "Second"]