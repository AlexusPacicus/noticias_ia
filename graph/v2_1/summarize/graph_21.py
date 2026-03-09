from __future__ import annotations

from graph.v2.nodes.summarize_reduce import summarize_reduce
from graph.v2_1.summarize.summarize_map import summarize_map

import graph.v2_1.runtime as _runtime


def _sync_runtime_symbols() -> None:
    _runtime.summarize_map = summarize_map
    _runtime.summarize_reduce = summarize_reduce


def build_summarize_graph():
    _sync_runtime_symbols()
    return _runtime.build_summarize_graph()
