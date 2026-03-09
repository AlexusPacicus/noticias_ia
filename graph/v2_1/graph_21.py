from __future__ import annotations

from typing import Any, Dict, Iterable

from graph.v2.nodes.fetch_arxiv import fetch_arxiv
from graph.v2.nodes.fetch_huggingface import fetch_huggingface
from graph.v2_1.hitl.graph_21 import hitl_review
from graph.v2_1.summarize.summarize_map import summarize_map as summarize_map_effective

from . import runtime as _runtime


def _extract_execute_until(config: Dict[str, Any] | None) -> str:
    if not config:
        return "summary"

    execute_until = config.get("execute_until")
    if execute_until is None:
        configurable = config.get("configurable")
        if isinstance(configurable, dict):
            execute_until = configurable.get("execute_until")

    if execute_until is None:
        return "summary"
    if execute_until not in {"select", "summary"}:
        raise ValueError("execute_until must be 'select' or 'summary'")
    return execute_until


class _RuntimeGraph21:
    def __init__(
        self,
        *,
        live: bool = False,
        sources: Iterable[str] | None = None,
        decision_provider=None,
    ):
        _sync_runtime_symbols()
        self._retrieval_graph = _runtime.build_retrieval_graph(live=live, sources=sources)
        self._full_graph = _runtime.build_graph(
            live=live,
            sources=sources,
            decision_provider=decision_provider,
        )

    def invoke(self, payload: Dict[str, Any], config: Dict[str, Any] | None = None):
        execute_until = _extract_execute_until(config)
        if execute_until == "select":
            return self._retrieval_graph.invoke(payload, config=config)
        return self._full_graph.invoke(payload, config=config)


def build_graph_21(
    *,
    live: bool = False,
    sources: Iterable[str] | None = None,
    decision_provider=None,
    ):
    return _RuntimeGraph21(
        live=live,
        sources=sources,
        decision_provider=decision_provider,
    )


def apply_hitl_decision(_state: Dict[str, Any]) -> Dict[str, Any]:
    # Legacy compatibility symbol kept for test monkeypatching.
    return {}


def _sync_runtime_symbols() -> None:
    _runtime.fetch_arxiv = fetch_arxiv
    _runtime.fetch_huggingface = fetch_huggingface
    _runtime.hitl_review = hitl_review
    _runtime.summarize_map = summarize_map_effective


graph = build_graph_21()


def run(
    payload: Dict[str, Any],
    *,
    execute_until: str = "summary",
    live: bool = False,
    sources: Iterable[str] | None = None,
    decision_provider=None,
):
    app = build_graph_21(
        live=live,
        sources=sources,
        decision_provider=decision_provider,
    )
    return app.invoke(payload, config={"execute_until": execute_until})
