
"""
ModelWatch regression analysis.

Compares a baseline evaluation run against a current evaluation run
across category accuracy, summary quality, latency, and statistical
significance.
"""

import json
import os

from statsmodels.stats.contingency_tables import mcnemar


# Default thresholds. Environment variables can override these.
WARNING_THRESHOLD = 0.03
CRITICAL_THRESHOLD = 0.08
SIGNIFICANCE_LEVEL = 0.05

SUMMARY_DROP_THRESHOLD = 0.2
LATENCY_P95_INCREASE_THRESHOLD = 0.3


def get_threshold(env_name: str, default: float) -> float:
    """Read a numeric threshold from an environment variable."""

    value = os.getenv(env_name)

    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        raise ValueError(
            f"Invalid value for {env_name}: {value!r}. "
            "Expected a number."
        )


def load_results(path: str) -> dict:
    """Load an evaluation result JSON file."""

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def find_regressions(
    baseline_results: list,
    current_results: list,
) -> list:
    """Find individual cases where category correctness regressed."""

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
                    "expected_category": current["expected_category"],
                    "baseline_category": baseline["actual_category"],
                    "current_category": current["actual_category"],
                    "baseline_latency_ms": baseline["latency_ms"],
                    "current_latency_ms": current["latency_ms"],
                }
            )

    return regressions


def find_improvements(
    baseline_results: list,
    current_results: list,
) -> list:
    """Find individual cases where category correctness improved."""

    baseline_by_id = {
        result["id"]: result
        for result in baseline_results
    }

    current_by_id = {
        result["id"]: result
        for result in current_results
    }

    improvements = []

    for case_id, current in current_by_id.items():
        baseline = baseline_by_id.get(case_id)

        if baseline is None:
            continue

        baseline_correct = baseline["category_correct"]
        current_correct = current["category_correct"]

        if not baseline_correct and current_correct:
            improvements.append(
                {
                    "id": case_id,
                    "expected_category": current["expected_category"],
                    "baseline_category": baseline["actual_category"],
                    "current_category": current["actual_category"],
                    "baseline_latency_ms": baseline["latency_ms"],
                    "current_latency_ms": current["latency_ms"],
                }
            )

    return improvements


def calculate_category_accuracy_delta(
    baseline_results: list,
    current_results: list,
) -> dict:
    """Calculate per-category accuracy changes in percentage points."""

    def category_accuracy(results):
        category_counts = {}

        for result in results:
            category = result.get("expected_category")

            if category is None or "category_correct" not in result:
                continue

            if category not in category_counts:
                category_counts[category] = {
                    "correct": 0,
                    "total": 0,
                }

            category_counts[category]["total"] += 1

            if result["category_correct"]:
                category_counts[category]["correct"] += 1

        return {
            category: counts["correct"] / counts["total"]
            for category, counts in category_counts.items()
            if counts["total"] > 0
        }

    baseline_accuracy = category_accuracy(baseline_results)
    current_accuracy = category_accuracy(current_results)

    deltas = {}

    for category in sorted(
        set(baseline_accuracy) | set(current_accuracy)
    ):
        baseline_value = baseline_accuracy.get(category)
        current_value = current_accuracy.get(category)

        if baseline_value is None or current_value is None:
            deltas[category] = {
                "baseline_accuracy": (
                    round(baseline_value * 100, 2)
                    if baseline_value is not None else None
                ),
                "current_accuracy": (
                    round(current_value * 100, 2)
                    if current_value is not None else None
                ),
                "delta_pp": None,
            }
            continue

        deltas[category] = {
            "baseline_accuracy": round(baseline_value * 100, 2),
            "current_accuracy": round(current_value * 100, 2),
            "delta_pp": round(
                (current_value - baseline_value) * 100,
                2,
            ),
        }

    return deltas


def find_summary_regressions(
    baseline_results: list,
    current_results: list,
) -> list:
    """Find cases with a significant summary-quality drop."""

    summary_drop_threshold = get_threshold(
        "MODELWATCH_SUMMARY_DROP_THRESHOLD",
        SUMMARY_DROP_THRESHOLD,
    )

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

        if (
            "summary_score" not in baseline
            or "summary_score" not in current
        ):
            continue

        baseline_score = baseline["summary_score"]
        current_score = current["summary_score"]

        drop = baseline_score - current_score

        if drop >= summary_drop_threshold:
            regressions.append(
                {
                    "id": case_id,
                    "baseline_summary_score": baseline_score,
                    "current_summary_score": current_score,
                    "drop": round(drop, 4),
                }
            )

    return regressions


