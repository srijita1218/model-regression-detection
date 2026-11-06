import pytest

from backend.regression import determine_status

NO_SIGNIFICANT = {"significant_regression": False}
SIGNIFICANT_REGRESSION = {"significant_regression": True}
LATENCY_REGRESSION = {"regression": True, "increase_pct": 46.25, "threshold_pct": 30.0}


def status(
    accuracy_drop=0.0,
    summary_regression_count=0,
    latency_regression=None,
    mcnemar_result=NO_SIGNIFICANT,
    summary_score_change=0.0,
):
    return determine_status(
        accuracy_drop=accuracy_drop,
        summary_regression_count=summary_regression_count,
        latency_regression=latency_regression,
        mcnemar_result=mcnemar_result,
        summary_score_change=summary_score_change,
    )


def test_clean_run_passes():
    assert status() == "PASS"


def test_improved_run_with_latency_regression_is_warning_not_critical():
    # the v2 bug: accuracy up, latency +46%, must never be CRITICAL
    assert status(latency_regression=LATENCY_REGRESSION) == "WARNING"


def test_small_accuracy_drop_below_warning_threshold_passes():
    assert status(accuracy_drop=0.02) == "PASS"


def test_accuracy_drop_at_warning_threshold_warns():
    assert status(accuracy_drop=0.03) == "WARNING"


def test_accuracy_drop_at_critical_threshold_is_critical():
    assert status(accuracy_drop=0.08) == "CRITICAL"


def test_significant_regression_is_critical_even_with_small_drop():
    assert status(accuracy_drop=0.01, mcnemar_result=SIGNIFICANT_REGRESSION) == "CRITICAL"


def test_latency_regression_alone_does_not_hide_a_critical_drop():
    assert status(accuracy_drop=0.10, latency_regression=LATENCY_REGRESSION) == "CRITICAL"


def test_summary_regressions_warn():
    assert status(summary_regression_count=2) == "WARNING"


def test_falling_average_summary_score_warns():
    assert status(summary_score_change=-0.05) == "WARNING"


def test_missing_summary_score_change_is_ignored():
    assert status(summary_score_change=None) == "PASS"


def test_thresholds_can_be_overridden_by_env_vars(monkeypatch):
    monkeypatch.setenv("MODELWATCH_CRITICAL_THRESHOLD", "0.5")
    monkeypatch.setenv("MODELWATCH_WARNING_THRESHOLD", "0.2")
    assert status(accuracy_drop=0.10) == "PASS"
    assert status(accuracy_drop=0.30) == "WARNING"
    assert status(accuracy_drop=0.60) == "CRITICAL"