"""
tests/test_robot_recent_weighted_mean.py

Verifies the recent-weighted mean function in the robot analyzer.
"""
from __future__ import annotations

import pytest

from yieldos.domains.robot.analyzer import _col_recent_weighted_mean


def test_recent_weighted_mean_emphasizes_recent_values():
    rows = [{"torque": 1.0}] * 7 + [{"torque": 10.0}] * 3
    result = _col_recent_weighted_mean(rows, "torque", recent_fraction=0.30, recent_weight=0.70)
    # recent 30% = last 3 rows (all 10.0), old 70% = first 7 rows (all 1.0)
    # weighted = 1.0 * 0.30 + 10.0 * 0.70 = 0.3 + 7.0 = 7.3
    assert result == pytest.approx(7.3)


def test_recent_weighted_mean_uniform_data_returns_mean():
    rows = [{"v": 5.0}] * 10
    result = _col_recent_weighted_mean(rows, "v")
    assert result == pytest.approx(5.0)


def test_recent_weighted_mean_single_row():
    rows = [{"v": 42.0}]
    result = _col_recent_weighted_mean(rows, "v")
    assert result == pytest.approx(42.0)


def test_recent_weighted_mean_empty_column_returns_none():
    rows = [{"other": 1.0}] * 5
    result = _col_recent_weighted_mean(rows, "missing_col")
    assert result is None


def test_recent_weighted_mean_skips_empty_strings():
    rows = [{"v": ""}, {"v": "3.0"}, {"v": "3.0"}, {"v": "3.0"}]
    result = _col_recent_weighted_mean(rows, "v")
    assert result == pytest.approx(3.0)


def test_recent_weighted_mean_recent_spike_dominates():
    rows = [{"v": 1.0}] * 9 + [{"v": 100.0}]
    result = _col_recent_weighted_mean(rows, "v", recent_fraction=0.30, recent_weight=0.70)
    # recent 30% = last 3 rows: [1.0, 1.0, 100.0] -> mean = 34.0
    # old 70% = first 7 rows: all 1.0 -> mean = 1.0
    # weighted = 1.0 * 0.30 + 34.0 * 0.70 = 0.3 + 23.8 = 24.1
    assert result == pytest.approx(24.1)


def test_recent_weighted_mean_default_constants():
    from yieldos.domains.robot.analyzer import RECENT_FRACTION, RECENT_WEIGHT
    assert RECENT_FRACTION == pytest.approx(0.30)
    assert RECENT_WEIGHT == pytest.approx(0.70)


def test_robot_analyze_aggregation_method_in_state():
    import csv
    import os
    import tempfile

    cols = ["motor_current_A", "joint_temp_C", "imu_vibration_g", "position_error_mm", "latency_ms"]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        csv_file = f.name
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for _ in range(10):
            writer.writerow({c: "1.0" for c in cols})

    try:
        from yieldos.domains.robot.analyzer import RobotAnalyzer
        result = RobotAnalyzer().analyze(csv_file, case_id="test_wm")
        agg = result["state"].metrics.get("aggregation_method", {})
        assert agg["kind"] == "recent_weighted_mean"
        assert agg["recent_fraction"] == pytest.approx(0.30)
        assert agg["recent_weight"] == pytest.approx(0.70)
    finally:
        os.unlink(csv_file)
