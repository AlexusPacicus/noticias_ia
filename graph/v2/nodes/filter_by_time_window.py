from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from graph.v2.state import V2State


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


_WINDOW_TO_DELTA = {
    "last_24h": timedelta(hours=24),
    "last_3_days": timedelta(days=3),
    "last_7_days": timedelta(days=7),
}


def _parse_iso_utc(ts: str) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts.strip():
        return None
    s = ts.strip()
    # Support "Z"
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    # Ensure tz-aware UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)
    return dt


def filter_by_time_window(state: V2State) -> Dict[str, Any]:
    """
    Contract:
    - Reads: normalized_items, input_validated.time_window
    - Writes: filtered_items OR abort_reason
    - MUST compute now_utc exactly once
    - MUST be inclusive: published_at >= cutoff
    - MUST discard invalid published_at (no abort for invalid date alone)
    - MUST preserve order
    - MUST return delta only
    """
    items = state.get("normalized_items", []) or []
    tw = (state.get("input_validated", {}) or {}).get("time_window")

    delta = _WINDOW_TO_DELTA.get(tw)
    # time_window should be validated earlier; if not, treat as no items (safe fail)
    if delta is None:
        return {"abort_reason": "NO_ITEMS_IN_TIME_WINDOW"}

    now_utc = _now_utc()
    cutoff = now_utc - delta

    filtered: List[Dict[str, Any]] = []
    for it in items:
        dt = _parse_iso_utc(it.get("published_at")) if isinstance(it, dict) else None
        if dt is None:
            continue
        if dt >= cutoff:  # inclusive
            filtered.append(it)

    if len(filtered) == 0:
        return {"abort_reason": "NO_ITEMS_IN_TIME_WINDOW"}

    return {"filtered_items": filtered}