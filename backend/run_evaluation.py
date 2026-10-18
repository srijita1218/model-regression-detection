
import json
import sys
from datetime import datetime
from pathlib import Path

from backend.evaluator import evaluate_dataset
from backend.run_store import save_run


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


run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
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

print(f"Total cases: {results['total_cases']}")
print(f"Correct categories: {results['correct_categories']}")
print(f"Category accuracy: {results['category_accuracy'] * 100:.2f}%")
print(f"Average summary score: {results['average_summary_score']:.4f}")


latency = results["latency"]

print(f"Minimum latency: {latency['minimum_ms']:.2f} ms")
print(f"Average latency: {latency['average_ms']:.2f} ms")
print(f"P50 latency: {latency['p50_ms']:.2f} ms")
print(f"P95 latency: {latency['p95_ms']:.2f} ms")
print(f"Maximum latency: {latency['maximum_ms']:.2f} ms")


tokens = results["tokens"]

print()
print(f"Total prompt tokens: {tokens['total_prompt_tokens']}")
print(f"Total generated tokens: {tokens['total_generated_tokens']}")
print(f"Total tokens: {tokens['total_tokens']}")
print(f"Average prompt tokens: {tokens['average_prompt_tokens']:.2f}")
print(f"Average generated tokens: {tokens['average_generated_tokens']:.2f}")
print(f"Average total tokens: {tokens['average_total_tokens']:.2f}")

print("=" * 60)


results["run_id"] = run_id
results["timestamp"] = timestamp
results["prompt_version"] = prompt_version
results["model"] = MODEL_NAME
results["dataset"] = dataset_name
results["status"] = "COMPLETED"


# Preserve the existing output path for baseline/current comparisons.
output_path = Path(OUTPUT_PATH)
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as file:
    json.dump(results, file, indent=2, ensure_ascii=False)
    file.write("\n")


# Save a permanent copy and update latest.json and run_history.json.
save_run(results)


print()
print(f"Results saved to {output_path}")
print(f"Run ID: {run_id}")
print("Run history updated.")
