STATUS_ICON = {"PASS": "✅", "WARNING": "⚠️", "CRITICAL": "🚨"}


def markdown_summary(comparison: dict, max_cases: int = 5) -> str:
    """Short markdown summary, reusable for a PR comment or a Slack message."""
    status = comparison["status"]
    m = comparison["mcnemar"]

    lines = [
        f"### ModelWatch: {STATUS_ICON.get(status, '')} {status}",
        "",
        (
            f"- **Accuracy:** {comparison['baseline_accuracy'] * 100:.1f}% → "
            f"{comparison['current_accuracy'] * 100:.1f}% "
            f"({comparison['accuracy_change'] * 100:+.1f} pts)"
        ),
        f"- **Category regressions:** {comparison['regression_count']}",
    ]

    improvements = comparison.get("improvements")
    if improvements is not None:
        count = len(improvements) if isinstance(improvements, list) else improvements
        lines.append(f"- **Improved cases:** {count}")

    lines.append(
        f"- **McNemar:** {m['direction']}, p = {m['p_value']:.4f} "
        f"({'significant' if m['significant'] else 'not significant'})"
    )
    lines.append(f"- **Summary regressions:** {comparison['summary_regression_count']}")

    latency = comparison.get("latency_regression")
    if latency is not None:
        lines.append(
            f"- **Latency:** P95 up {latency['increase_pct']:.1f}% "
            f"(threshold {latency['threshold_pct']:.1f}%)"
        )

    regressions = comparison["regressions"]
    if regressions:
        lines += ["", "**Regressed cases**", ""]
        for r in regressions[:max_cases]:
            lines.append(
                f"- `{r['id']}`: expected {r['expected_category']}, "
                f"{r['baseline_category']} → {r['current_category']}"
            )
        if len(regressions) > max_cases:
            lines.append(f"- …and {len(regressions) - max_cases} more")

    for warning in comparison["warnings"]:
        lines.append(f"\n> ⚠️ {warning}")

    return "\n".join(lines)