import json
import sys
from datetime import datetime
from pathlib import Path

from backend.evaluator import evaluate_dataset


DATASET_PATH = "datasets/golden_dataset.json"
MODEL_NAME = "llama2"


if len(sys.argv) != 3:
    print(
        "Usage: python backend/run_evaluation.py "
        "<prompt_path> <output_path>"
    )
    print()
    print("Example:")
    print(
        "python backend/run_evaluation.py "
        "prompts/v1.yaml results/baseline.json"
    )
    sys.exit(1)


PROMPT_PATH = sys.argv[1]
OUTPUT_PATH = sys.argv[2]


run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
timestamp = datetime.now().isoformat()

prompt_version = Path(PROMPT_PATH).stem
dataset_name = Path(DATASET_PATH).name


print()
print("=" * 60)
print("MODELWATCH EVALUATION")
print("=" * 60)

print(f"Dataset:       {dataset_name}")
print(f"Prompt:        {PROMPT_PATH}")
print(f"Model:         {MODEL_NAME}")
print(f"Output:        {OUTPUT_PATH}")
print("=" * 60)
print()


results = evaluate_dataset(
    DATASET_PATH,
    PROMPT_PATH,
)


print()
print("=" * 60)
print("EVALUATION SUMMARY")
print("=" * 60)

print(
    f"Total cases: "
    f"{results['total_cases']}"
)

print(
    f"Correct categories: "
    f"{results['correct_categories']}"
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
    f"P50 latency: "
    f"{latency['p50_ms']:.2f} ms"
)

print(
    f"P95 latency: "
    f"{latency['p95_ms']:.2f} ms"
)

print(
    f"Maximum latency: "
    f"{latency['maximum_ms']:.2f} ms"
)


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

print("=" * 60)


results["run_id"] = run_id
results["timestamp"] = timestamp
results["prompt_version"] = prompt_version
results["model"] = MODEL_NAME
results["dataset"] = dataset_name
results["status"] = "COMPLETED"


output_path = Path(OUTPUT_PATH)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)


with open(
    output_path,
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        results,
        file,
        indent=2,
    )


print()
print(
    f"Results saved to {output_path}"
)