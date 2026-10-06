"""
1. Load results
2. Find individual regressions
3. Run McNemar's statistical test
4. Compare the two runs and produce final result
"""

import json

from backend.regression import calculate_mcnemar, compare_runs


def make_result(case_id: str, correct: bool) -> dict:
    return {
        "id": case_id,
        "category_correct": correct,
    }


def test_mcnemar_no_change():
    baseline = [
        make_result("TC001", True),
        make_result("TC002", False),
        make_result("TC003", True),
        make_result("TC004", False),
    ]

    current = [
        make_result("TC001", True),
        make_result("TC002", False),
        make_result("TC003", True),
        make_result("TC004", False),
    ]

    result = calculate_mcnemar(
        baseline,
        current,
    )

    assert result["regressions"] == 0
    assert result["improvements"] == 0
    assert result["p_value"] == 1.0
    assert result["significant"] is False


def test_mcnemar_significant_drop():
    baseline = [
        make_result(f"TC{i:03d}", True)
        for i in range(1, 11)
    ]

    current = [
        make_result(f"TC{i:03d}", False)
        for i in range(1, 11)
    ]

    result = calculate_mcnemar(
        baseline,
        current,
    )

    assert result["regressions"] == 10
    assert result["improvements"] == 0
    assert result["p_value"] < 0.05
    assert result["significant"] is True


def test_mcnemar_small_non_significant_change():
    baseline = [
        make_result("TC001", True),
        make_result("TC002", True),
        make_result("TC003", False),
        make_result("TC004", False),
    ]

    current = [
        make_result("TC001", False),
        make_result("TC002", True),
        make_result("TC003", True),
        make_result("TC004", False),
    ]

    result = calculate_mcnemar(
        baseline,
        current,
    )

    assert result["regressions"] == 1
    assert result["improvements"] == 1
    assert result["p_value"] >= 0.05
    assert result["significant"] is False


def make_run(flags: list) -> list:
    return [
        make_result(f"TC{i:03d}", flag)
        for i, flag in enumerate(flags, start=1)
    ]


def test_mcnemar_small_drop_not_significant():
    # 3 regressions, 0 improvements: real drop, but p = 0.25
    baseline = make_run([True, True, True, True, False])
    current = make_run([False, False, False, True, False])

    result = calculate_mcnemar(baseline, current)

    assert result["regressions"] == 3
    assert result["improvements"] == 0
    assert result["p_value"] == 0.25
    assert result["significant"] is False
    assert result["direction"] == "regression"
    assert result["significant_regression"] is False


def test_mcnemar_direction_regression():
    result = calculate_mcnemar(
        make_run([True] * 10),
        make_run([False] * 10),
    )

    assert result["direction"] == "regression"
    assert result["significant_regression"] is True


def test_mcnemar_significant_improvement_is_not_regression():
    result = calculate_mcnemar(
        make_run([False] * 10),
        make_run([True] * 10),
    )

    assert result["significant"] is True
    assert result["direction"] == "improvement"
    assert result["significant_regression"] is False


def test_mcnemar_no_change_direction():
    flags = [True, False, True, False]

    result = calculate_mcnemar(make_run(flags), make_run(flags))

    assert result["direction"] == "none"
    assert result["significant_regression"] is False
    assert result["n_paired"] == 4
    assert result["only_in_baseline"] == 0
    assert result["only_in_current"] == 0


def test_mcnemar_reports_unmatched_ids():
    result = calculate_mcnemar(
        make_run([True] * 3),
        make_run([True] * 5),
    )

    assert result["n_paired"] == 3
    assert result["only_in_baseline"] == 0
    assert result["only_in_current"] == 2


# --- compare_runs end to end -----------------------------------


def write_run(path, flags: list) -> None:
    results = [
        {
            "id": f"TC{i:03d}",
            "category_correct": flag,
            "expected_category": "billing",
            "actual_category": "billing" if flag else "other",
            "latency_ms": 100.0,
        }
        for i, flag in enumerate(flags, start=1)
    ]

    path.write_text(
        json.dumps(
            {
                "category_accuracy": sum(flags) / len(flags),
                "results": results,
            }
        ),
        encoding="utf-8",
    )


def test_compare_runs_critical(tmp_path):
    write_run(tmp_path / "base.json", [True] * 10)
    write_run(tmp_path / "cur.json", [False] * 10)

    result = compare_runs(
        str(tmp_path / "base.json"),
        str(tmp_path / "cur.json"),
    )

    assert result["status"] == "CRITICAL"
    assert result["regression_count"] == 10
    assert result["mcnemar"]["significant_regression"] is True
    assert result["warnings"] == []


def test_compare_runs_pass_when_identical(tmp_path):
    flags = [True, False, True, True]
    write_run(tmp_path / "base.json", flags)
    write_run(tmp_path / "cur.json", flags)

    result = compare_runs(
        str(tmp_path / "base.json"),
        str(tmp_path / "cur.json"),
    )

    assert result["status"] == "PASS"
    assert result["regression_count"] == 0


def test_compare_runs_warns_on_mismatched_cases(tmp_path):
    write_run(tmp_path / "base.json", [True] * 3)
    write_run(tmp_path / "cur.json", [True] * 5)

    result = compare_runs(
        str(tmp_path / "base.json"),
        str(tmp_path / "cur.json"),
    )

    assert len(result["warnings"]) == 1