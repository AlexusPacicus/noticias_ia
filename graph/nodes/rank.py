import re


def _tokenize(text):
    """Normalización textual contractual: lowercase, no [a-z0-9] → espacio, split, set."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]", " ", text)
    return set(t for t in text.split() if t)


def rank(state: dict) -> dict:
    normalized_items = state["normalized_items"]
    query = state["input_validated"]["query"]

    Q = _tokenize(query)
    if not Q:
        raise ValueError("RANK_QUERY_EMPTY_AFTER_NORMALIZATION")

    if not normalized_items:
        state["ranked_items"] = []
        return state

    def sort_key(item):
        T = _tokenize(item["title"] + " " + item["content"])
        score = len(Q & T)
        return (-score, item["title"], item["link"])

    state["ranked_items"] = sorted(normalized_items, key=sort_key)
    return state
