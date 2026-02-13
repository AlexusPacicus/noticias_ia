_NS = {"atom": "http://www.w3.org/2005/Atom"}


def normalize(state: dict) -> dict:
    external_units = state["external_units"]

    if not external_units:
        state["normalized_items"] = []
        return state

    normalized = []
    for entry in external_units:
        title_el = entry.find("atom:title", _NS)
        id_el = entry.find("atom:id", _NS)
        summary_el = entry.find("atom:summary", _NS)

        title = title_el.text if title_el is not None else None
        link = id_el.text if id_el is not None else None
        content = summary_el.text if summary_el is not None else None

        if not isinstance(title, str) or not title.strip():
            raise ValueError("NORMALIZE_MISSING_TITLE")
        if not isinstance(link, str) or not link.strip():
            raise ValueError("NORMALIZE_MISSING_LINK")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("NORMALIZE_MISSING_CONTENT")

        normalized.append({
            "title": title.strip(),
            "link": link.strip(),
            "content": content.strip(),
        })

    state["normalized_items"] = normalized
    return state
