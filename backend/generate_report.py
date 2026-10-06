import json


def load_json(path: str) -> dict:
    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


latest = load_json(
    "results/latest.json"
)

comparison = load_json(
    "results/comparison.json"
)


status = comparison["status"]

status_class = status.lower()


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
            No individual regressions detected.
        </td>
    </tr>
    """


html = f"""
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
            max-width: 1100px;
            margin: auto;
        }}

        h1 {{
            margin-bottom: 5px;
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

    </style>

</head>


<body>

<div class="container">

    <h1>ModelWatch</h1>

    <div class="subtitle">
        LLM Regression Detection Report
    </div>


    <div class="status {status_class}">
        STATUS: {status}
    </div>


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
                Regressions
            </div>

            <div class="card-value">
                {comparison["regression_count"]}
            </div>
        </div>

    </div>


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


    <div class="section">

        <h2>Baseline Comparison</h2>

        <table>

            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>

            <tr>
                <td>Baseline Accuracy</td>
                <td>
                    {comparison["baseline_accuracy"] * 100:.2f}%
                </td>
            </tr>

            <tr>
                <td>Current Accuracy</td>
                <td>
                    {comparison["current_accuracy"] * 100:.2f}%
                </td>
            </tr>

            <tr>
                <td>Accuracy Change</td>
                <td>
                    {comparison["accuracy_change"] * 100:.2f}%
                </td>
            </tr>

            <tr>
                <td>Accuracy Drop</td>
                <td>
                    {comparison["accuracy_drop"] * 100:.2f}%
                </td>
            </tr>

        </table>

    </div>


    <div class="section">

        <h2>Latency Metrics</h2>

        <table>

            <tr>
                <th>Metric</th>
                <th>Latency</th>
            </tr>

            <tr>
                <td>Minimum</td>
                <td>{latest["latency"]["minimum_ms"]:.2f} ms</td>
            </tr>

            <tr>
                <td>Average</td>
                <td>{latest["latency"]["average_ms"]:.2f} ms</td>
            </tr>

            <tr>
                <td>P50</td>
                <td>{latest["latency"]["p50_ms"]:.2f} ms</td>
            </tr>

            <tr>
                <td>P95</td>
                <td>{latest["latency"]["p95_ms"]:.2f} ms</td>
            </tr>

            <tr>
                <td>Maximum</td>
                <td>{latest["latency"]["maximum_ms"]:.2f} ms</td>
            </tr>

        </table>

    </div>


    <div class="section">

        <h2>Token Usage</h2>

        <table>

            <tr>
                <th>Metric</th>
                <th>Tokens</th>
            </tr>

            <tr>
                <td>Total Prompt Tokens</td>
                <td>{latest["tokens"]["total_prompt_tokens"]}</td>
            </tr>

            <tr>
                <td>Total Generated Tokens</td>
                <td>{latest["tokens"]["total_generated_tokens"]}</td>
            </tr>

            <tr>
                <td>Total Tokens</td>
                <td>{latest["tokens"]["total_tokens"]}</td>
            </tr>

            <tr>
                <td>Average Total Tokens</td>
                <td>{latest["tokens"]["average_total_tokens"]:.2f}</td>
            </tr>

        </table>

    </div>


    <div class="section">

        <h2>Regressed Cases</h2>

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

</div>

</body>

</html>
"""


with open(
    "results/report.html",
    "w",
    encoding="utf-8",
) as file:

    file.write(html)


print(
    "HTML report generated at results/report.html"
)