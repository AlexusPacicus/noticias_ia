from __future__ import annotations

import re
from typing import Any, Dict

from runtime.llm_client import LLMClient, LLMEmptyResponse, LLMError, LLMTimeout
from runtime.parse_llm_output import ParseError, parse_llm_output


def _sanitize_fallback_summary(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""

    text = text.replace("```json", "").replace("```", "").strip()
    text = re.sub(r"^\s*here'?s a summary of the query:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*summary\s*:\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


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
        abstract = item.get("abstract") or item.get("content")
        if not isinstance(abstract, str) or not abstract.strip():
            failed += 1
            continue

        llm_input = {
            "title": item["title"],
            "abstract": abstract,
            "query": query,
        }

        try:
            raw = llm.generate(**llm_input)
        except (LLMTimeout, LLMError, LLMEmptyResponse) as exc:
            failed += 1
            continue

        try:
            parsed = parse_llm_output(raw)
            summary_text = parsed.summary
        except ParseError:
            summary_text = _sanitize_fallback_summary(raw)
            if not summary_text:
                failed += 1
                continue

        summary_items.append(
            {
                "rank_position": item["rank_position"],
                "title": item["title"],
                "summary": summary_text,
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