def find_latency_regression(
    baseline_latency: dict,
    current_latency: dict,
) -> dict | None:
    """Check whether P95 latency increased by the configured threshold."""

    if (
        "p95_ms" not in baseline_latency
        or "p95_ms" not in current_latency
    ):
        return None

    baseline_p95 = baseline_latency["p95_ms"]
    current_p95 = current_latency["p95_ms"]

    # A percentage increase cannot be calculated from a zero baseline.
    if baseline_p95 <= 0:
        return None

    latency_threshold = get_threshold(
        "MODELWATCH_LATENCY_P95_INCREASE_THRESHOLD",
        LATENCY_P95_INCREASE_THRESHOLD,
    )

    increase_pct = (
        (current_p95 - baseline_p95)
        / baseline_p95
    )

    if increase_pct < latency_threshold:
        return None

    return {
        "baseline_p95_ms": baseline_p95,
        "current_p95_ms": current_p95,
        "increase_pct": round(increase_pct * 100, 2),
        "threshold_pct": latency_threshold * 100,
        "regression": True,
    }


def calculate_mcnemar(
    baseline_results: list,
    current_results: list,
) -> dict:
    """Run McNemar's exact test on paired category results."""

    significance_level = get_threshold(
        "MODELWATCH_SIGNIFICANCE_LEVEL",
        SIGNIFICANCE_LEVEL,
    )

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

    if regressions > improvements:
        direction = "regression"
    elif improvements > regressions:
        direction = "improvement"
    else:
        direction = "none"

    if discordant_cases == 0:
        return {
            "n_paired": n_paired,
            "only_in_baseline": only_in_baseline,
            "only_in_current": only_in_current,
            "regressions": 0,
            "improvements": 0,
            "p_value": 1.0,
            "alpha": significance_level,
            "significant": False,
            "direction": "none",
            "significant_regression": False,
        }

    table = [
        [both_correct, regressions],
        [improvements, both_wrong],
    ]

    result = mcnemar(
        table,
        exact=True,
    )

    raw_p_value = float(result.pvalue)

    significant = raw_p_value < significance_level

    return {
        "n_paired": n_paired,
        "only_in_baseline": only_in_baseline,
        "only_in_current": only_in_current,
        "regressions": regressions,
        "improvements": improvements,
        "p_value": round(raw_p_value, 4),
        "alpha": significance_level,
        "significant": significant,
        "direction": direction,
        "significant_regression": (
            significant and direction == "regression"
        ),
    }


def determine_status(
    accuracy_drop: float,
    summary_regression_count: int,
    latency_regression: dict | None,
    mcnemar_result: dict,
    summary_score_change: float | None = None,
) -> str:
    """Determine the overall ModelWatch status."""

    warning_threshold = get_threshold(
        "MODELWATCH_WARNING_THRESHOLD",
        WARNING_THRESHOLD,
    )

    critical_threshold = get_threshold(
        "MODELWATCH_CRITICAL_THRESHOLD",
        CRITICAL_THRESHOLD,
    )

    # CRITICAL CONDITIONS

    if accuracy_drop >= critical_threshold:
        return "CRITICAL"

    # A statistically significant regression can block CI.
    # A significant improvement does not raise regression status.
    if mcnemar_result["significant_regression"]:
        return "CRITICAL"


    # WARNING CONDITIONS

    if accuracy_drop >= warning_threshold:
        return "WARNING"

    if (
        latency_regression is not None
        and latency_regression["regression"]
    ):
        return "WARNING"

    if summary_regression_count > 0:
        return "WARNING"

    if (
        summary_score_change is not None
        and summary_score_change < 0
    ):
        return "WARNING"

    return "PASS"


