from datetime import datetime

_KIND_PRIORITY = {"release": 0, "paper": 1, "news": 2}


def _sort_key(item: dict):
    """
    Ranking A contractual:
    1) published_at desc (missing => last)
    2) kind priority: release > paper > news
    3) title asc
    4) link asc
    """
    published = item.get("published_at")

    # Avoid datetime.min.timestamp() (can raise on some platforms).
    if isinstance(published, datetime):
        # Use timestamp for numeric ordering; negate later for desc.
        date_ts = published.timestamp()
    else:
        # Missing/invalid => last
        date_ts = float("-inf")

    return (
        -date_ts,  # desc by time
        _KIND_PRIORITY.get(item.get("kind"), 99),
        item.get("title", "") or "",
        item.get("link", "") or "",
    )


def rank(state: dict) -> dict:
    sorted_items = sorted(state["normalized_items"], key=_sort_key)

    ranked = []
    for i, item in enumerate(sorted_items, start=1):
        ranked.append({**item, "score": i})

    state["ranked_items"] = ranked
    return state
