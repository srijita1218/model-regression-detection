from backend.token_metrics import extract_token_metrics


response = {
    "prompt_eval_count": 100,
    "eval_count": 40,
}


metrics = extract_token_metrics(
    response
)


print(metrics)