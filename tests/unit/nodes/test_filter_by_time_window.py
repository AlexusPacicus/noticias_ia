from datetime import datetime, timezone, timedelta
from graph.v2.nodes.filter_by_time_window import filter_by_time_window


def test_inclusive_cutoff(monkeypatch):
    fixed_now = datetime(2025, 1, 10, tzinfo=timezone.utc)

    monkeypatch.setattr(
        "graph.v2.nodes.filter_by_time_window._now_utc",
        lambda: fixed_now
    )

    state = {
        "normalized_items": [
            {
                "title": "A",
                "content": "AA",
                "published_at": "2025-01-03T00:00:00Z",  # exactly 7 days before
                "link": "x",
                "source": "arxiv",
                "canonical_id": "id1",
            }
        ],
        "input_validated": {
            "time_window": "last_7_days"
        }
    }

    out = filter_by_time_window(state)
    assert len(out["filtered_items"]) == 1

def test_excludes_old_item(monkeypatch):
    fixed_now = datetime(2025, 1, 10, tzinfo=timezone.utc)

    monkeypatch.setattr(
        "graph.v2.nodes.filter_by_time_window._now_utc",
        lambda: fixed_now
    )

    state = {
        "normalized_items": [
            {
                "title": "Old",
                "content": "AA",
                "published_at": "2024-12-01T00:00:00Z",
                "link": "x",
                "source": "arxiv",
                "canonical_id": "id1",
            }
        ],
        "input_validated": {
            "time_window": "last_7_days"
        }
    }

    out = filter_by_time_window(state)
    assert out["abort_reason"] == "NO_ITEMS_IN_TIME_WINDOW"
    assert out["filtered_items"] == []

def test_preserves_order(monkeypatch):
    fixed_now = datetime(2025, 1, 10, tzinfo=timezone.utc)

    monkeypatch.setattr(
        "graph.v2.nodes.filter_by_time_window._now_utc",
        lambda: fixed_now
    )

    state = {
        "normalized_items": [
            {
                "title": "A",
                "content": "AA",
                "published_at": "2025-01-09T00:00:00Z",
                "link": "x",
                "source": "arxiv",
                "canonical_id": "id1",
            },
            {
                "title": "B",
                "content": "BB",
                "published_at": "2025-01-08T00:00:00Z",
                "link": "y",
                "source": "arxiv",
                "canonical_id": "id2",
            },
        ],
        "input_validated": {
            "time_window": "last_7_days"
        }
    }

    out = filter_by_time_window(state)
    titles = [x["title"] for x in out["filtered_items"]]
    assert titles == ["A", "B"]

def test_invalid_date_discarded(monkeypatch):
    fixed_now = datetime(2025, 1, 10, tzinfo=timezone.utc)

    monkeypatch.setattr(
        "graph.v2.nodes.filter_by_time_window._now_utc",
        lambda: fixed_now
    )

    state = {
        "normalized_items": [
            {
                "title": "Bad",
                "content": "AA",
                "published_at": "invalid-date",
                "link": "x",
                "source": "arxiv",
                "canonical_id": "id1",
            }
        ],
        "input_validated": {
            "time_window": "last_7_days"
        }
    }

    out = filter_by_time_window(state)
    assert out["abort_reason"] == "NO_ITEMS_IN_TIME_WINDOW"
    assert out["filtered_items"] == []
