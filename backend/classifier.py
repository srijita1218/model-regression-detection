import json
from pathlib import Path
from pydantic import ValidationError

import yaml

from backend.llm_client import generate
from backend.models import ClassificationResult


def load_prompt(prompt_path: str) -> PromptConfig:
    with open(prompt_path, "r", encoding="utf-8") as file:
        raw = yaml.safe_load(file)
    return PromptConfig(**raw)


def classify(
    email: str,
    prompt_path: str,
) -> tuple[ClassificationResult, dict]:

    prompt_config = load_prompt(prompt_path)

    system_prompt = prompt_config.system_prompt

    user_prompt = prompt_config.user_prompt.replace(
        "{{email}}",
        email,
    )

    full_prompt = f"""
{system_prompt}

{user_prompt}
"""

    llm_response = generate(full_prompt)

    raw_response = llm_response["response"]

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"LLM returned invalid JSON:\n{raw_response}"
        ) from error

    try:
        classification = ClassificationResult(**result)
    except ValidationError as error:
        raise ValueError(
            f"LLM response missing required fields (category/summary):\n{raw_response}"
        ) from error

    return classification, llm_response