# Nodo dedupe - Responsabilidad: deduplicar por canonical_id preservando primer ocurrencia.

def dedupe(state: dict) -> dict:
    items = state.get("filtered_items") or []

    seen = set()
    deduped = []

    for item in items:
        cid = item["canonical_id"]
        if cid not in seen:
            seen.add(cid)
            deduped.append(item)

    if not deduped:
        return {
            "deduped_items": [],
            "abort_reason": "NO_ITEMS_AFTER_DEDUPE",
        }

    return {"deduped_items": deduped}
