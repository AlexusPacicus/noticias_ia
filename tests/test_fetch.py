"""
Tests contractuales: fetch.
Ref: docs/v1.1/Contrato_Sistema_v1.1.md

Tests marcados @pytest.mark.integration requieren conexion a arXiv.
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
        units = result["external_units"]
        assert isinstance(units, list)
        if units:
            assert isinstance(units[0], dict)
            assert "title" in units[0]
            assert "id" in units[0]
            assert "summary" in units[0]


class TestFetchErrors:

    def test_source_error(self):
        with patch("graph.nodes.fetch.urllib.request.urlopen",
                    side_effect=Exception("connection refused")):
            result = fetch(_state())
        assert result["abort_reason"] == "FETCH_SOURCE_ERROR"

    def test_not_iterable(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"this is not xml"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("graph.nodes.fetch.urllib.request.urlopen", return_value=mock_resp):
            result = fetch(_state())
        assert result["abort_reason"] == "FETCH_NOT_ITERABLE"
