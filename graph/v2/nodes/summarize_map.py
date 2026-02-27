from __future__ import annotations
from typing import Dict, Any, List
import logging
from graph.v2.llm import generate_summary as llm_generate_summary

# Nodo summarize_map - Responsabilidad: resumir secuencialmente selected_items y acumular summary_stats.

logger = logging.getLogger(__name__)


def generate_summary(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adapter kept as a module symbol so tests can monkeypatch this call site.
    """
    return llm_generate_summary(item)


def _extract_summary_text(result: Dict[str, Any]) -> str:
    if not isinstance(result, dict):
        raise ValueError("Invalid summary payload type")

    summary = result.get("summary")
    if isinstance(summary, str) and summary.strip():
        return summary.strip()

    raise ValueError("Invalid summary value")


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

    summary_items = []
    ok = 0
    failed = 0

    for item in selected_items:
        try:
            llm_input = {
                "title": item["title"],
                # Selected items come from ranked_items (field: content).
                "abstract": item.get("abstract") or item.get("content", ""),
                "link": item["link"],
                "source": item["source"],
            }
            result = generate_summary(llm_input)
            if isinstance(result, dict) and result.get("mode") in {"fallback_text", "fallback_json_recovery"}:
                logger.info(
                    "Using %s summary for rank_position=%s",
                    result.get("mode"),
                    item.get("rank_position"),
                )
            summary_text = _extract_summary_text(result)

            summary_items.append({
                "rank_position": item["rank_position"],
                "title": item["title"],
                "link": item["link"],
                "source": item["source"],
                "summary": summary_text
            })

            ok += 1

        except Exception as exc:
            logger.warning(
                "summary generation failed for rank_position=%s source=%s title=%r: %s",
                item.get("rank_position"),
                item.get("source"),
                (item.get("title") or "")[:120],
                exc,
                exc_info=True,
            )
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
        "summary_stats": {
            "ok": ok,
            "failed": failed
        }
    }
