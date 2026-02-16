"""
Tests contractuales: normalize.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md
"""

from graph.nodes.normalize import normalize
from tests.conftest import (
    ARXIV_ENTRY_VALID_1,
    ARXIV_ENTRY_NO_TITLE,
)


class TestNormalize:

    def test_happy_path_maps_schema(self):
        result = normalize({"external_units": [ARXIV_ENTRY_VALID_1]})
        item = result["normalized_items"][0]
        assert set(item.keys()) == {"title", "link", "content"}
        assert item["title"] == "Test Paper on Machine Learning"
        assert item["link"] == "http://arxiv.org/abs/2401.00001v1"
        assert "machine learning" in item["content"].lower()

    def test_empty_produces_empty(self):
        result = normalize({"external_units": []})
        assert result["normalized_items"] == []

    def test_missing_field_aborts(self):
        result = normalize({"external_units": [ARXIV_ENTRY_NO_TITLE]})
        assert result["abort_reason"] == "NORMALIZE_MISSING_TITLE"

    def test_atomicity_on_failure(self):
        result = normalize({"external_units": [ARXIV_ENTRY_VALID_1, ARXIV_ENTRY_NO_TITLE]})
        assert "abort_reason" in result
        assert "normalized_items" not in result
