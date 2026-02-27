import math
import re
from collections import Counter


STOPWORDS = {
    "the", "and", "of", "in", "on", "for", "to", "a", "an"
}


def _preprocess(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS]
    return tokens


def rank_bm25(state: dict) -> dict:
    query = state["input_validated"]["query"]
    items = state["deduped_items"]

    query_tokens = _preprocess(query)

    if not query_tokens:
        return {"abort_reason": "RANK_QUERY_EMPTY_AFTER_NORMALIZATION"}

    docs_tokens = []
    for item in items:
        doc_text = f"{item['title']} {item['content']}"
        docs_tokens.append(_preprocess(doc_text))

    N = len(docs_tokens)
    avgdl = sum(len(doc) for doc in docs_tokens) / N if N > 0 else 0

    # IDF
    df = Counter()
    for doc in docs_tokens:
        for token in set(doc):
            df[token] += 1

    idf = {}
    for token in df:
        idf[token] = math.log((N - df[token] + 0.5) / (df[token] + 0.5) + 1)

    k1 = 1.5
    b = 0.75

    ranked = []

    for idx, item in enumerate(items):
        score = 0.0
        doc = docs_tokens[idx]
        doc_len = len(doc)
        tf = Counter(doc)

        for token in query_tokens:
            if token in tf:
                numerator = tf[token] * (k1 + 1)
                denominator = tf[token] + k1 * (1 - b + b * (doc_len / avgdl))
                score += idf.get(token, 0) * (numerator / denominator)

        new_item = item.copy()
        new_item["bm25_score"] = score
        ranked.append(new_item)

    ranked.sort(key=lambda x: (-x["bm25_score"], x["title"], x["link"]))

    for i, item in enumerate(ranked, start=1):
        item["rank_position"] = i

    return {"ranked_items": ranked}
