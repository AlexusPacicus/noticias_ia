import pytest
from graph.v2.nodes.normalize import _generate_canonical_id


def test_arxiv_removes_version():
    link = "https://arxiv.org/abs/1234.0001v2"
    assert _generate_canonical_id(link) == "arxiv:1234.0001"


def test_arxiv_pdf_url():
    link = "https://arxiv.org/pdf/1234.0001v3.pdf"
    assert _generate_canonical_id(link) == "arxiv:1234.0001"


def test_url_removes_utm_params():
    link = "https://huggingface.co/paper/0001?utm_source=twitter&utm_campaign=test"
    assert _generate_canonical_id(link) == "url:https://huggingface.co/paper/0001"


def test_url_trailing_slash_removed():
    link = "https://huggingface.co/paper/0001/"
    assert _generate_canonical_id(link) == "url:https://huggingface.co/paper/0001"


def test_url_keeps_non_utm_params():
    link = "https://example.com/page?id=123&utm_source=twitter"
    assert _generate_canonical_id(link) == "url:https://example.com/page?id=123"


def test_idempotent():
    link = "https://arxiv.org/abs/1234.0001v5"
    first = _generate_canonical_id(link)
    second = _generate_canonical_id(link)
    assert first == second