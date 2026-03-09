from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from typing import Any, Dict, List

from graph.v2.nodes.summarize_reduce import summarize_reduce


def _load_summarize_map_module():
    runtime_types = types.ModuleType("runtime.types")

    @dataclass
    class LLMOutput:
        summary: str

    runtime_types.LLMOutput = LLMOutput
    sys.modules["runtime.types"] = runtime_types
    return importlib.import_module("graph.v2_1.summarize.summarize_map")


def _base_state(selected_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "selected_items": selected_items,
        "input_validated": {
            "query": "agentic ai",
            "time_window": "last_7_days",
            "top_k": len(selected_items),
        },
    }


def _to_reduce_state(state: Dict[str, Any], map_delta: Dict[str, Any]) -> Dict[str, Any]:
    raw_items = map_delta["summary_items"]
    ok_items = [
        {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "link": item["link"],
            "source": item["source"],
            "summary": item["summary"],
        }
        for item in raw_items
    ]
    summary_stats = {
        "ok": int(map_delta["summary_stats"]["ok"]),
        "failed": int(map_delta["summary_stats"]["failed"]),
    }

    return {
        **state,
        "summary_items": ok_items,
        "summary_stats": summary_stats,
    }


def test_summarize_success(monkeypatch):
    summarize_map_module = _load_summarize_map_module()

    def fake_generate(self, **kwargs):
        return '{"summary": "test summary"}'

    monkeypatch.setattr(summarize_map_module.LLMClient, "generate", fake_generate)

    state = _base_state(
        [
            {
                "canonical_id": "a",
                "rank_position": 1,
                "title": "Paper A",
                "abstract": "Abstract A",
                "link": "https://a",
                "source": "arxiv",
            },
            {
                "canonical_id": "b",
                "rank_position": 2,
                "title": "Paper B",
                "abstract": "Abstract B",
                "link": "https://b",
                "source": "arxiv",
            },
        ]
    )

    map_delta = summarize_map_module.summarize_map(state)
    reduce_state = _to_reduce_state(state, map_delta)
    reduce_delta = summarize_reduce(reduce_state)

    assert reduce_state["summary_stats"]["ok"] == 2
    assert reduce_state["summary_stats"]["failed"] == 0
    assert len(reduce_delta["output"]["results"]) == 2


def test_parse_error(monkeypatch):
    summarize_map_module = _load_summarize_map_module()

    def fake_generate(self, **kwargs):
        return "not-json"

    monkeypatch.setattr(summarize_map_module.LLMClient, "generate", fake_generate)

    state = _base_state(
        [
            {
                "canonical_id": "a",
                "rank_position": 1,
                "title": "Paper A",
                "abstract": "Abstract A",
                "link": "https://a",
                "source": "arxiv",
            }
        ]
    )

    map_delta = summarize_map_module.summarize_map(state)
    reduce_state = _to_reduce_state(state, map_delta)
    reduce_delta = summarize_reduce(reduce_state)

    assert reduce_state["summary_stats"]["ok"] == 0
    assert reduce_state["summary_stats"]["failed"] == 1
    assert reduce_delta["abort_reason"] == "SUMMARY_ALL_ITEMS_FAILED"


def test_rank_order(monkeypatch):
    summarize_map_module = _load_summarize_map_module()

    def fake_generate(self, **kwargs):
        return '{"summary": "test summary"}'

    monkeypatch.setattr(summarize_map_module.LLMClient, "generate", fake_generate)

    state = _base_state(
        [
            {
                "canonical_id": "a",
                "rank_position": 3,
                "title": "Paper 3",
                "abstract": "Abstract 3",
                "link": "https://3",
                "source": "arxiv",
            },
            {
                "canonical_id": "b",
                "rank_position": 1,
                "title": "Paper 1",
                "abstract": "Abstract 1",
                "link": "https://1",
                "source": "arxiv",
            },
            {
                "canonical_id": "c",
                "rank_position": 2,
                "title": "Paper 2",
                "abstract": "Abstract 2",
                "link": "https://2",
                "source": "arxiv",
            },
        ]
    )

    map_delta = summarize_map_module.summarize_map(state)
    reduce_state = _to_reduce_state(state, map_delta)
    reduce_delta = summarize_reduce(reduce_state)

    ranks = [item["rank_position"] for item in reduce_delta["output"]["results"]]
    assert ranks == [1, 2, 3]
