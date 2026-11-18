
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from backend.evaluator import evaluate_dataset
from backend.llm_client import MODEL_NAME
from backend.run_metadata import stamp_metadata
from backend.run_store import save_run
from backend.compare_runs import run_comparison as run_comparison_cli


DEFAULT_DATASET_PATH = "datasets/golden_dataset.json"
DEFAULT_OUTPUT_PATH = "results/latest.json"


def run_evaluation(
    prompt_path: str,
    output_path: str = DEFAULT_OUTPUT_PATH,
    dataset_path: str = DEFAULT_DATASET_PATH,
) -> dict:
    started = datetime.now()

    print()
    print("=" * 60)
    print("MODELWATCH EVALUATION")
    print("=" * 60)
    print(f"Dataset:       {Path(dataset_path).name}")
    print(f"Prompt:        {prompt_path}")
    print(f"Model:         {MODEL_NAME}")
    print(f"Output:        {output_path}")
    print("=" * 60)
    print()

    results = evaluate_dataset(dataset_path, prompt_path)

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

    tokens = results.get("tokens", {})
    print()
    print(f"Total prompt tokens: {tokens.get('total_prompt_tokens', 0)}")
    print(f"Total generated tokens: {tokens.get('total_generated_tokens', 0)}")
    print(f"Total tokens: {tokens.get('total_tokens', 0)}")
    print(f"Average prompt tokens: {tokens.get('average_prompt_tokens', 0.0):.2f}")
    print(f"Average generated tokens: {tokens.get('average_generated_tokens', 0.0):.2f}")
    print(f"Average total tokens: {tokens.get('average_total_tokens', 0.0):.2f}")
    print("=" * 60)

    stamp_metadata(
        results,
        prompt_path=prompt_path,
        dataset_path=dataset_path,
        started=started,
    )

    target_output = Path(output_path)
    target_output.parent.mkdir(parents=True, exist_ok=True)

    with target_output.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)
        file.write("\n")

    save_run(results)

    print()
    print(f"Results saved to {target_output}")
    print(f"Run ID: {results['run_id']}")
    print("Run history updated.")

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run ModelWatch evaluation on a prompt against a dataset."
    )

    parser.add_argument(
        "-p", "--prompt",
        dest="prompt",
        help="Path to prompt YAML file",
    )

    parser.add_argument(
        "-d", "--dataset",
        dest="dataset",
        default=DEFAULT_DATASET_PATH,
        help=f"Path to dataset JSON file (default: {DEFAULT_DATASET_PATH})",
    )

    parser.add_argument(
        "-o", "--output",
        dest="output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path to output evaluation JSON file (default: {DEFAULT_OUTPUT_PATH})",
    )

    parser.add_argument(
        "-c", "--compare",
        dest="compare",
        help="Optional path to baseline JSON to automatically compare against",
    )

    parser.add_argument(
        "-r", "--report",
        dest="report",
        action="store_true",
        help="Generate HTML report if --compare is set",
    )

    parser.add_argument(
        "--report-output",
        dest="report_output",
        default="results/report.html",
        help="Path for generated HTML report (default: results/report.html)",
    )

    # Positional arguments for legacy backward compatibility.
    parser.add_argument(
        "prompt_pos",
        nargs="?",
        help="Positional prompt path (legacy)",
    )

    parser.add_argument(
        "output_pos",
        nargs="?",
        help="Positional output path (legacy)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    prompt = args.prompt or args.prompt_pos

    if not prompt:
        parser.error(
            "Prompt path is required (use --prompt <path> or positional <prompt_path>)."
        )

    if args.report and not args.compare:
        parser.error("--report requires --compare.")

    # Preserve legacy positional output-path behaviour.
    output = (
        args.output_pos
        if args.output_pos and args.output == DEFAULT_OUTPUT_PATH
        else args.output
    )

    try:
        # Validate input files before starting evaluation.
        required_files = [
            ("Prompt", prompt),
            ("Dataset", args.dataset),
        ]

        if args.compare:
            required_files.append(("Baseline", args.compare))

        for label, file_path in required_files:
            if not Path(file_path).is_file():
                print(
                    f"Error: {label} file not found: {file_path}",
                    file=sys.stderr,
                )
                return 2

        run_evaluation(
            prompt_path=prompt,
            output_path=output,
            dataset_path=args.dataset,
        )

        if args.compare:
            print()
            print("=" * 60)
            print("RUNNING AUTOMATIC COMPARISON AGAINST BASELINE")
            print("=" * 60)

            comparison = run_comparison_cli(
                baseline_path=args.compare,
                current_path=output,
                generate_html_report=args.report,
                report_output_path=args.report_output,
            )

            if comparison["status"] == "CRITICAL":
                return 1

        return 0

    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
