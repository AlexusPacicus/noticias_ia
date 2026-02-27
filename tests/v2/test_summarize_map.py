from graph.v2.nodes.summarize_map import summarize_map


def fake_llm_ok(_item):
    return {"summary": "x"}


def fake_llm_fail(_item):
    raise ValueError("LLM error")


def test_summarize_map_happy_path(monkeypatch):
    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
        {"rank_position": 2, "title": "B", "link": "l2", "source": "hf"},
        {"rank_position": 3, "title": "C", "link": "l3", "source": "hf"},
    ]

    calls = [fake_llm_ok, fake_llm_ok, fake_llm_fail]

    def dispatcher(item):
        fn = calls.pop(0)
        return fn(item)

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        dispatcher,
    )

    delta = summarize_map({"selected_items": selected_items})

    assert "summary_items" in delta
    assert "summary_stats" in delta
    assert delta["summary_stats"]["ok"] == 2
    assert delta["summary_stats"]["failed"] == 1
    assert len(delta["summary_items"]) == 2
    assert all(set(item.keys()) == {"rank_position", "title", "link", "source", "summary"}
               for item in delta["summary_items"])


def test_summarize_map_no_abort_on_all_fail(monkeypatch):
    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
    ]

    def always_fail(_item):
        raise RuntimeError()

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        always_fail,
    )

    delta = summarize_map({"selected_items": selected_items})

    assert "abort_reason" not in delta
    assert delta["summary_stats"]["ok"] == 0
    assert delta["summary_stats"]["failed"] == 1
    assert delta["summary_items"] == []


def test_summarize_map_preserves_rank_position(monkeypatch):
    selected_items = [
        {"rank_position": 5, "title": "A", "link": "l1", "source": "arxiv"},
    ]

    def ok(_item):
        return {"summary": "x"}

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        ok,
    )

    delta = summarize_map({"selected_items": selected_items})

    assert delta["summary_items"][0]["rank_position"] == 5


def test_summarize_map_invariant(monkeypatch):
    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
        {"rank_position": 2, "title": "B", "link": "l2", "source": "hf"},
    ]

    def ok(_item):
        return {"summary": "x"}

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        ok,
    )

    delta = summarize_map({"selected_items": selected_items})
    stats = delta["summary_stats"]

    assert stats["ok"] + stats["failed"] == len(selected_items)
    assert len(delta["summary_items"]) == stats["ok"]


def test_summarize_map_rejects_legacy_schema(monkeypatch):
    selected_items = [
        {"rank_position": 1, "title": "A", "link": "l1", "source": "arxiv"},
    ]

    def legacy_shape(_item):
        return {
            "idea_clave": "x",
            "relacion_con_query": "y",
        }

    monkeypatch.setattr(
        "graph.v2.nodes.summarize_map.generate_summary",
        legacy_shape,
    )

    delta = summarize_map({"selected_items": selected_items})
    assert delta["summary_stats"] == {"ok": 0, "failed": 1}
    assert delta["summary_items"] == []
