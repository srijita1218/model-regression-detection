def extract_token_metrics(
    llm_response: dict,
) -> dict:

    prompt_tokens = llm_response.get(
        "prompt_eval_count",
        0,
    )

    generated_tokens = llm_response.get(
        "eval_count",
        0,
    )

    total_tokens = (
        prompt_tokens
        + generated_tokens
    )

    return {
        "prompt_tokens": prompt_tokens,
        "generated_tokens": generated_tokens,
        "total_tokens": total_tokens,
    }