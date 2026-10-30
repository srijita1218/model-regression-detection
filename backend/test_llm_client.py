import pytest
import requests

from backend import llm_client


class FakeResponse:
    def __init__(self, data, fail=False):
        self._data, self._fail = data, fail

    def raise_for_status(self):
        if self._fail:
            raise requests.HTTPError("500")

    def json(self):
        return self._data


def test_generate_posts_expected_payload_and_returns_json(monkeypatch):
    seen = {}

    def fake_post(url, json, timeout):
        seen.update(url=url, json=json, timeout=timeout)
        return FakeResponse({"response": "ok", "eval_count": 3})

    monkeypatch.setattr(llm_client.requests, "post", fake_post)

    out = llm_client.generate("hello")

    assert out == {"response": "ok", "eval_count": 3}
    assert seen["url"] == llm_client.OLLAMA_URL
    assert seen["json"]["model"] == llm_client.MODEL_NAME
    assert seen["json"]["prompt"] == "hello"
    assert seen["json"]["stream"] is False


def test_generate_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(
        llm_client.requests, "post", lambda *a, **k: FakeResponse({}, fail=True)
    )
    with pytest.raises(requests.HTTPError):
        llm_client.generate("hello")

def test_generate_is_deterministic_and_json_formatted(monkeypatch):
    seen = {}

    def fake_post(url, json, timeout):
        seen.update(json=json)
        return FakeResponse({"response": "{}"})

    monkeypatch.setattr(llm_client.requests, "post", fake_post)
    llm_client.generate("hello")

    assert seen["json"]["options"]["temperature"] == 0
    assert seen["json"]["options"]["seed"] == llm_client.SEED
    assert seen["json"]["format"] == "json"
    assert seen["json"]["keep_alive"]

#Later in M8, add assertions here for temperature == 0, the fixed seed and format == "json", so determinism is locked in by a test.       