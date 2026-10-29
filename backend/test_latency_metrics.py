import pytest
from backend.latency_metrics import (
    calculate_percentile,
    calculate_latency_metrics,
)


def test_percentile_empty_list_returns_zero():
    assert calculate_percentile([], 50) == 0.0


def test_percentile_single_value():
    assert calculate_percentile([10.0], 95) == 10.0


def test_percentile_median_of_odd_list():
    assert calculate_percentile([1, 2, 3, 4, 5], 50) == 3


def test_percentile_interpolates_between_values():
    assert calculate_percentile([10, 20], 50) == 15.0
    assert calculate_percentile([1, 2, 3, 4, 5], 95) == pytest.approx(4.8)


def test_percentile_does_not_need_sorted_input():
    assert calculate_percentile([5, 1, 3], 50) == 3


def test_metrics_empty_returns_all_zeros():
    assert calculate_latency_metrics([]) == {
        "minimum_ms": 0.0,
        "average_ms": 0.0,
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "maximum_ms": 0.0,
    }


def test_metrics_known_values():
    m = calculate_latency_metrics([100, 200, 300])
    assert m["minimum_ms"] == 100
    assert m["average_ms"] == 200
    assert m["p50_ms"] == 200
    assert m["p95_ms"] == pytest.approx(290.0)
    assert m["maximum_ms"] == 300


def test_p95_ignores_a_single_outlier_but_max_and_average_do_not():
    # the reason percentiles exist: 99 fast calls + one 30 s outlier
    latencies = [1000] * 99 + [30000]
    m = calculate_latency_metrics(latencies)
    assert m["p50_ms"] == 1000
    assert m["p95_ms"] == 1000
    assert m["maximum_ms"] == 30000
    assert m["average_ms"] == pytest.approx(1290.0)