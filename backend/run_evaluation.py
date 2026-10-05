import json

from backend.evaluator import evaluate_dataset


DATASET_PATH = "datasets/golden_dataset.json"
PROMPT_PATH = "prompts/v1.yaml"


results = evaluate_dataset(
    DATASET_PATH,
    PROMPT_PATH,
)

print()
print("=" * 50)
print("MODELWATCH EVALUATION")
print("=" * 50)

print(
    f"Total cases: {results['total_cases']}"
)

print(
    f"Correct categories: {results['correct_categories']}"
)

print(
    f"Category accuracy: "
    f"{results['category_accuracy'] * 100:.2f}%"
)

print(
    f"Average summary score: "
    f"{results['average_summary_score']:.4f}"
)

latency = results["latency"]

print(
    f"Minimum latency: "
    f"{latency['minimum_ms']:.2f} ms"
)

print(
    f"Average latency: "
    f"{latency['average_ms']:.2f} ms"
)

print(
    f"P50 latency:     "
    f"{latency['p50_ms']:.2f} ms"
)

print(
    f"P95 latency:     "
    f"{latency['p95_ms']:.2f} ms"
)

print(
    f"Maximum latency: "
    f"{latency['maximum_ms']:.2f} ms"
)

print("=" * 50)

tokens = results["tokens"]

print()

print(
    f"Total prompt tokens: "
    f"{tokens['total_prompt_tokens']}"
)

print(
    f"Total generated tokens: "
    f"{tokens['total_generated_tokens']}"
)

print(
    f"Total tokens: "
    f"{tokens['total_tokens']}"
)

print(
    f"Average prompt tokens: "
    f"{tokens['average_prompt_tokens']:.2f}"
)

print(
    f"Average generated tokens: "
    f"{tokens['average_generated_tokens']:.2f}"
)

print(
    f"Average total tokens: "
    f"{tokens['average_total_tokens']:.2f}"
)

with open(
    "results/latest.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        results,
        file,
        indent=2,
    )

print("Results saved to results/latest.json")