from __future__ import annotations
from typing import Dict, Any, List

# Nodo summarize_reduce - Responsabilidad: aplicar gate final de summarize y construir output público.

_SUMMARY_ITEM_KEYS = {"rank_position", "title", "summary", "link", "source"}


def _assert_summary_items_schema(summary_items: List[Dict[str, Any]]) -> None:
    for item in summary_items:
        assert isinstance(item, dict), "Invalid summary item type"
        assert set(item.keys()) == _SUMMARY_ITEM_KEYS, "Invalid summary item keys"
        assert isinstance(item["summary"], str) and item["summary"].strip(), (
            "Invalid summary value"
        )


def summarize_reduce(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Contract v2 — summarize_reduce

    Reads:
        - summary_items
        - summary_stats
        - input_validated.*

    Writes:
        - output
        - abort_reason (gate)

    Abort:
        - SUMMARY_ALL_ITEMS_FAILED if summary_stats.ok == 0

    Invariants:
        - len(summary_items) == summary_stats.ok
    """

    summary_items: List[Dict[str, Any]] = state["summary_items"]
    summary_stats: Dict[str, int] = state["summary_stats"]
    input_validated: Dict[str, Any] = state["input_validated"]

    ok = summary_stats["ok"]
    failed = summary_stats["failed"]

    # ----------------------------------------
    # Structural invariant (hard failure)
    # ----------------------------------------
    assert len(summary_items) == ok, (
        "Invariant violation: len(summary_items) != summary_stats.ok"
    )
    _assert_summary_items_schema(summary_items)

    # ----------------------------------------
    # Abort gate
    # ----------------------------------------
    if ok == 0:
        return {
            "abort_reason": "SUMMARY_ALL_ITEMS_FAILED"
        }

    # ----------------------------------------
    # Deterministic ordering
    # ----------------------------------------
    ordered = sorted(
        summary_items,
        key=lambda x: x["rank_position"]
    )

    # ----------------------------------------
    # Build output
    # ----------------------------------------
    output = {
        "topic": input_validated["query"],
        "time_window": input_validated["time_window"],
        "requested_k": input_validated["top_k"],
        "returned_k": ok,
        "failed_summaries": failed,
        "results": ordered,
    }

    return {"output": output}
