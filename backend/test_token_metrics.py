from backend.token_metrics import extract_token_metrics


def test_extracts_and_sums_tokens():
    out = extract_token_metrics({"prompt_eval_count": 120, "eval_count": 30})
    assert out == {"prompt_tokens": 120, "generated_tokens": 30, "total_tokens": 150}


def test_missing_keys_default_to_zero():
    out = extract_token_metrics({"response": "hi"})
    assert out == {"prompt_tokens": 0, "generated_tokens": 0, "total_tokens": 0}