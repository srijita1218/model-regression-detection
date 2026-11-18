import json
from pathlib import Path
import pytest

import backend.compare_runs as compare_cli
import backend.run_evaluation as eval_cli


@pytest.fixture
def fake_runs(tmp_path):
    """Create sample baseline, pass, warning, and critical evaluation JSON files."""
    def make_run(accuracy, run_id, correct_count, total=10, error=None):
        results = []
        for i in range(1, total + 1):
            is_ok = i <= correct_count
            results.append({
                "id": f"TC{i:03d}",
                "expected_category": "billing",
                "actual_category": "billing" if is_ok else "technical",
                "category_correct": is_ok,
                "summary_score": 0.8 if is_ok else 0.4,
                "latency_ms": 100.0,
                "error": error,
            })
        return {
            "run_id": run_id,
            "timestamp": "2026-11-18T10:00:00",
            "prompt_version": run_id,
            "model": "llama3.2:3b",
            "dataset": "golden_dataset.json",
            "dataset_version": "2.0",
            "total_cases": total,
            "correct_categories": correct_count,
            "category_accuracy": accuracy,
            "average_summary_score": 0.7,
            "latency": {"p95_ms": 150.0, "minimum_ms": 50.0, "average_ms": 100.0, "p50_ms": 90.0, "maximum_ms": 200.0},
            "tokens": {
                "total_tokens": 1000,
                "total_prompt_tokens": 800,
                "total_generated_tokens": 200,
                "average_prompt_tokens": 80.0,
                "average_generated_tokens": 20.0,
                "average_total_tokens": 100.0,
            },
            "status": "COMPLETED",
            "results": results,
        }

    base = make_run(0.9, "base", 9)
    # 9 correct -> 9 correct = PASS (0% drop)
    pass_run = make_run(0.9, "pass", 9)
    # 9 correct -> 8 correct = drop of 0.10 (>= 0.08 critical threshold) -> CRITICAL
    crit_run = make_run(0.7, "crit", 7)
    # 9 correct -> 8 correct on 50 cases would be warning, but on 10 cases let's check
    # Let's write them:
    base_file = tmp_path / "baseline.json"
    pass_file = tmp_path / "pass.json"
    crit_file = tmp_path / "crit.json"

    base_file.write_text(json.dumps(base))
    pass_file.write_text(json.dumps(pass_run))
    crit_file.write_text(json.dumps(crit_run))

    return base_file, pass_file, crit_file


def test_compare_runs_cli_flags_parsing():
    parser = compare_cli.build_parser()
    args = parser.parse_args(["-b", "base.json", "-c", "cur.json", "-o", "out.json", "-r", "--report-output", "rep.html"])
    assert args.baseline == "base.json"
    assert args.current == "cur.json"
    assert args.output == "out.json"
    assert args.report is True
    assert args.report_output == "rep.html"


def test_compare_runs_cli_positional_fallback():
    parser = compare_cli.build_parser()
    args = parser.parse_args(["base_pos.json", "cur_pos.json"])
    assert args.baseline_pos == "base_pos.json"
    assert args.current_pos == "cur_pos.json"


def test_compare_runs_exit_code_zero_on_pass(fake_runs, tmp_path):
    base_file, pass_file, _ = fake_runs
    out_comparison = tmp_path / "comp.json"
    exit_code = compare_cli.main(["-b", str(base_file), "-c", str(pass_file), "-o", str(out_comparison)])
    assert exit_code == 0
    assert out_comparison.exists()
    comp_data = json.loads(out_comparison.read_text())
    assert comp_data["status"] == "PASS"


def test_compare_runs_exit_code_one_on_critical(fake_runs, tmp_path):
    base_file, _, crit_file = fake_runs
    out_comparison = tmp_path / "comp.json"
    exit_code = compare_cli.main(["-b", str(base_file), "-c", str(crit_file), "-o", str(out_comparison)])
    assert exit_code == 1
    comp_data = json.loads(out_comparison.read_text())
    assert comp_data["status"] == "CRITICAL"


def test_compare_runs_generates_report(fake_runs, tmp_path):
    base_file, _, crit_file = fake_runs
    out_comparison = tmp_path / "comp.json"
    report_file = tmp_path / "report.html"

    exit_code = compare_cli.main([
        "-b", str(base_file),
        "-c", str(crit_file),
        "-o", str(out_comparison),
        "--report",
        "--report-output", str(report_file),
    ])
    assert exit_code == 1
    assert report_file.exists()
    assert "STATUS: CRITICAL" in report_file.read_text()


