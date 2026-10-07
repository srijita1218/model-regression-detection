import json

from backend.regression import compare_runs


result = compare_runs(
    "results/baseline.json",
    "results/latest.json",
)


print()
print("=" * 60)
print("MODELWATCH REGRESSION ANALYSIS")
print("=" * 60)


# ============================================================
# CATEGORY METRICS
# ============================================================

print()
print("CATEGORY METRICS")
print("-" * 60)

print(
    f"Baseline accuracy: {result['baseline_accuracy'] * 100:.2f}%"
)

print(
    f"Current accuracy:  {result['current_accuracy'] * 100:.2f}%"
)

print(
    f"Accuracy change:   {result['accuracy_change'] * 100:.2f}%"
)

print(
    f"Accuracy drop:     {result['accuracy_drop'] * 100:.2f}%"
)

print(
    f"Category regressions: {result['regression_count']}"
)


# ============================================================
# MCMAR TEST
# ============================================================

mcnemar = result["mcnemar"]

print()
print("MCNEMAR STATISTICAL TEST")
print("-" * 60)

print(
    f"Paired cases: {mcnemar['n_paired']}"
)

print(
    f"Baseline correct -> Current wrong: "
    f"{mcnemar['regressions']}"
)

print(
    f"Baseline wrong -> Current correct: "
    f"{mcnemar['improvements']}"
)

print(
    f"Direction: {mcnemar['direction']}"
)

print(
    f"p-value: {mcnemar['p_value']:.4f}"
)

print(
    f"Significant at α={mcnemar['alpha']}: "
    f"{mcnemar['significant']}"
)

print(
    f"Significant regression: "
    f"{mcnemar['significant_regression']}"
)


# ============================================================
# SUMMARY METRICS
# ============================================================

print()
print("SUMMARY QUALITY")
print("-" * 60)

baseline_summary = result["baseline_summary_score"]
current_summary = result["current_summary_score"]

if (
    baseline_summary is not None
    and current_summary is not None
):
    print(
        f"Baseline average summary score: "
        f"{baseline_summary:.4f}"
    )

    print(
        f"Current average summary score:  "
        f"{current_summary:.4f}"
    )

    print(
        f"Summary score change:            "
        f"{result['summary_score_change']:+.4f}"
    )
else:
    print("Aggregate summary score unavailable.")

print(
    f"Summary regressions: "
    f"{result['summary_regression_count']}"
)

if result["summary_regressions"]:

    print()
    print("SUMMARY REGRESSIONS")
    print("-" * 60)

    for regression in result["summary_regressions"]:

        print()
        print(regression["id"])

        print(
            f"  Baseline score: "
            f"{regression['baseline_summary_score']:.4f}"
        )

        print(
            f"  Current score:  "
            f"{regression['current_summary_score']:.4f}"
        )

        print(
            f"  Drop:            "
            f"{regression['drop']:.4f}"
        )

else:

    print("No summary regressions detected.")


# ============================================================
# LATENCY
# ============================================================

baseline_latency = result["baseline_latency"]
current_latency = result["current_latency"]

print()
print("LATENCY")
print("-" * 60)

print(
    f"Baseline P95: "
    f"{baseline_latency['p95_ms']:.2f} ms"
)

print(
    f"Current P95:  "
    f"{current_latency['p95_ms']:.2f} ms"
)

latency_regression = result["latency_regression"]

if latency_regression is None:

    print("Latency regression: NO")

else:

    print(
        f"P95 increase: "
        f"{latency_regression['increase_pct']:.2f}%"
    )

    print(
        f"Threshold: "
        f"{latency_regression['threshold_pct']:.2f}%"
    )

    print(
        f"Latency regression: "
        f"{latency_regression['regression']}"
    )


# ============================================================
# CATEGORY REGRESSED CASES
# ============================================================

print()
print("CATEGORY REGRESSIONS")
print("-" * 60)

if result["regressions"]:

    for regression in result["regressions"]:

        print()
        print(regression["id"])

        print(
            f"  Expected: "
            f"{regression['expected_category']}"
        )

        print(
            f"  Baseline: "
            f"{regression['baseline_category']}"
        )

        print(
            f"  Current:  "
            f"{regression['current_category']}"
        )

        print(
            f"  Latency:  "
            f"{regression['baseline_latency_ms']:.2f} ms"
            f" -> "
            f"{regression['current_latency_ms']:.2f} ms"
        )

else:

    print("No individual category regressions detected.")


# ============================================================
# WARNINGS
# ============================================================

if result["warnings"]:

    print()
    print("WARNINGS")
    print("-" * 60)

    for warning in result["warnings"]:
        print(f"- {warning}")


# ============================================================
# FINAL STATUS
# ============================================================

print()
print("=" * 60)
print(f"STATUS: {result['status']}")
print("=" * 60)


# ============================================================
# SAVE COMPARISON
# ============================================================

with open(
    "results/comparison.json",
    "w",
    encoding="utf-8",
) as file:

    json.dump(
        result,
        file,
        indent=2,
    )


print()
print("Comparison saved to results/comparison.json")