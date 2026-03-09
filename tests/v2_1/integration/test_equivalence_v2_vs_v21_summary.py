from __future__ import annotations

from typing import Any

from graph.v2.graph import build_graph
from graph.v2_1.graph_21 import build_graph_21


def _summarize_ok_from_selected(selected_items: list[dict[str, Any]]) -> dict[str, Any]:
    summary_items = [
        {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "summary": "ok",
            "link": item["link"],
            "source": item["source"],
        }
        for item in selected_items
    ]
    return {
        "summary_items": summary_items,
        "summary_stats": {"ok": len(summary_items), "failed": 0},
    }


def _effective_selected_items(state: dict[str, Any]) -> list[dict[str, Any]]:
    remove = set(state.get("hitl_remove_keys", []) or [])
    selected = state.get("selected_items", []) or []
    return [item for item in selected if item.get("canonical_id") not in remove]


def test_equivalence_v2_full_vs_v21_execute_until_summary(
    monkeypatch,
    payload_valid,
    patch_now_utc,
    nominal_arxiv_items,
    nominal_hf_items,
):
    patch_now_utc()

    def fixed_fetch_arxiv(_state):
        return {
            "source_units": {
                "arxiv": {
                    "status": "ok",
                    "error": None,
                    "items": nominal_arxiv_items,
                }
            }
        }

    def fixed_fetch_hf(_state):
        return {
            "source_units": {
                "huggingface": {
                    "status": "ok",
                    "error": None,
                    "items": nominal_hf_items,
                }
            }
        }

    def summarize_ok_v2(state):
        return _summarize_ok_from_selected(state.get("selected_items", []) or [])

    def summarize_ok_v21(state):
        effective = _effective_selected_items(state)
        return _summarize_ok_from_selected(effective)

    monkeypatch.setattr("graph.v2.graph.fetch_arxiv", fixed_fetch_arxiv)
    monkeypatch.setattr("graph.v2.graph.fetch_huggingface", fixed_fetch_hf)
    monkeypatch.setattr("graph.v2_1.graph_21.fetch_arxiv", fixed_fetch_arxiv)
    monkeypatch.setattr("graph.v2_1.graph_21.fetch_huggingface", fixed_fetch_hf)
    monkeypatch.setattr("graph.v2.graph.summarize_map", summarize_ok_v2)
    monkeypatch.setattr("graph.v2_1.graph_21.summarize_map_effective", summarize_ok_v21)

    state_v2 = build_graph(live=False).invoke(payload_valid)
    state_v21 = build_graph_21(live=False).invoke(
        payload_valid,
        config={"execute_until": "summary"},
    )

    assert "abort_reason" not in state_v2
    assert "abort_reason" not in state_v21
    assert "output" in state_v2
    assert "output" in state_v21

    extra_v21 = set(state_v21.keys()) - set(state_v2.keys())
    missing_v21 = set(state_v2.keys()) - set(state_v21.keys())

    assert missing_v21 == set()
    assert extra_v21 == {"hitl_action", "hitl_remove_keys"}
    assert state_v21["hitl_action"] == "accept"
    assert state_v21["hitl_remove_keys"] == []

    for key in state_v2:
        assert state_v21[key] == state_v2[key]
