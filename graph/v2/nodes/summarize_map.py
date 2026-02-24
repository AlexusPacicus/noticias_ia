from __future__ import annotations
from typing import Dict, Any, List


# Esta función será parcheada en tests
def generate_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    raise NotImplementedError


def summarize_map(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Contract v2 — summarize_map

    Reads:
        - selected_items

    Writes:
        - summary_items
        - summary_stats

    MUST NOT abort.
    MUST iterate in order of selected_items.
    MUST preserve rank_position.
    MUST return only delta.
    """

    selected_items: List[Dict[str, Any]] = state["selected_items"]

    summary_items: List[Dict[str, Any]] = []
    ok = 0
    failed = 0

    for item in selected_items:
        try:
            summary = generate_summary(item)

            # Hard structural validation mínima
            assert summary["rank_position"] == item["rank_position"]

            summary_items.append(summary)
            ok += 1

        except Exception:
            failed += 1

    summary_stats = {
        "ok": ok,
        "failed": failed,
    }

    # Invariante contractual fuerte
    assert ok + failed == len(selected_items)
    assert len(summary_items) == ok

    return {
        "summary_items": summary_items,
        "summary_stats": summary_stats,
    }