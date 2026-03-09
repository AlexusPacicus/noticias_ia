from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import graph.v2_1.graph_21 as g21
import graph.v2_1.summarize.graph_21 as summarize_graph_21
from graph.v2_1.retrieval.graph_21 import build_retrieval_graph
from graph.v2_1.summarize.graph_21 import build_summarize_graph


def _mock_summarize_ok(state):
    remove = set(state.get("hitl_remove_keys", []) or [])
    selected = state.get("selected_items", []) or []
    effective = [item for item in selected if item.get("canonical_id") not in remove]
    summary_items = [
        {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "summary": "ok",
            "link": item["link"],
            "source": item["source"],
        }
        for item in effective
    ]
    return {
        "summary_items": summary_items,
        "summary_stats": {"ok": len(summary_items), "failed": 0},
    }


def test_graph_21_invoke_writes_snapshot_json(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    nominal_arxiv_items,
    nominal_hf_items,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    monkeypatch.setattr(g21, "summarize_map_effective", _mock_summarize_ok)

    graph_21 = g21.build_graph_21(live=False)
    out = graph_21.invoke(payload_valid)

    assert "abort_reason" not in out
    assert "output" in out

    snapshot_path = Path("tests/artifacts/v2_1_graph_21_invoke_snapshot.json")
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(out, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    assert snapshot_path.exists()


def test_retrieval_graph_then_summarize_graph(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    patch_fetch_snapshot,
    nominal_arxiv_items,
    nominal_hf_items,
):
    patch_now_utc()
    patch_fetch_snapshot(arxiv_items=nominal_arxiv_items, hf_items=nominal_hf_items)
    monkeypatch.setattr(summarize_graph_21, "summarize_map", _mock_summarize_ok)

    retrieval_graph = build_retrieval_graph(live=False)
    summarize_graph = build_summarize_graph()

    retrieval_state = retrieval_graph.invoke(payload_valid)
    summarize_state = summarize_graph.invoke(deepcopy(retrieval_state))

    assert "abort_reason" not in retrieval_state
    assert "abort_reason" not in summarize_state
    assert "summary_items" in summarize_state
    assert "output" in summarize_state
    assert summarize_state["output"]["returned_k"] == len(summarize_state["summary_items"])
    assert summarize_state["selected_items"] == retrieval_state["selected_items"]
