"""
Tests contractuales: fetch.
Ref: Contrato_Fetch.md

Tests marcados @pytest.mark.integration requieren conexión a arXiv.
"""

import pytest
from unittest.mock import patch, MagicMock

from graph.nodes.fetch import fetch


def _state(query="artificial intelligence", tw="last_7_days"):
    return {"input_validated": {"query": query, "time_window": tw, "top_k": 5}}


@pytest.mark.integration
class TestFetchIntegration:

    def test_happy_path(self):
        result = fetch(_state())
        assert isinstance(result["external_units"], list)
        if result["external_units"]:
            import xml.etree.ElementTree as ET
            assert isinstance(result["external_units"][0], ET.Element)


class TestFetchErrors:

    def test_source_error(self):
        with patch("graph.nodes.fetch.urllib.request.urlopen",
                    side_effect=Exception("connection refused")):
            with pytest.raises(ValueError, match="FETCH_SOURCE_ERROR"):
                fetch(_state())

    def test_not_iterable(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"this is not xml"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("graph.nodes.fetch.urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(ValueError, match="FETCH_NOT_ITERABLE"):
                fetch(_state())
