#the LLM is mocked, so no Ollama is needed
import json
from pathlib import Path

import pytest

from backend import classifier

PROMPT_PATH = str(Path(__file__).resolve().parent.parent / "prompts" / "v1.yaml")


def fake_llm(payload: str, captured: list | None = None):
    def _generate(prompt: str) -> dict:
        if captured is not None:
            captured.append(prompt)
        return {"response": payload, "prompt_eval_count": 10, "eval_count": 5}
    return _generate


def test_classify_returns_result_and_raw_response(monkeypatch):
    payload = json.dumps({"category": "billing", "summary": "Customer was charged twice."})
    monkeypatch.setattr(classifier, "generate", fake_llm(payload))

    result, raw = classifier.classify("I was charged twice", PROMPT_PATH)

    assert result.category == "billing"
    assert result.summary == "Customer was charged twice."
    assert raw["prompt_eval_count"] == 10  # token metadata survives


def test_email_is_injected_into_prompt(monkeypatch):
    captured = []
    payload = json.dumps({"category": "general", "summary": "x"})
    monkeypatch.setattr(classifier, "generate", fake_llm(payload, captured))

    classifier.classify("UNIQUE-EMAIL-TEXT-123", PROMPT_PATH)

    assert "UNIQUE-EMAIL-TEXT-123" in captured[0]
    assert "{{email}}" not in captured[0]


def test_invalid_json_raises_clear_valueerror(monkeypatch):
    monkeypatch.setattr(classifier, "generate", fake_llm("this is not json"))
    with pytest.raises(ValueError, match="invalid JSON"):
        classifier.classify("hello", PROMPT_PATH)


def test_valid_json_wrong_shape_raises_valueerror(monkeypatch):
    monkeypatch.setattr(classifier, "generate", fake_llm('{"foo": "bar"}'))
    with pytest.raises(ValueError, match="missing required fields"):
        classifier.classify("hello", PROMPT_PATH)


def test_load_prompt_reads_real_config():
    cfg = classifier.load_prompt(PROMPT_PATH)
    assert "{{email}}" in cfg.user_prompt