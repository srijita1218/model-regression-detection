import json

from backend.report_trend import load_trend_points, trend_chart_svg


def write_run(folder, name, **fields):
    (folder / f"{name}.json").write_text(json.dumps(fields))


def test_only_matching_model_and_size_are_included(tmp_path):
    write_run(tmp_path, "a", model="m1", total_cases=50,
              category_accuracy=0.6, timestamp="2026-10-01T10:00:00", prompt_version="v1")
    write_run(tmp_path, "b", model="m1", total_cases=50,
              category_accuracy=0.7, timestamp="2026-10-02T10:00:00", prompt_version="v2")
    write_run(tmp_path, "old", model="llama2", total_cases=15,
              category_accuracy=0.9, timestamp="2026-08-01T10:00:00", prompt_version="v1")

    points = load_trend_points(str(tmp_path), "m1", 50)

    assert [p["label"] for p in points] == ["v1", "v2"]
    assert points[1]["accuracy"] == 70


def test_corrupt_files_are_skipped(tmp_path):
    (tmp_path / "bad.json").write_text("not json")
    assert load_trend_points(str(tmp_path), "m1", 50) == []


def test_chart_needs_two_points():
    assert "Not enough runs" in trend_chart_svg([])
    assert "Not enough runs" in trend_chart_svg([{"timestamp": "t", "label": "v1", "accuracy": 50}])


def test_chart_renders_svg_and_escapes_labels():
    pts = [
        {"timestamp": "1", "label": "<b>", "accuracy": 60},
        {"timestamp": "2", "label": "v2", "accuracy": 70},
    ]
    svg = trend_chart_svg(pts)
    assert svg.startswith("<svg")
    assert "<b>" not in svg
    assert "&lt;b&gt;" in svg