import json
from html import escape
from pathlib import Path


def load_trend_points(
    runs_dir: str,
    model: str,
    total_cases: int,
    limit: int = 20,
) -> list[dict]:
    """Accuracy per past run, oldest first.

    Only runs with the same model and dataset size are included, because
    accuracy on a 15-case dataset or a different model isn't comparable.
    """
    points = []

    for path in Path(runs_dir).glob("*.json"):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if run.get("model") != model or run.get("total_cases") != total_cases:
            continue
        if "category_accuracy" not in run or "timestamp" not in run:
            continue

        points.append(
            {
                "timestamp": run["timestamp"],
                "label": run.get("prompt_version", "?"),
                "accuracy": run["category_accuracy"] * 100,
            }
        )

    points.sort(key=lambda p: p["timestamp"])
    return points[-limit:]


def trend_chart_svg(points: list[dict], width: int = 700, height: int = 240) -> str:
    if len(points) < 2:
        return (
            "<p class='small-text'>Not enough runs for a trend yet "
            "(needs at least 2 runs with the same model and dataset size).</p>"
        )

    pad_l, pad_r, pad_t, pad_b = 44, 16, 16, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    n = len(points)

    def x(i: int) -> float:
        return pad_l + plot_w * i / (n - 1)

    def y(accuracy: float) -> float:
        return pad_t + plot_h * (1 - accuracy / 100)

    grid = ""
    for tick in (0, 25, 50, 75, 100):
        grid += (
            f'<line x1="{pad_l}" y1="{y(tick):.1f}" '
            f'x2="{width - pad_r}" y2="{y(tick):.1f}" stroke="#e5e7eb"/>'
            f'<text x="{pad_l - 6}" y="{y(tick) + 4:.1f}" font-size="11" '
            f'text-anchor="end" fill="#6b7280">{tick}%</text>'
        )

    coords = " ".join(
        f"{x(i):.1f},{y(p['accuracy']):.1f}" for i, p in enumerate(points)
    )

    dots = ""
    for i, p in enumerate(points):
        label = escape(str(p["label"]))
        dots += (
            f'<circle cx="{x(i):.1f}" cy="{y(p["accuracy"]):.1f}" r="4" fill="#2563eb">'
            f'<title>{label}: {p["accuracy"]:.1f}%</title></circle>'
            f'<text x="{x(i):.1f}" y="{height - 18}" font-size="10" '
            f'text-anchor="middle" fill="#6b7280">{label}</text>'
        )

    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="Category accuracy per run">'
        f"{grid}"
        f'<polyline points="{coords}" fill="none" stroke="#2563eb" stroke-width="2"/>'
        f"{dots}</svg>"
    )