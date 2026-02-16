"""
Fixtures y datos compartidos para tests contractuales v1.1.
"""

# ── Sample arXiv entries como dicts serializables ─────────────────────

ARXIV_ENTRY_VALID_1 = {
    "title": "Test Paper on Machine Learning",
    "id": "http://arxiv.org/abs/2401.00001v1",
    "summary": (
        "This paper presents a new approach to machine learning "
        "using neural networks and transformers."
    ),
    "published": "2025-02-10T00:00:00Z",
}

ARXIV_ENTRY_NO_TITLE = {
    "id": "http://arxiv.org/abs/2401.00004v1",
    "summary": "This entry has no title element.",
    "published": "2025-02-07T00:00:00Z",
}
