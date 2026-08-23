"""
Unit tests for detector.py — pure logic, no Flask or database involved.
This is the fastest, simplest kind of test: given input X, expect output Y.
"""
from detector import find_anomalies


def test_flags_ip_over_threshold():
    totals = {"1.1.1.1": 15_000_000}
    assert find_anomalies(totals) == ["1.1.1.1"]


def test_does_not_flag_ip_under_threshold():
    totals = {"1.1.1.1": 500_000}
    assert find_anomalies(totals) == []


def test_ip_exactly_at_threshold_is_not_flagged():
    """Boundary case: threshold is exclusive (must be strictly greater than)."""
    totals = {"1.1.1.1": 10_000_000}
    assert find_anomalies(totals) == []


def test_multiple_anomalies_sorted_highest_first():
    totals = {
        "1.1.1.1": 11_000_000,
        "2.2.2.2": 50_000_000,
        "3.3.3.3": 1_000_000,  # not an anomaly
    }
    assert find_anomalies(totals) == ["2.2.2.2", "1.1.1.1"]


def test_empty_input_returns_empty_list():
    assert find_anomalies({}) == []


def test_custom_threshold_is_respected():
    totals = {"1.1.1.1": 5_000}
    assert find_anomalies(totals, threshold=1_000) == ["1.1.1.1"]
