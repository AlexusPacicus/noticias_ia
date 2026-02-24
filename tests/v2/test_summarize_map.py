import pytest
from graph.v2.nodes.summarize_map import summarize_map


def fake_llm_ok(item):
    return {
        "rank_position": item["rank_position"],
        "title": item["title"],
        "idea_clave": "x",
        "relacion_con_query": "y",
        "link": item["link"],
        "source": item["source"],
    }


def fake_llm_fail(item):
    raise ValueError("LLM error")


def test_summarize_map_happy_path(monkeypatch):

    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
        {"rank_position": 2, "title": "B", "link": "l2", "source": "hf"},
        {"rank_position": 3, "title": "C", "link": "l3", "source": "hf"},
    ]

    # 2 ok, 1 fail
    calls = [fake_llm_ok, fake_llm_ok, fake_llm_fail]

    def dispatcher(item):
        fn = calls.pop(0)
        return fn(item)

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        dispatcher
    )

    state = {"selected_items": selected_items}

    delta = summarize_map(state)

    assert "summary_items" in delta
    assert "summary_stats" in delta

    assert delta["summary_stats"]["ok"] == 2
    assert delta["summary_stats"]["failed"] == 1
    assert len(delta["summary_items"]) == 2

def test_summarize_map_no_abort_on_all_fail(monkeypatch):

    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
    ]

    def always_fail(item):
        raise RuntimeError()

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        always_fail
    )

    state = {"selected_items": selected_items}

    delta = summarize_map(state)

    assert "abort_reason" not in delta
    assert delta["summary_stats"]["ok"] == 0
    assert delta["summary_stats"]["failed"] == 1
    assert delta["summary_items"] == []

def test_summarize_map_no_abort_on_all_fail(monkeypatch):

    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
    ]

    def always_fail(item):
        raise RuntimeError()

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        always_fail
    )

    state = {"selected_items": selected_items}

    delta = summarize_map(state)

    assert "abort_reason" not in delta
    assert delta["summary_stats"]["ok"] == 0
    assert delta["summary_stats"]["failed"] == 1
    assert delta["summary_items"] == []

def test_summarize_map_preserves_rank_position(monkeypatch):

    selected_items = [
        {"rank_position": 5, "title": "A", "link": "l1", "source": "arxiv"},
    ]

    def ok(item):
        return {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "idea_clave": "x",
            "relacion_con_query": "y",
            "link": item["link"],
            "source": item["source"],
        }

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        ok
    )

    delta = summarize_map({"selected_items": selected_items})

    assert delta["summary_items"][0]["rank_position"] == 5

def test_summarize_map_invariant(monkeypatch):

    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
        {"rank_position": 2, "title": "B", "link": "l2", "source": "hf"},
    ]

    def ok(item):
        return {
            "rank_position": item["rank_position"],
            "title": item["title"],
            "idea_clave": "x",
            "relacion_con_query": "y",
            "link": item["link"],
            "source": item["source"],
        }

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        ok
    )

    delta = summarize_map({"selected_items": selected_items})

    stats = delta["summary_stats"]

    assert stats["ok"] + stats["failed"] == len(selected_items)
    assert len(delta["summary_items"]) == stats["ok"]