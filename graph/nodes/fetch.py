_DUMMY_ITEMS = [
    {
        "kind": "paper",
        "title": "Attention Is All You Need",
        "source": "arXiv",
        "link": "https://arxiv.org/abs/1706.03762",
    },
    {
        "kind": "release",
        "title": "GPT-4o mini",
        "source": "OpenAI",
        "link": "https://openai.com/index/gpt-4o-mini",
    },
    {
        "kind": "news",
        "title": "Google announces Gemini 2",
        "source": "Google",
        "link": "https://blog.google/gemini-2",
    },
]


def fetch(state: dict) -> dict:
    _ = state["input"]
    state["items"] = list(_DUMMY_ITEMS)
    return state
