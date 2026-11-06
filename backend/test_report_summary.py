from backend.report_summary import markdown_summary


def make(**overrides):
    base = {
        "status": "PASS",
        "baseline_accuracy": 0.62,
        "current_accuracy": 0.68,
        "accuracy_change": 0.06,
        "regression_count": 0,
        "regressions": [],
        "summary_regression_count": 0,
        "latency_regression": None,
        "warnings": [],
        "mcnemar": {"direction": "improvement", "p_value": 0.4531, "significant": False},
    }
    base.update(overrides)
    return base


def test_pass_summary_has_status_and_accuracy():
    text = markdown_summary(make())
    assert "PASS" in text
    assert "62.0% → 68.0%" in text
    assert "Regressed cases" not in text


def test_regressed_cases_are_listed_and_truncated():
    regs = [
        {"id": f"TC{i:03d}", "expected_category": "billing",
         "baseline_category": "billing", "current_category": "technical"}
        for i in range(1, 8)
    ]
    text = markdown_summary(make(status="CRITICAL", regression_count=7, regressions=regs))
    assert "`TC001`" in text
    assert "and 2 more" in text


def test_latency_line_only_when_regression_present():
    assert "Latency" not in markdown_summary(make())
    text = markdown_summary(make(latency_regression={"increase_pct": 46.25, "threshold_pct": 30.0}))
    assert "46.2% " in text or "46.3% " in text


def test_warnings_are_included():
    assert "dataset differs" in markdown_summary(make(warnings=["dataset differs"]))