def dedupe(state: dict) -> dict:
    items = state.get("filtered_items")

    seen = set()
    deduped = []

    for item in items:
        cid = item["canonical_id"]
        if cid not in seen:
            seen.add(cid)
            deduped.append(item)

    if not deduped:
        return {"abort_reason": "NO_ITEMS_AFTER_DEDUPE"}

    return {"deduped_items": deduped}