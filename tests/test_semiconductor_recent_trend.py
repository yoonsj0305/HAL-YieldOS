"""
tests/test_semiconductor_recent_trend.py

Verifies _detect_recent_trend() behavior in the semfab analyzer.
"""
from __future__ import annotations

import pytest

from yieldos.domains.semfab.analyzer import (
    SEMICONDUCTOR_MIN_TREND_SAMPLES,
    SEMICONDUCTOR_RECENT_TREND_FRACTION,
    SEMICONDUCTOR_RECENT_TREND_THRESHOLD,
    _detect_recent_trend,
)


def _make_rows(values, column="rf_power_W"):
    return [{column: v} for v in values]


def test_detect_drift_candidate_when_recent_spike():
    # First 10 at 100, last 3 at 200 -> delta = (200-100)/100 = 1.0 >> 0.08
    rows = _make_rows([100.0] * 10 + [200.0] * 3)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["status"] == "DRIFT_CANDIDATE"
    assert result["relative_delta"] > 0


def test_detect_stable_normal_when_flat():
    rows = _make_rows([50.0] * 20)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["status"] == "STABLE_NORMAL"
    assert result["relative_delta"] == pytest.approx(0.0)


def test_insufficient_data_below_min_samples():
    rows = _make_rows([1.0] * 5)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["status"] == "INSUFFICIENT_DATA"
    assert result["relative_delta"] is None
    assert result["sample_count"] == 5


def test_returns_metric_name_in_result():
    rows = _make_rows([1.0] * 10, column="temperature_C")
    result = _detect_recent_trend(rows, "temperature_C")
    assert result["metric"] == "temperature_C"


def test_relative_delta_is_signed():
    # Early=200, recent=100 -> delta < 0
    rows = _make_rows([200.0] * 10 + [100.0] * 3)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["relative_delta"] < 0


def test_threshold_boundary_stable_just_below():
    # 7% delta: 10 rows at 100, 3 rows at 107 → total 13; recent_count=ceil(13*0.3)=4
    # recent_mean=(100+107*3)/4=105.25; delta=(105.25-100)/100=5.25% < 8% → STABLE_NORMAL
    rows = _make_rows([100.0] * 10 + [107.0] * 3)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["status"] == "STABLE_NORMAL"


def test_threshold_boundary_drift_clearly_above():
    # 20 rows at 100, then 3 rows at 200: delta >> 8% → DRIFT_CANDIDATE
    rows = _make_rows([100.0] * 20 + [200.0] * 3)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["status"] == "DRIFT_CANDIDATE"


def test_constants_values():
    assert SEMICONDUCTOR_RECENT_TREND_FRACTION == pytest.approx(0.30)
    assert SEMICONDUCTOR_RECENT_TREND_THRESHOLD == pytest.approx(0.08)
    assert SEMICONDUCTOR_MIN_TREND_SAMPLES == 8


def test_skips_missing_column_values():
    rows = [{"rf_power_W": ""}, {"rf_power_W": None}] + _make_rows([50.0] * 10)
    result = _detect_recent_trend(rows, "rf_power_W")
    assert result["sample_count"] == 10


def test_process_drift_report_in_semfab_result():
    from yieldos.domains.semfab.analyzer import SemFabAnalyzer

    result = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_drift_report")
    assert "process_drift_report" in result
    report = result["process_drift_report"]
    assert report["schema"] == "yieldos.semfab.process_drift_report.v1"
    assert "metric_trends" in report
    assert isinstance(report["drift_candidate_count"], int)
    assert isinstance(report["stable_count"], int)
    assert isinstance(report["insufficient_count"], int)


def test_confidence_report_in_semfab_result():
    from yieldos.domains.semfab.analyzer import SemFabAnalyzer

    result = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_conf_report")
    assert "confidence_report" in result
    report = result["confidence_report"]
    assert "score" in report
    assert "data_status" in report
    assert "signal_status" in report
    assert "confidence_kind" in report
    assert "claim_boundary" in report
    assert 0.0 <= report["score"] <= 1.0
