import json


WARNING_THRESHOLD = 0.03
CRITICAL_THRESHOLD = 0.08


def load_results(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_regressions(
    baseline_results: list,
    current_results: list,
) -> list:

    baseline_by_id = {
        result["id"]: result
        for result in baseline_results
    }

    current_by_id = {
        result["id"]: result
        for result in current_results
    }

    regressions = []

    for case_id, current in current_by_id.items():

        baseline = baseline_by_id.get(case_id)

        if baseline is None:
            continue

        baseline_correct = baseline["category_correct"]
        current_correct = current["category_correct"]

        if baseline_correct and not current_correct:

            regressions.append(
                {
                    "id": case_id,
                    "expected_category": current[
                        "expected_category"
                    ],
                    "baseline_category": baseline[
                        "actual_category"
                    ],
                    "current_category": current[
                        "actual_category"
                    ],
                    "baseline_latency_ms": baseline[
                        "latency_ms"
                    ],
                    "current_latency_ms": current[
                        "latency_ms"
                    ],
                }
            )

    return regressions


def compare_runs(
    baseline_path: str,
    current_path: str,
) -> dict:

    baseline = load_results(baseline_path)
    current = load_results(current_path)

    baseline_accuracy = baseline["category_accuracy"]
    current_accuracy = current["category_accuracy"]

    accuracy_change = current_accuracy - baseline_accuracy

    accuracy_drop = max(0, -accuracy_change)

    if accuracy_drop >= CRITICAL_THRESHOLD:
        status = "CRITICAL"

    elif accuracy_drop >= WARNING_THRESHOLD:
        status = "WARNING"

    else:
        status = "PASS"

    regressions = find_regressions(
        baseline["results"],
        current["results"],
    )

    return {
        "baseline_accuracy": baseline_accuracy,
        "current_accuracy": current_accuracy,
        "accuracy_change": accuracy_change,
        "accuracy_drop": accuracy_drop,
        "status": status,
        "regressions": regressions,
        "regression_count": len(regressions),
    }