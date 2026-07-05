"""Tests for v3.0.4 Semiconductor Confidence Missing Metrics Message Patch."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from yieldos.domains.semfab.analyzer import (
    WATCHED_METRICS,
    _build_confidence_report,
    _detect_recent_trend,
)
from yieldos.domains.semfab.pilot_pack import generate_pilot_pack

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"


# ── Unit tests for _build_confidence_report() ────────────────────────────────

def _make_trend(metric, status):
    """Make a minimal trend dict with the given status."""
    return {
        "metric": metric,
        "status": status,
        "sample_count": 0 if status == "INSUFFICIENT_DATA" else 20,
        "relative_delta": None if status == "INSUFFICIENT_DATA" else 0.01,
        "early_mean": None if status == "INSUFFICIENT_DATA" else 1.0,
        "recent_mean": None if status == "INSUFFICIENT_DATA" else 1.01,
    }


def test_missing_metrics_field_present():
    """_build_confidence_report() must include 'missing_metrics' in return dict."""
    trends = [_make_trend(m, "STABLE_NORMAL") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    assert "missing_metrics" in report


def test_available_metrics_summary_field_present():
    """_build_confidence_report() must include 'available_metrics_summary' in return dict."""
    trends = [_make_trend(m, "STABLE_NORMAL") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    assert "available_metrics_summary" in report


def test_missing_metrics_when_all_insufficient():
    """All WATCHED_METRICS with INSUFFICIENT_DATA must all appear in missing_metrics."""
    trends = [_make_trend(m, "INSUFFICIENT_DATA") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "INSUFFICIENT_DATA"))
    report = _build_confidence_report(tool_log_rows=0, metrology_rows=0, trend_statuses=trends)
    assert set(report["missing_metrics"]) == set(WATCHED_METRICS)


def test_missing_metrics_when_one_missing():
    """Only the metric with INSUFFICIENT_DATA must appear in missing_metrics."""
    trends = []
    for i, m in enumerate(WATCHED_METRICS):
        status = "INSUFFICIENT_DATA" if i == 0 else "STABLE_NORMAL"
        trends.append(_make_trend(m, status))
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    assert report["missing_metrics"] == [WATCHED_METRICS[0]]


def test_missing_metrics_when_none_missing():
    """missing_metrics must be empty when all WATCHED_METRICS have data."""
    trends = [_make_trend(m, "STABLE_NORMAL") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    assert report["missing_metrics"] == []


def test_available_metrics_summary_counts_add_up():
    """available_count + missing_count must equal total_watched (== len(WATCHED_METRICS))."""
    # Mark 2 as missing
    missing_set = set(WATCHED_METRICS[:2])
    trends = [
        _make_trend(m, "INSUFFICIENT_DATA" if m in missing_set else "STABLE_NORMAL")
        for m in WATCHED_METRICS
    ]
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    s = report["available_metrics_summary"]
    assert s["total_watched"] == len(WATCHED_METRICS)
    assert s["available_count"] + s["missing_count"] == s["total_watched"]
    assert s["missing_count"] == 2


def test_available_metrics_summary_text_present():
    """available_metrics_summary must contain a non-empty 'summary_text' string."""
    trends = [_make_trend(m, "STABLE_NORMAL") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    s = report["available_metrics_summary"]
    assert isinstance(s.get("summary_text"), str)
    assert len(s["summary_text"]) > 0


def test_cd_nm_not_in_missing_metrics():
    """cd_nm (non-WATCHED_METRIC) must never appear in missing_metrics even if INSUFFICIENT."""
    trends = [_make_trend(m, "STABLE_NORMAL") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "INSUFFICIENT_DATA"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    assert "cd_nm" not in report["missing_metrics"]


# ── Integration tests using SemFabAnalyzer + _semiconductor_extra_outputs ────

@pytest.fixture(scope="module")
def semfab_conf_output():
    """Run SemFabAnalyzer on sample data and apply _semiconductor_extra_outputs."""
    from yieldos.domains.semfab import SemFabAnalyzer
    from yieldos.cli.main import _semiconductor_extra_outputs
    result = SemFabAnalyzer().analyze(
        data_dir=str(SAMPLE_DIR), case_id="conf_missing_test", asset_id="chip_demo"
    )
    extras = _semiconductor_extra_outputs(result) or {}
    return extras


def test_confidence_report_has_missing_metrics_in_pilot(semfab_conf_output):
    """semiconductor_confidence_report output must have missing_metrics."""
    conf_report = semfab_conf_output.get("semiconductor_confidence_report", {})
    assert conf_report, "semiconductor_confidence_report must be present in extra outputs"
    inner = conf_report.get("confidence_report", {})
    assert "missing_metrics" in inner, "missing_metrics must be in confidence_report"


def test_confidence_report_has_available_metrics_summary_in_pilot(semfab_conf_output):
    """semiconductor_confidence_report output must have available_metrics_summary."""
    conf_report = semfab_conf_output.get("semiconductor_confidence_report", {})
    inner = conf_report.get("confidence_report", {})
    assert "available_metrics_summary" in inner


def test_available_metrics_summary_structure_in_pilot(semfab_conf_output):
    """available_metrics_summary must have all required sub-fields."""
    conf_report = semfab_conf_output.get("semiconductor_confidence_report", {})
    inner = conf_report.get("confidence_report", {})
    s = inner.get("available_metrics_summary", {})
    for key in ("total_watched", "available_count", "missing_count", "available", "missing", "summary_text"):
        assert key in s, f"available_metrics_summary missing key: {key}"


def test_summary_text_mentions_missing_if_any(semfab_conf_output):
    """If any metrics are missing, summary_text must mention them by name."""
    conf_report = semfab_conf_output.get("semiconductor_confidence_report", {})
    inner = conf_report.get("confidence_report", {})
    missing = inner.get("missing_metrics", [])
    s = inner.get("available_metrics_summary", {})
    text = s.get("summary_text", "")
    for m in missing:
        assert m in text, f"summary_text must mention missing metric '{m}'"