def compare_runs(
    baseline_path: str,
    current_path: str,
) -> dict:
    """Compare two ModelWatch evaluation runs."""

    baseline = load_results(baseline_path)
    current = load_results(current_path)

    baseline_accuracy = baseline["category_accuracy"]
    current_accuracy = current["category_accuracy"]

    accuracy_change = current_accuracy - baseline_accuracy

    accuracy_drop = max(
        0,
        -accuracy_change,
    )

    regressions = find_regressions(
        baseline["results"],
        current["results"],
    )

    improvements = find_improvements(
        baseline["results"],
        current["results"],
    )

    category_accuracy_delta = calculate_category_accuracy_delta(
        baseline["results"],
        current["results"],
    )

    summary_regressions = find_summary_regressions(
        baseline["results"],
        current["results"],
    )

    latency_regression = find_latency_regression(
        baseline["latency"],
        current["latency"],
    )

    mcnemar_result = calculate_mcnemar(
        baseline["results"],
        current["results"],
    )

    # SUMMARY AGGREGATE METRICS

    baseline_summary_score = baseline.get(
        "average_summary_score"
    )

    current_summary_score = current.get(
        "average_summary_score"
    )

    if (
        baseline_summary_score is not None
        and current_summary_score is not None
    ):
        summary_score_change = (
            current_summary_score - baseline_summary_score
        )
    else:
        summary_score_change = None

    # WARNINGS

    warnings = []

    if (
        mcnemar_result["only_in_baseline"]
        or mcnemar_result["only_in_current"]
    ):
        warnings.append(
            f"Runs contain different cases: "
            f"{mcnemar_result['only_in_baseline']} "
            f"only in baseline, "
            f"{mcnemar_result['only_in_current']} "
            f"only in current. "
            f"Significance test used "
            f"{mcnemar_result['n_paired']} "
            f"shared cases only."
        )

    # Check whether the runs use matching metadata.

    for field in ("model", "dataset", "dataset_version"):
        baseline_value = baseline.get(field)
        current_value = current.get(field)

        if baseline_value != current_value:
            warnings.append(
                f"{field} mismatch: baseline={baseline_value!r}, "
                f"current={current_value!r}"
            )

    # OVERALL STATUS

    status = determine_status(
        accuracy_drop=accuracy_drop,
        summary_regression_count=len(summary_regressions),
        latency_regression=latency_regression,
        mcnemar_result=mcnemar_result,
        summary_score_change=summary_score_change,
    )

    return {
        "baseline_accuracy": baseline_accuracy,
        "current_accuracy": current_accuracy,
        "accuracy_change": accuracy_change,
        "accuracy_drop": accuracy_drop,

        "baseline_summary_score": baseline_summary_score,
        "current_summary_score": current_summary_score,
        "summary_score_change": summary_score_change,

        "baseline_latency": baseline["latency"],
        "current_latency": current["latency"],

        "status": status,

        "regressions": regressions,
        "regression_count": len(regressions),

        "improvements": improvements,
        "improvement_count": len(improvements),

        "category_accuracy_delta": category_accuracy_delta,

        "summary_regressions": summary_regressions,
        "summary_regression_count": len(summary_regressions),

        "latency_regression": latency_regression,

        "mcnemar": mcnemar_result,

        "warnings": warnings,
    }

def test_warning_threshold_can_be_configured(monkeypatch):
    from backend.regression import determine_status

    monkeypatch.setenv(
        "MODELWATCH_WARNING_THRESHOLD",
        "0.05",
    )

    result = determine_status(
        accuracy_drop=0.04,
        summary_regression_count=0,
        latency_regression=None,
        mcnemar_result={"significant_regression": False},
    )

    assert result == "PASS"


def test_critical_threshold_can_be_configured(monkeypatch):
    from backend.regression import determine_status

    monkeypatch.setenv(
        "MODELWATCH_CRITICAL_THRESHOLD",
        "0.05",
    )

    result = determine_status(
        accuracy_drop=0.06,
        summary_regression_count=0,
        latency_regression=None,
        mcnemar_result={"significant_regression": False},
    )

    assert result == "CRITICAL"


def test_summary_threshold_can_be_configured(monkeypatch):
    from backend.regression import find_summary_regressions

    monkeypatch.setenv(
        "MODELWATCH_SUMMARY_DROP_THRESHOLD",
        "0.3",
    )

    baseline = [
        {"id": "TC001", "summary_score": 0.9}
    ]
    current = [
        {"id": "TC001", "summary_score": 0.65}
    ]

    result = find_summary_regressions(baseline, current)

    assert result == []


def test_latency_threshold_can_be_configured(monkeypatch):
    from backend.regression import find_latency_regression

    monkeypatch.setenv(
        "MODELWATCH_LATENCY_P95_INCREASE_THRESHOLD",
        "0.5",
    )

    result = find_latency_regression(
        {"p95_ms": 100},
        {"p95_ms": 140},
    )

    assert result is None


def test_significance_level_can_be_configured(monkeypatch):
    from backend.regression import calculate_mcnemar

    monkeypatch.setenv(
        "MODELWATCH_SIGNIFICANCE_LEVEL",
        "0.01",
    )

    baseline = [
        {"id": f"TC{i}", "category_correct": True}
        for i in range(1, 6)
    ]
    current = [
        {"id": f"TC{i}", "category_correct": False}
        for i in range(1, 6)
    ]

    result = calculate_mcnemar(baseline, current)

    assert result["alpha"] == 0.01
    assert result["significant"] is False


def test_invalid_threshold_raises_error(monkeypatch):
    import pytest
    from backend.regression import get_threshold

    monkeypatch.setenv(
        "MODELWATCH_WARNING_THRESHOLD",
        "not-a-number",
    )

    with pytest.raises(ValueError):
        get_threshold("MODELWATCH_WARNING_THRESHOLD", 0.03)
