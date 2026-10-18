import json

from backend.models import EvaluationCase

#golden dataset contains dataset version asw 

def load_dataset(path: str) -> tuple[list[EvaluationCase],str]:
    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    cases=[EvaluationCase(**case) for case in data["cases"]]

    return cases, data["dataset_version"] 