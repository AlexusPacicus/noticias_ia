from __future__ import annotations

from typing import Iterable

from graph.v2.nodes.collect_input import collect_input
from graph.v2.nodes.dedupe import dedupe
from graph.v2.nodes.fetch_arxiv import fetch_arxiv
from graph.v2.nodes.fetch_huggingface import fetch_huggingface
from graph.v2.nodes.fetch_router import fetch_router
from graph.v2.nodes.filter_by_time_window import filter_by_time_window
from graph.v2.nodes.merge_source_units import merge_source_units
from graph.v2.nodes.normalize import normalize
from graph.v2.nodes.rank_bm25 import rank_bm25
from graph.v2.nodes.select import select
from graph.v2.nodes.validate_input import validate_input

import graph.v2_1.runtime as _runtime


def _sync_runtime_symbols() -> None:
    _runtime.collect_input = collect_input
    _runtime.validate_input = validate_input
    _runtime.fetch_router = fetch_router
    _runtime.fetch_arxiv = fetch_arxiv
    _runtime.fetch_huggingface = fetch_huggingface
    _runtime.merge_source_units = merge_source_units
    _runtime.normalize = normalize
    _runtime.filter_by_time_window = filter_by_time_window
    _runtime.dedupe = dedupe
    _runtime.rank_bm25 = rank_bm25
    _runtime.select = select


def build_retrieval_graph(live: bool = False, sources: Iterable[str] | None = None):
    _sync_runtime_symbols()
    return _runtime.build_retrieval_graph(live=live, sources=sources)
