import pytest

# Esto DEBE fallar ahora (no existe todavía el nodo).
from graph.v2.nodes.select import select


def _mk_item(i: int) -> dict:
    return {"title": f"t{i}", "link": f"https://x/{i}", "bm25_score": 1.0, "rank_position": i}


def test_select_happy_path_prefix_exact():
    ranked = [_mk_item(i) for i in range(1, 6)]
    state = {
        "ranked_items": ranked,
        "input_validated": {"top_k": 3},
    }

    delta = select(state)
    assert "abort_reason" not in delta
    assert delta["selected_items"] == ranked[:3]          # prefijo exacto
    assert delta["selected_items"][0] is ranked[0]        # no copias raras


def test_select_topk_gt_len_no_abort():
    ranked = [_mk_item(i) for i in range(1, 4)]
    state = {
        "ranked_items": ranked,
        "input_validated": {"top_k": 5},
    }

    delta = select(state)
    assert "abort_reason" not in delta
    assert delta["selected_items"] == ranked[:]           # devuelve todo
    assert len(delta["selected_items"]) == 3


def test_select_ranked_items_empty_ok():
    state = {
        "ranked_items": [],
        "input_validated": {"top_k": 3},
    }
    delta = select(state)
    assert "abort_reason" not in delta
    assert delta["selected_items"] == []


def test_select_missing_ranked_items_abort():
    state = {"input_validated": {"top_k": 3}}
    delta = select(state)
    assert delta == {"abort_reason": "SELECT_MISSING_RANKED_ITEMS"}


@pytest.mark.parametrize("bad_top_k", [None, "3", 0, 6, -1, 2.5])
def test_select_topk_invalid_abort(bad_top_k):
    state = {
        "ranked_items": [_mk_item(1)],
        "input_validated": {"top_k": bad_top_k},
    }
    delta = select(state)
    assert delta == {"abort_reason": "SELECT_TOPK_INVALID"}


def test_select_does_not_modify_ranked_items():
    ranked = [_mk_item(i) for i in range(1, 4)]
    snapshot = list(ranked)
    state = {"ranked_items": ranked, "input_validated": {"top_k": 2}}

    delta = select(state)
    assert ranked == snapshot
    assert delta["selected_items"] == ranked[:2]