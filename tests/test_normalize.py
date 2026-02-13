"""
Tests contractuales: normalize.
Ref: Contrato_Normalize.md
"""

import pytest

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
        with pytest.raises(ValueError, match="NORMALIZE_MISSING_TITLE"):
            normalize({"external_units": [ARXIV_ENTRY_NO_TITLE]})

    def test_atomicity_on_failure(self):
        state = {"external_units": [ARXIV_ENTRY_VALID_1, ARXIV_ENTRY_NO_TITLE]}
        with pytest.raises(ValueError):
            normalize(state)
        assert "normalized_items" not in state
