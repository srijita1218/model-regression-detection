import argparse
import json
import sys
from pathlib import Path

from backend.dataset_loader import load_dataset
from backend.generate_report import generate_report
from backend.regression import compare_runs, load_results

DEFAULT_BASELINE_PATH = "results/baseline.json"
DEFAULT_CURRENT_PATH = "results/latest.json"
DEFAULT_COMPARISON_OUTPUT = "results/comparison.json"
DEFAULT_REPORT_OUTPUT = "results/report.html"


def run_comparison(
    baseline_path: str = DEFAULT_BASELINE_PATH,
    current_path: str = DEFAULT_CURRENT_PATH,
    output_path: str = DEFAULT_COMPARISON_OUTPUT,
    generate_html_report: bool = False,
    report_output_path: str = DEFAULT_REPORT_OUTPUT,
) -> dict:
    result = compare_runs(
        baseline_path,
        current_path,
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
    print(f"Baseline accuracy: {result['baseline_accuracy'] * 100:.2f}%")
    print(f"Current accuracy:  {result['current_accuracy'] * 100:.2f}%")
    print(f"Accuracy change:   {result['accuracy_change'] * 100:.2f}%")
    print(f"Accuracy drop:     {result['accuracy_drop'] * 100:.2f}%")
    print(f"Category regressions: {result['regression_count']}")

    # ============================================================
    # MCNEMAR TEST
    # ============================================================
    mcnemar = result["mcnemar"]
    print()
    print("MCNEMAR STATISTICAL TEST")
    print("-" * 60)
    print(f"Paired cases: {mcnemar['n_paired']}")
    print(f"Baseline correct -> Current wrong: {mcnemar['regressions']}")
    print(f"Baseline wrong -> Current correct: {mcnemar['improvements']}")
    print(f"Direction: {mcnemar['direction']}")
    print(f"p-value: {mcnemar['p_value']:.4f}")
    print(f"Significant at α={mcnemar['alpha']}: {mcnemar['significant']}")
    print(f"Significant regression: {mcnemar['significant_regression']}")

    # ============================================================
    # SUMMARY METRICS
    # ============================================================
    print()
    print("SUMMARY QUALITY")
    print("-" * 60)
    baseline_summary = result["baseline_summary_score"]
    current_summary = result["current_summary_score"]

    if baseline_summary is not None and current_summary is not None:
        print(f"Baseline average summary score: {baseline_summary:.4f}")
        print(f"Current average summary score:  {current_summary:.4f}")
        print(f"Summary score change:            {result['summary_score_change']:+.4f}")
    else:
        print("Aggregate summary score unavailable.")

    print(f"Summary regressions: {result['summary_regression_count']}")

    if result["summary_regressions"]:
        print()
        print("SUMMARY REGRESSIONS")
        print("-" * 60)
        for regression in result["summary_regressions"]:
            print()
            print(regression["id"])
            print(f"  Baseline score: {regression['baseline_summary_score']:.4f}")
            print(f"  Current score:  {regression['current_summary_score']:.4f}")
            print(f"  Drop:            {regression['drop']:.4f}")
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
    print(f"Baseline P95: {baseline_latency['p95_ms']:.2f} ms")
    print(f"Current P95:  {current_latency['p95_ms']:.2f} ms")

    latency_regression = result["latency_regression"]
    if latency_regression is None:
        print("Latency regression: NO")
    else:
        print(f"P95 increase: {latency_regression['increase_pct']:.2f}%")
        print(f"Threshold: {latency_regression['threshold_pct']:.2f}%")
        print(f"Latency regression: {latency_regression['regression']}")

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
            print(f"  Expected: {regression['expected_category']}")
            print(f"  Baseline: {regression['baseline_category']}")
            print(f"  Current:  {regression['current_category']}")
            print(
                f"  Latency:  {regression['baseline_latency_ms']:.2f} ms -> "
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

    # Save comparison JSON
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2)

    print()
    print(f"Comparison saved to {out_file}")

    if generate_html_report:
        baseline_data = load_results(baseline_path)
        current_data = load_results(current_path)

        case_texts = None
        dataset_name = current_data.get("dataset") or baseline_data.get("dataset")
        if dataset_name:
            dataset_candidate = Path("datasets") / dataset_name
            if dataset_candidate.is_file():
                try:
                    cases, _ = load_dataset(str(dataset_candidate))
                    case_texts = {c.id: c.input.text for c in cases}
                except Exception:
                    pass

        generate_report(
            latest=current_data,
            comparison=result,
            out_path=report_output_path,
            baseline=baseline_data,
            case_texts=case_texts,
        )
        print(f"HTML report generated at {report_output_path}")

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare two ModelWatch evaluation runs and detect quality regressions."
    )
    parser.add_argument(
        "-b", "--baseline",
        dest="baseline",
        default=DEFAULT_BASELINE_PATH,
        help=f"Path to baseline evaluation JSON (default: {DEFAULT_BASELINE_PATH})",
    )
    parser.add_argument(
        "-c", "--current",
        dest="current",
        default=DEFAULT_CURRENT_PATH,
        help=f"Path to candidate evaluation JSON (default: {DEFAULT_CURRENT_PATH})",
    )
    parser.add_argument(
        "-o", "--output",
        dest="output",
        default=DEFAULT_COMPARISON_OUTPUT,
        help=f"Path to output comparison JSON (default: {DEFAULT_COMPARISON_OUTPUT})",
    )
    parser.add_argument(
        "-r", "--report",
        dest="report",
        action="store_true",
        help="Generate HTML report",
    )
    parser.add_argument(
        "--report-output",
        dest="report_output",
        default=DEFAULT_REPORT_OUTPUT,
        help=f"Path for generated HTML report (default: {DEFAULT_REPORT_OUTPUT})",
    )
    # Positional arguments for legacy backward compatibility:
    parser.add_argument("baseline_pos", nargs="?", help="Positional baseline path (legacy)")
    parser.add_argument("current_pos", nargs="?", help="Positional current path (legacy)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    baseline = (
        args.baseline_pos
        if args.baseline_pos and args.baseline == DEFAULT_BASELINE_PATH
        else args.baseline
    )
    current = (
        args.current_pos
        if args.current_pos and args.current == DEFAULT_CURRENT_PATH
        else args.current
    )

    if not Path(baseline).is_file():
        print(f"Error: Baseline file not found: {baseline}", file=sys.stderr)
        return 2

    if not Path(current).is_file():
        print(f"Error: Current file not found: {current}", file=sys.stderr)
        return 2

    try:
        result = run_comparison(
            baseline_path=baseline,
            current_path=current,
            output_path=args.output,
            generate_html_report=args.report,
            report_output_path=args.report_output,
        )

        if result["status"] == "CRITICAL":
            return 1

        return 0

    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
