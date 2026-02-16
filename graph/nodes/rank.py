from __future__ import annotations

import re

from graph.state import PipelineState


def _tokenize(text: str) -> set[str]:
    """Normalizacion textual contractual: lowercase, no [a-z0-9] -> espacio, split, set."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", " ", text)
    return set(t for t in text.split() if t)


def rank(state: PipelineState) -> dict:
    """Ordena normalized_items por coincidencia lexica con query.

    Retorna ranked_items o abort_reason.
    """
    normalized_items = state["normalized_items"]
    query = state["input_validated"]["query"]

    Q = _tokenize(query)
    if not Q:
        return {"abort_reason": "RANK_QUERY_EMPTY_AFTER_NORMALIZATION"}

    if not normalized_items:
        return {"ranked_items": []}

    def sort_key(item: dict) -> tuple:
        T = _tokenize(item["title"] + " " + item["content"])
        score = len(Q & T)
        return (-score, item["title"], item["link"])

    return {"ranked_items": sorted(normalized_items, key=sort_key)}
