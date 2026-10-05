import json

from backend.models import EvaluationCase


def load_dataset(path: str) -> list[EvaluationCase]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return [
        EvaluationCase(**case)
        for case in data
    ]