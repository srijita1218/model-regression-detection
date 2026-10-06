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

print(
    f"Baseline accuracy: "
    f"{result['baseline_accuracy'] * 100:.2f}%"
)

print(
    f"Current accuracy:  "
    f"{result['current_accuracy'] * 100:.2f}%"
)

print(
    f"Accuracy change:   "
    f"{result['accuracy_change'] * 100:.2f}%"
)

print(
    f"Accuracy drop:     "
    f"{result['accuracy_drop'] * 100:.2f}%"
)

print(
    f"McNemar p-value:   "
    f"{result['mcnemar']['p_value']:.4f}"
)

print(
    f"Statistically significant: "
    f"{result['mcnemar']['significant']}"
)

print()

print()

print(
    f"Regressions found: "
    f"{result['regression_count']}"
)

print()

if result["regressions"]:

    print("REGRESSED CASES")
    print("-" * 60)

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

    print("No individual regressions detected.")


print()

print(
    f"STATUS: {result['status']}"
)

print("=" * 60)

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