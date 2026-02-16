from __future__ import annotations

from graph.state import PipelineState


def normalize(state: PipelineState) -> dict:
    """Mapea external_units (dicts) a normalized_items con schema minimo cerrado.

    Retorna normalized_items o abort_reason.
    """
    external_units = state["external_units"]

    if not external_units:
        return {"normalized_items": []}

    normalized = []
    for unit in external_units:
        title = unit.get("title")
        link = unit.get("id")
        content = unit.get("summary")

        if not isinstance(title, str) or not title.strip():
            return {"abort_reason": "NORMALIZE_MISSING_TITLE"}
        if not isinstance(link, str) or not link.strip():
            return {"abort_reason": "NORMALIZE_MISSING_LINK"}
        if not isinstance(content, str) or not content.strip():
            return {"abort_reason": "NORMALIZE_MISSING_CONTENT"}

        normalized.append({
            "title": title.strip(),
            "link": link.strip(),
            "content": content.strip(),
        })

    return {"normalized_items": normalized}
