"""
without MCNemar test we wouldnt know if the change is statistically significant.
"""

import json

from statsmodels.stats.contingency_tables import mcnemar


WARNING_THRESHOLD = 0.03
CRITICAL_THRESHOLD = 0.08
SIGNIFICANCE_LEVEL = 0.05


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


def calculate_mcnemar(
    baseline_results: list,
    current_results: list,
) -> dict:

    baseline_by_id = {
        result["id"]: result
        for result in baseline_results
    }

    current_by_id = {
        result["id"]: result
        for result in current_results
    }

    both_correct = 0
    baseline_correct_current_wrong = 0
    baseline_wrong_current_correct = 0
    both_wrong = 0

    for case_id, baseline in baseline_by_id.items():

        current = current_by_id.get(case_id)

        if current is None:
            continue

        baseline_correct = baseline["category_correct"]
        current_correct = current["category_correct"]

        if baseline_correct and current_correct:
            both_correct += 1

        elif baseline_correct and not current_correct:
            baseline_correct_current_wrong += 1

        elif not baseline_correct and current_correct:
            baseline_wrong_current_correct += 1

        else:
            both_wrong += 1

    regressions = baseline_correct_current_wrong
    improvements = baseline_wrong_current_correct

    discordant_cases = regressions + improvements

    # NEW: how many cases were actually compared, and how many had no match
    n_paired = (
        both_correct
        + regressions
        + improvements
        + both_wrong
    )
    only_in_baseline = len(
        baseline_by_id.keys() - current_by_id.keys()
    )
    only_in_current = len(
        current_by_id.keys() - baseline_by_id.keys()
    )

    # NEW: which way did the change go?
    if regressions > improvements:
        direction = "regression"
    elif improvements > regressions:
        direction = "improvement"
    else:
        direction = "none"

    if discordant_cases == 0:
        return {
            "n_paired": n_paired,                    # NEW
            "only_in_baseline": only_in_baseline,    # NEW
            "only_in_current": only_in_current,      # NEW
            "regressions": 0,
            "improvements": 0,
            "p_value": 1.0,
            "alpha": SIGNIFICANCE_LEVEL,
            "significant": False,
            "direction": "none",                     # NEW
            "significant_regression": False,         # NEW
        }

    table = [
        [both_correct, regressions],
        [improvements, both_wrong],
    ]

    result = mcnemar(
        table,
        exact=True,
    )

    # CHANGED: compare the unrounded p-value, round only for output
    raw_p_value = float(result.pvalue)
    significant = bool(raw_p_value < SIGNIFICANCE_LEVEL)

    return {
        "n_paired": n_paired,                        # NEW
        "only_in_baseline": only_in_baseline,        # NEW
        "only_in_current": only_in_current,          # NEW
        "regressions": regressions,
        "improvements": improvements,
        "p_value": round(raw_p_value, 4),
        "alpha": SIGNIFICANCE_LEVEL,
        "significant": significant,
        "direction": direction,                      # NEW
        "significant_regression": (                  # NEW
            significant and direction == "regression"
        ),
    }


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

    mcnemar_result = calculate_mcnemar(
        baseline["results"],
        current["results"],
    )

    # NEW: flag runs that don't cover the same cases
    warnings = []

    if (
        mcnemar_result["only_in_baseline"]
        or mcnemar_result["only_in_current"]
    ):
        warnings.append(
            f"Runs contain different cases: "
            f"{mcnemar_result['only_in_baseline']} only in baseline, "
            f"{mcnemar_result['only_in_current']} only in current. "
            f"Significance test used {mcnemar_result['n_paired']} "
            f"shared cases only."
        )

    return {
        "baseline_accuracy": baseline_accuracy,
        "current_accuracy": current_accuracy,
        "accuracy_change": accuracy_change,
        "accuracy_drop": accuracy_drop,
        "status": status,
        "regressions": regressions,
        "regression_count": len(regressions),
        "mcnemar": mcnemar_result,
        "warnings": warnings,                        # NEW
    }