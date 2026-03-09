from __future__ import annotations

from typing import Any, Dict

from runtime.llm_client import LLMClient
from runtime.parse_llm_output import ParseError, parse_llm_output


def summarize_map(state: Dict[str, Any]) -> Dict[str, Any]:
    selected_items = state["selected_items"]
    remove_keys = state.get("hitl_remove_keys", [])
    query = state["input_validated"]["query"]

    effective_items = [
        item for item in selected_items
        if item["canonical_id"] not in remove_keys
    ]

    if not effective_items:
        return {"abort_reason": "SUMMARY_EMPTY_INPUT"}

    llm = LLMClient()
    summary_items = []
    ok = 0
    failed = 0
    for item in effective_items:
        llm_input = {
            "title": item["title"],
            "abstract": item["abstract"],
            "query": query,
        }
        raw = llm.generate(**llm_input)
        try:
            parsed = parse_llm_output(raw)
        except ParseError:
            failed += 1
            continue

        summary_items.append(
            {
                "rank_position": item["rank_position"],
                "title": item["title"],
                "summary": parsed.summary,
                "link": item["link"],
                "source": item["source"],
            }
        )
        ok += 1

    return {
        "summary_items": summary_items,
        "summary_stats": {
            "ok": ok,
            "failed": failed,
        },
    }