def test_run_evaluation_cli_flags_parsing():
    parser = eval_cli.build_parser()
    args = parser.parse_args([
        "-p", "prompts/v1.yaml",
        "-d", "datasets/custom.json",
        "-o", "results/custom.json",
        "-c", "results/baseline.json",
        "-r",
        "--report-output", "out.html",
    ])
    assert args.prompt == "prompts/v1.yaml"
    assert args.dataset == "datasets/custom.json"
    assert args.output == "results/custom.json"
    assert args.compare == "results/baseline.json"
    assert args.report is True
    assert args.report_output == "out.html"


def test_run_evaluation_cli_positional_fallback():
    parser = eval_cli.build_parser()
    args = parser.parse_args(["prompts/v2.yaml", "results/pos.json"])
    assert args.prompt_pos == "prompts/v2.yaml"
    assert args.output_pos == "results/pos.json"


def test_run_evaluation_cli_missing_prompt_fails():
    parser = eval_cli.build_parser()
    with pytest.raises(SystemExit):
        eval_cli.main([])


def test_run_evaluation_with_mocked_evaluator(tmp_path, monkeypatch):
    out_file = tmp_path / "eval_out.json"
    dataset_file = tmp_path / "data.json"
    dataset_file.write_text(json.dumps({"dataset_version": "v1.0", "cases": []}))

    mock_result = {
        "total_cases": 2,
        "correct_categories": 2,
        "category_accuracy": 1.0,
        "average_summary_score": 0.8,
        "latency": {"minimum_ms": 10, "average_ms": 20, "p50_ms": 20, "p95_ms": 25, "maximum_ms": 30},
        "tokens": {"total_prompt_tokens": 10, "total_generated_tokens": 10, "total_tokens": 20, "average_prompt_tokens": 5, "average_generated_tokens": 5, "average_total_tokens": 10},
        "results": [
            {"id": "TC001", "category_correct": True, "error": None},
            {"id": "TC002", "category_correct": True, "error": None},
        ],
    }

    monkeypatch.setattr(eval_cli, "evaluate_dataset", lambda d, p: mock_result.copy())
    monkeypatch.setattr(eval_cli, "save_run", lambda r: r)

    exit_code = eval_cli.main([
        "-p", "prompts/v1.yaml",
        "-d", str(dataset_file),
        "-o", str(out_file),
    ])

    assert exit_code == 0
    assert out_file.exists()
    saved = json.loads(out_file.read_text())
    assert saved["prompt_version"] == "v1"
    assert saved["dataset_version"] == "v1.0"
    assert saved["status"] == "COMPLETED"


def test_run_evaluation_unified_compare_and_report_critical(tmp_path, monkeypatch, fake_runs):
    base_file, _, crit_file = fake_runs
    dataset_file = tmp_path / "data.json"
    dataset_file.write_text(json.dumps({"dataset_version": "2.0", "cases": []}))

    eval_out = tmp_path / "eval_latest.json"
    report_out = tmp_path / "report_out.html"

    # Mocks evaluator returning crit_file contents
    crit_data = json.loads(crit_file.read_text())
    monkeypatch.setattr(eval_cli, "evaluate_dataset", lambda d, p: crit_data.copy())
    monkeypatch.setattr(eval_cli, "save_run", lambda r: r)

    # Calling main with --compare and --report
    exit_code = eval_cli.main([
        "-p", "prompts/v3.yaml",
        "-d", str(dataset_file),
        "-o", str(eval_out),
        "-c", str(base_file),
        "-r",
        "--report-output", str(report_out),
    ])

    # Status is CRITICAL, so exit code must be 1
    assert exit_code == 1
    assert eval_out.exists()
    assert report_out.exists()
    assert "STATUS: CRITICAL" in report_out.read_text()


def test_compare_runs_exit_code_zero_on_warning(tmp_path, monkeypatch):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"
    baseline.write_text("{}")
    current.write_text("{}")

    monkeypatch.setattr(
        compare_cli,
        "run_comparison",
        lambda **kwargs: {"status": "WARNING"},
    )

    exit_code = compare_cli.main([
        "-b", str(baseline),
        "-c", str(current),
    ])

    assert exit_code == 0


def test_compare_runs_missing_current_returns_two(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"
    baseline.write_text("{}")
    missing_current = tmp_path / "missing.json"

    exit_code = compare_cli.main([
        "-b", str(baseline),
        "-c", str(missing_current),
    ])

    assert exit_code == 2
    assert "Current file not found" in capsys.readouterr().err


def test_compare_runs_invalid_json_returns_two(tmp_path, capsys):
    baseline = tmp_path / "baseline.json"
    current = tmp_path / "current.json"

    baseline.write_text("{invalid json")
    current.write_text("{}")

    exit_code = compare_cli.main([
        "-b", str(baseline),
        "-c", str(current),
    ])

    assert exit_code == 2
    assert "Error:" in capsys.readouterr().err
