import html
import json
from pathlib import Path
from backend.regression import LATENCY_P95_INCREASE_THRESHOLD
from backend.report_trend import load_trend_points, trend_chart_svg

def esc(value) -> str:
    """HTML-escape any value; None becomes an empty string."""
    return html.escape("" if value is None else str(value))

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def generate_report(
    latest: dict,
    comparison: dict,
    out_path: str = "results/report.html",
    baseline: dict | None = None,
    case_texts: dict[str, str] | None = None,
    runs_dir: str = "results/runs",
) -> str:


        status = comparison["status"]

        status_class = status.lower()


        # ============================================================
        # CATEGORY REGRESSION ROWS
        # ============================================================

        regression_rows = ""

        for regression in comparison["regressions"]:

            regression_rows += f"""
            <tr>
                <td>{regression["id"]}</td>
                <td>{regression["expected_category"]}</td>
                <td>{regression["baseline_category"]}</td>
                <td>{regression["current_category"]}</td>
                <td>
                    {regression["baseline_latency_ms"]:.2f} ms
                    →
                    {regression["current_latency_ms"]:.2f} ms
                </td>
            </tr>
            """


        if not regression_rows:

            regression_rows = """
            <tr>
                <td colspan="5">
                    No individual category regressions detected.
                </td>
            </tr>
            """


        # ============================================================
        # SUMMARY REGRESSION ROWS
        # ============================================================

        summary_regression_rows = ""

        for regression in comparison["summary_regressions"]:

            summary_regression_rows += f"""
            <tr>
                <td>{regression["id"]}</td>
                <td>{regression["baseline_summary_score"]:.4f}</td>
                <td>{regression["current_summary_score"]:.4f}</td>
                <td>{regression["drop"]:.4f}</td>
            </tr>
            """


        if not summary_regression_rows:

            summary_regression_rows = """
            <tr>
                <td colspan="4">
                    No individual summary regressions detected.
                </td>
            </tr>
            """


        # ============================================================
        # MCNEMAR
        # ============================================================

        mcnemar = comparison["mcnemar"]

        mcnemar_significance = (
            "Yes"
            if mcnemar["significant"]
            else "No"
        )

        significant_regression = (
            "Yes"
            if mcnemar["significant_regression"]
            else "No"
        )


        # ============================================================
        # LATENCY REGRESSION
        # ============================================================

        latency_regression = comparison["latency_regression"]

        if latency_regression is not None:

            latency_status = "YES"

            latency_increase = (
                f'{latency_regression["increase_pct"]:.2f}%'
            )

            latency_threshold = (
                f'{latency_regression["threshold_pct"]:.2f}%'
            )

        else:

            latency_status = "NO"

            baseline_p95 = (
                comparison["baseline_latency"]["p95_ms"]
            )

            current_p95 = (
                comparison["current_latency"]["p95_ms"]
            )

            if baseline_p95 > 0:

                calculated_increase = (
                    (current_p95 - baseline_p95)
                    / baseline_p95
                ) * 100

                latency_increase = (
                    f"{calculated_increase:.2f}%"
                )

            else:

                latency_increase = "N/A"

            latency_threshold = f"{LATENCY_P95_INCREASE_THRESHOLD * 100:.2f}%"


        # ============================================================
        # SUMMARY SCORE CHANGE
        # ============================================================

        summary_score_change = (
            comparison["summary_score_change"]
        )

        if summary_score_change is None:

            summary_change_display = "N/A"

        else:

            summary_change_display = (
                f"{summary_score_change:+.4f}"
            )


        # ============================================================
        # WARNINGS
        # ============================================================

        warning_rows = ""

        for warning in comparison["warnings"]:

            warning_rows += f"""
            <div class="warning-item">
                {warning}
            </div>
            """


        if not warning_rows:

            warning_rows = """
            <div class="no-warning">
                No run consistency warnings.
            </div>
            """

        # ========================================================
        # CATEGORY ACCURACY ROWS
        # ========================================================

        category_rows = ""

        for name, row in comparison["category_accuracy_delta"].items():
            delta = row["delta_pp"]
            css = "metric-good" if delta > 0 else "metric-bad" if delta < 0 else ""

            category_rows += f"""
            <tr>
                <td>{html.escape(name)}</td>
                <td>{row["baseline_accuracy"]:.2f}%</td>
                <td>{row["current_accuracy"]:.2f}%</td>
                <td class="{css}">{delta:+.2f} pp</td>
            </tr>
            """

        # ========================================================
        # IMPROVEMENT ROWS
        # ========================================================

        improvement_rows = ""

        for item in comparison["improvements"]:
            improvement_rows += f"""
            <tr>
                <td>{html.escape(item["id"])}</td>
                <td>{html.escape(item["expected_category"])}</td>
                <td>{html.escape(item["baseline_category"])}</td>
                <td>{html.escape(item["current_category"])}</td>
            </tr>
            """

        if not improvement_rows:
            improvement_rows = """
            <tr><td colspan="4">No improved cases.</td></tr>
            """


        # ========================================================
        # REGRESSED CASES: SIDE BY SIDE
        # ========================================================

        base_by_id = {r["id"]: r for r in (baseline or {}).get("results", [])}
        cur_by_id = {r["id"]: r for r in latest["results"]}
        texts = case_texts or {}

        regressed_ids = []
        for item in comparison["regressions"] + comparison["summary_regressions"]:
            if item["id"] not in regressed_ids:
                regressed_ids.append(item["id"])

        def side(label, run):
            mark = "✓" if run.get("category_correct") else "✗"
            return f"""
                <div>
                    <div class="stat-label">{label}</div>
                    <div><strong>{esc(run.get("actual_category") or "(error)")}</strong> {mark}</div>
                    <p>{esc(run.get("actual_summary") or "(no summary)")}</p>
                    <div class="small-text">
                        summary score {(run.get("summary_score") or 0.0):.4f}
                    </div>
                </div>
            """

        case_cards = ""

        if baseline is None:
            case_cards = "<p>Baseline run not provided, so summaries can't be compared.</p>"
        else:
            for case_id in regressed_ids:
                base = base_by_id.get(case_id)
                cur = cur_by_id.get(case_id)
                if base is None or cur is None:
                    continue

                case_cards += f"""
                <div class="case">
                    <h3>{esc(case_id)}
                        <span class="small-text">
                            expected: {esc(cur.get("expected_category"))}
                        </span>
                    </h3>
                    <pre class="email">{esc(texts.get(case_id, "(email text not available)"))}</pre>
                    <div class="small-text">
                        Expected summary: {esc(cur.get("expected_summary"))}
                    </div>
                    <div class="side-by-side">
                        {side("Baseline", base)}
                        {side("Current", cur)}
                    </div>
                </div>
                """

            if not case_cards:
                case_cards = "<p>No regressed cases.</p>"

        trend_svg = trend_chart_svg(
            load_trend_points(runs_dir, latest["model"], latest["total_cases"])
        )
        # ============================================================
        # HTML
        # ============================================================

        html_doc = f"""
        <!DOCTYPE html>
        <html lang="en">

        <head>

            <meta charset="UTF-8">

            <meta name="viewport"
                content="width=device-width, initial-scale=1.0">

            <title>ModelWatch Regression Report</title>

            <style>

                body {{
                    font-family: Arial, sans-serif;
                    background: #f5f7fa;
                    margin: 0;
                    padding: 40px;
                    color: #1f2937;
                }}


                .container {{
                    max-width: 1200px;
                    margin: auto;
                }}

                h1 {{
                    margin-bottom: 5px;
                }}

                h2 {{
                    margin-top: 0;
                    margin-bottom: 20px;
                }}

                h3 {{
                    margin-top: 25px;
                }}

                .case {{
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 16px;
                }}

                .email {{
                    background: #f9fafb;
                    padding: 12px;
                    border-radius: 6px;
                    white-space: pre-wrap;
                    font-family: inherit;
                    margin: 8px 0 12px;
                }}

                .side-by-side {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 12px;
                    margin-top: 12px;
                }}

                .side-by-side > div {{
                    background: #f9fafb;
                    padding: 12px;
                    border-radius: 6px;
                }}

                .subtitle {{
                    color: #6b7280;
                    margin-bottom: 30px;
                }}

                .status {{
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 25px;
                    font-size: 22px;
                    font-weight: bold;
                }}

                .pass {{
                    background: #dcfce7;
                    color: #166534;
                }}

                .warning {{
                    background: #fef3c7;
                    color: #92400e;
                }}

                .critical {{
                    background: #fee2e2;
                    color: #991b1b;
                }}

                .cards {{
                    display: grid;
                    grid-template-columns:
                        repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 30px;
                }}

                .card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow:
                        0 2px 8px rgba(0, 0, 0, 0.06);
                }}

                .card-title {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 8px;
                }}

                .card-value {{
                    font-size: 28px;
                    font-weight: bold;
                }}

                .section {{
                    background: white;
                    padding: 25px;
                    border-radius: 10px;
                    margin-bottom: 25px;
                    box-shadow:
                        0 2px 8px rgba(0, 0, 0, 0.06);
                }}

                table {{
                    width: 100%;
                    border-collapse: collapse;
                }}

                th,
                td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e5e7eb;
                }}

                th {{
                    background: #f9fafb;
                }}

                tr:last-child td {{
                    border-bottom: none;
                }}

                .metadata {{
                    display: grid;
                    grid-template-columns:
                        repeat(auto-fit, minmax(220px, 1fr));
                    gap: 10px;
                }}

                .metadata div {{
                    padding: 10px;
                    background: #f9fafb;
                    border-radius: 6px;
                }}

                .metric-good {{
                    color: #166534;
                    font-weight: bold;
                }}

                .metric-bad {{
                    color: #991b1b;
                    font-weight: bold;
                }}

                .metric-warning {{
                    color: #92400e;
                    font-weight: bold;
                }}

                .stat-box {{
                    display: grid;
                    grid-template-columns:
                        repeat(auto-fit, minmax(180px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}

                .stat {{
                    background: #f9fafb;
                    padding: 18px;
                    border-radius: 8px;
                }}

                .stat-label {{
                    color: #6b7280;
                    font-size: 13px;
                    margin-bottom: 6px;
                }}

                .stat-value {{
                    font-size: 22px;
                    font-weight: bold;
                }}

                .warning-box {{
                    background: #fffbeb;
                    border: 1px solid #fde68a;
                    padding: 18px;
                    border-radius: 8px;
                }}

                .warning-item {{
                    padding: 10px 0;
                    border-bottom: 1px solid #fde68a;
                }}

                .warning-item:last-child {{
                    border-bottom: none;
                }}

                .no-warning {{
                    color: #166534;
                    font-weight: bold;
                }}

                .small-text {{
                    color: #6b7280;
                    font-size: 13px;
                    margin-top: 10px;
                }}

            </style>

        </head>


        <body>

        <div class="container">

            <h1>ModelWatch</h1>

            <div class="subtitle">
                LLM Regression Detection Report
            </div>


            <!-- STATUS -->

            <div class="status {status_class}">
                STATUS: {status}
            </div>


            <!-- SUMMARY CARDS -->

            <div class="cards">

                <div class="card">
                    <div class="card-title">
                        Category Accuracy
                    </div>

                    <div class="card-value">
                        {latest["category_accuracy"] * 100:.2f}%
                    </div>
                </div>


                <div class="card">
                    <div class="card-title">
                        Summary Score
                    </div>

                    <div class="card-value">
                        {latest["average_summary_score"]:.4f}
                    </div>
                </div>


                <div class="card">
                    <div class="card-title">
                        Average Latency
                    </div>

                    <div class="card-value">
                        {latest["latency"]["average_ms"]:.2f} ms
                    </div>
                </div>


                <div class="card">
                    <div class="card-title">
                        P95 Latency
                    </div>

                    <div class="card-value">
                        {latest["latency"]["p95_ms"]:.2f} ms
                    </div>
                </div>


                <div class="card">
                    <div class="card-title">
                        Total Tokens
                    </div>

                    <div class="card-value">
                        {latest["tokens"]["total_tokens"]}
                    </div>
                </div>


                <div class="card">
                    <div class="card-title">
                        Category Regressions
                    </div>

                    <div class="card-value">
                        {comparison["regression_count"]}
                    </div>
                </div>

            </div>


            <!-- RUN INFORMATION -->

            <div class="section">

                <h2>Run Information</h2>

                <div class="metadata">

                    <div>
                        <strong>Run ID</strong><br>
                        {latest["run_id"]}
                    </div>

                    <div>
                        <strong>Timestamp</strong><br>
                        {latest["timestamp"]}
                    </div>

                    <div>
                        <strong>Prompt Version</strong><br>
                        {latest["prompt_version"]}
                    </div>

                    <div>
                        <strong>Model</strong><br>
                        {latest["model"]}
                    </div>

                    <div>
                        <strong>Dataset</strong><br>
                        {latest["dataset"]}
                    </div>

                    <div>
                        <strong>Total Cases</strong><br>
                        {latest["total_cases"]}
                    </div>

                </div>

            </div>

            <!-- TREND -->

            <div class="section">

                <h2>Accuracy Trend</h2>

                {trend_svg}

                <div class="small-text">
                    Category accuracy for past runs with the same model and
                    dataset size.
                </div>

            </div>


            <!-- BASELINE COMPARISON -->

            <div class="section">

                <h2>Baseline Comparison</h2>

                <table>

                    <tr>
                        <th>Metric</th>
                        <th>Baseline</th>
                        <th>Current</th>
                        <th>Change</th>
                    </tr>

                    <tr>

                        <td>Category Accuracy</td>

                        <td>
                            {comparison["baseline_accuracy"] * 100:.2f}%
                        </td>

                        <td>
                            {comparison["current_accuracy"] * 100:.2f}%
                        </td>

                        <td class="metric-warning">
                            {comparison["accuracy_change"] * 100:+.2f}%
                        </td>

                    </tr>


                    <tr>

                        <td>Average Summary Score</td>

                        <td>
                            {comparison["baseline_summary_score"]:.4f}
                        </td>

                        <td>
                            {comparison["current_summary_score"]:.4f}
                        </td>

                        <td class="metric-good">
                            {summary_change_display}
                        </td>

                    </tr>


                    <tr>

                        <td>P95 Latency</td>

                        <td>
                            {comparison["baseline_latency"]["p95_ms"]:.2f} ms
                        </td>

                        <td>
                            {comparison["current_latency"]["p95_ms"]:.2f} ms
                        </td>

                        <td>
                            {latency_increase}
                        </td>

                    </tr>

                </table>

            </div>

        <!-- CATEGORY ACCURACY -->

        <div class="section">

            <h2>Accuracy by Category</h2>

            <table>
                <tr>
                    <th>Category</th>
                    <th>Baseline</th>
                    <th>Current</th>
                    <th>Change</th>
                </tr>

                {category_rows}
            </table>

            <div class="small-text">
                Each category holds only a handful of cases, so one flipped
                case can move these percentages a lot.
            </div>

        </div>


            <!-- MCNEMAR -->

            <div class="section">

                <h2>McNemar Statistical Test</h2>

                <p>
                    McNemar's exact test evaluates whether the change
                    in category correctness between the baseline and
                    current model is statistically significant.
                </p>


                <div class="stat-box">

                    <div class="stat">
                        <div class="stat-label">
                            Paired Cases
                        </div>

                        <div class="stat-value">
                            {mcnemar["n_paired"]}
                        </div>
                    </div>


                    <div class="stat">
                        <div class="stat-label">
                            Baseline Correct → Current Wrong
                        </div>

                        <div class="stat-value">
                            {mcnemar["regressions"]}
                        </div>
                    </div>


                    <div class="stat">
                        <div class="stat-label">
                            Baseline Wrong → Current Correct
                        </div>

                        <div class="stat-value">
                            {mcnemar["improvements"]}
                        </div>
                    </div>


                    <div class="stat">
                        <div class="stat-label">
                            Direction
                        </div>

                        <div class="stat-value">
                            {mcnemar["direction"].capitalize()}
                        </div>
                    </div>


                    <div class="stat">
                        <div class="stat-label">
                            P-Value
                        </div>

                        <div class="stat-value">
                            {mcnemar["p_value"]:.4f}
                        </div>
                    </div>


                    <div class="stat">
                        <div class="stat-label">
                            Significance Level
                        </div>

                        <div class="stat-value">
                            α = {mcnemar["alpha"]}
                        </div>
                    </div>

                </div>


                <table>

                    <tr>
                        <th>Test Result</th>
                        <th>Result</th>
                    </tr>

                    <tr>
                        <td>Statistically Significant</td>

                        <td>
                            <strong>
                                {mcnemar_significance}
                            </strong>
                        </td>
                    </tr>

                    <tr>
                        <td>Significant Regression</td>

                        <td>
                            <strong>
                                {significant_regression}
                            </strong>
                        </td>
                    </tr>

                </table>


                <div class="small-text">
                    A p-value below 0.05 indicates statistically
                    significant evidence of a change in paired
                    classification outcomes.
                </div>

            </div>


            <!-- SUMMARY QUALITY -->

            <div class="section">

                <h2>Summary Quality Analysis</h2>


                <div class="stat-box">

                    <div class="stat">

                        <div class="stat-label">
                            Baseline Average Score
                        </div>

                        <div class="stat-value">
                            {comparison["baseline_summary_score"]:.4f}
                        </div>

                    </div>


                    <div class="stat">

                        <div class="stat-label">
                            Current Average Score
                        </div>

                        <div class="stat-value">
                            {comparison["current_summary_score"]:.4f}
                        </div>

                    </div>


                    <div class="stat">

                        <div class="stat-label">
                            Score Change
                        </div>

                        <div class="stat-value">
                            {summary_change_display}
                        </div>

                    </div>


                    <div class="stat">

                        <div class="stat-label">
                            Individual Regressions
                        </div>

                        <div class="stat-value">
                            {comparison["summary_regression_count"]}
                        </div>

                    </div>

                </div>


                <h3>Summary Regressions</h3>


                <table>

                    <tr>
                        <th>Case</th>
                        <th>Baseline Score</th>
                        <th>Current Score</th>
                        <th>Drop</th>
                    </tr>

                    {summary_regression_rows}

                </table>

            </div>


            <!-- LATENCY ANALYSIS -->

            <div class="section">

                <h2>Latency Analysis</h2>

                <table>

                    <tr>
                        <th>Metric</th>
                        <th>Baseline</th>
                        <th>Current</th>
                    </tr>


                    <tr>

                        <td>P95 Latency</td>

                        <td>
                            {comparison["baseline_latency"]["p95_ms"]:.2f} ms
                        </td>

                        <td>
                            {comparison["current_latency"]["p95_ms"]:.2f} ms
                        </td>

                    </tr>


                    <tr>

                        <td>P95 Increase</td>

                        <td colspan="2">
                            {latency_increase}
                        </td>

                    </tr>


                    <tr>

                        <td>Regression Threshold</td>

                        <td colspan="2">
                            {latency_threshold}
                        </td>

                    </tr>


                    <tr>

                        <td>Latency Regression</td>

                        <td colspan="2">
                            <strong>
                                {latency_status}
                            </strong>
                        </td>

                    </tr>

                </table>

            </div>


            <!-- FULL LATENCY -->

            <div class="section">

                <h2>Latency Metrics</h2>

                <table>

                    <tr>
                        <th>Metric</th>
                        <th>Latency</th>
                    </tr>


                    <tr>
                        <td>Minimum</td>

                        <td>
                            {latest["latency"]["minimum_ms"]:.2f} ms
                        </td>
                    </tr>


                    <tr>
                        <td>Average</td>

                        <td>
                            {latest["latency"]["average_ms"]:.2f} ms
                        </td>
                    </tr>


                    <tr>
                        <td>P50</td>

                        <td>
                            {latest["latency"]["p50_ms"]:.2f} ms
                        </td>
                    </tr>


                    <tr>
                        <td>P95</td>

                        <td>
                            {latest["latency"]["p95_ms"]:.2f} ms
                        </td>
                    </tr>


                    <tr>
                        <td>Maximum</td>

                        <td>
                            {latest["latency"]["maximum_ms"]:.2f} ms
                        </td>
                    </tr>

                </table>

            </div>


            <!-- TOKEN USAGE -->

            <div class="section">

                <h2>Token Usage</h2>

                <table>

                    <tr>
                        <th>Metric</th>
                        <th>Tokens</th>
                    </tr>


                    <tr>
                        <td>Total Prompt Tokens</td>

                        <td>
                            {latest["tokens"]["total_prompt_tokens"]}
                        </td>
                    </tr>


                    <tr>
                        <td>Total Generated Tokens</td>

                        <td>
                            {latest["tokens"]["total_generated_tokens"]}
                        </td>
                    </tr>


                    <tr>
                        <td>Total Tokens</td>

                        <td>
                            {latest["tokens"]["total_tokens"]}
                        </td>
                    </tr>


                    <tr>
                        <td>Average Total Tokens</td>

                        <td>
                            {latest["tokens"]["average_total_tokens"]:.2f}
                        </td>
                    </tr>

                </table>

            </div>


            <!-- CATEGORY REGRESSIONS -->

            <div class="section">

                <h2>Category Regressions</h2>

                <table>

                    <tr>
                        <th>Case</th>
                        <th>Expected</th>
                        <th>Baseline</th>
                        <th>Current</th>
                        <th>Latency</th>
                    </tr>

                    {regression_rows}

                </table>

            </div>    
            
            <!-- REGRESSED CASES: SIDE BY SIDE -->

            <div class="section">

                <h2>Regressed Cases: Baseline vs Current</h2>

                {case_cards}

            </div>

            <!-- IMPROVEMENTS -->

            <div class="section">

                <h2>Improved Cases ({comparison["improvement_count"]})</h2>

                <table>
                    <tr>
                        <th>Case</th>
                        <th>Expected</th>
                        <th>Baseline</th>
                        <th>Current</th>
                    </tr>

                    {improvement_rows}
                </table>

            </div>




            <!-- WARNINGS -->

            <div class="section">

                <h2>Warnings</h2>

                <div class="warning-box">

                    {warning_rows}

                </div>

            </div>


            <!-- FINAL ANALYSIS -->

            <div class="section">

                <h2>Final Analysis</h2>

                <table>

                    <tr>
                        <th>Condition</th>
                        <th>Result</th>
                    </tr>


                    <tr>
                        <td>Category Accuracy Drop</td>

                        <td>
                            {comparison["accuracy_drop"] * 100:.2f}%
                        </td>
                    </tr>


                    <tr>
                        <td>Category Regression Count</td>

                        <td>
                            {comparison["regression_count"]}
                        </td>
                    </tr>


                    <tr>
                        <td>Summary Regression Count</td>

                        <td>
                            {comparison["summary_regression_count"]}
                        </td>
                    </tr>


                    <tr>
                        <td>McNemar Direction</td>

                        <td>
                            {mcnemar["direction"].capitalize()}
                        </td>
                    </tr>


                    <tr>
                        <td>McNemar P-Value</td>

                        <td>
                            {mcnemar["p_value"]:.4f}
                        </td>
                    </tr>


                    <tr>
                        <td>Statistically Significant</td>

                        <td>
                            {mcnemar_significance}
                        </td>
                    </tr>


                    <tr>
                        <td>Latency Regression</td>

                        <td>
                            {latency_status}
                        </td>
                    </tr>


                    <tr>
                        <td>Overall ModelWatch Status</td>

                        <td>
                            <strong>
                                {status}
                            </strong>
                        </td>
                    </tr>

                </table>

            </div>

        </div>

        </body>

        </html>
        """

        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(html_doc, encoding="utf-8")
        return html_doc


def main() -> None:
    latest = load_json("results/latest.json")
    comparison = load_json("results/comparison.json")
    baseline = load_json("results/baseline.json")
    dataset = load_json("datasets/golden_dataset.json")
    case_texts = {c["id"]: c["input"]["text"] for c in dataset["cases"]}

    generate_report(latest, comparison, "results/report.html", baseline, case_texts)
    print("HTML report generated at results/report.html")


if __name__ == "__main__":
    main()