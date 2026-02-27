import json

from graph.v2 import llm


def test_generate_summary_uses_retry_hardening(monkeypatch):
    prompts = []
    calls = {"n": 0}

    def fake_call_ollama(prompt: str) -> str:
        prompts.append(prompt)
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return '{"summary":"ok"}'

    monkeypatch.setattr(llm, "call_ollama", fake_call_ollama)

    out = llm.generate_summary(
        {"title": "T", "abstract": "A", "link": "L", "source": "arxiv"}
    )

    assert out == {"summary": "ok"}
    assert calls["n"] == 2
    assert "The previous output was invalid." in prompts[1]
    assert "Return ONLY raw JSON." in prompts[1]


def test_generate_summary_returns_error_after_retries(monkeypatch):
    def always_fail(_prompt: str) -> str:
        raise RuntimeError("down")

    monkeypatch.setattr(llm, "call_ollama", always_fail)

    out = llm.generate_summary(
        {"title": "T", "abstract": "A", "link": "L", "source": "arxiv"}
    )
    assert "error" in out
    assert out["error"].startswith("LLM_CALL_FAILED:")


def test_call_ollama_sends_frozen_config(monkeypatch):
    captured = {}

    class DummyResp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"response":"{\\"summary\\":\\"ok\\"}"}'

    def fake_urlopen(req, timeout):
        captured["timeout"] = timeout
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return DummyResp()

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    raw = llm.call_ollama("prompt")
    assert raw == '{"summary":"ok"}'
    assert captured["timeout"] == llm.TIMEOUT_SECONDS
    assert captured["url"] == llm.OLLAMA_API_URL
    assert captured["method"] == "POST"
    assert captured["payload"]["model"] == llm.MODEL_NAME
    assert captured["payload"]["options"]["temperature"] == llm.TEMPERATURE
    assert captured["payload"]["options"]["num_predict"] == llm.MAX_TOKENS
