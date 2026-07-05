"""
tests/test_semiconductor_confidence_semantics.py

Verifies _build_confidence_report() semantics and the fix for the
hardcoded confidence=0.30 bug in SemFabAnalyzer when no evidence found.
"""
from __future__ import annotations

import pytest

from yieldos.domains.semfab.analyzer import _build_confidence_report


def _stable_trend(metric):
    return {"metric": metric, "status": "STABLE_NORMAL", "sample_count": 20}


def _drift_trend(metric):
    return {"metric": metric, "status": "DRIFT_CANDIDATE", "sample_count": 20}


def _insuf_trend(metric):
    return {"metric": metric, "status": "INSUFFICIENT_DATA", "sample_count": 3}


# ── Scoring rules ─────────────────────────────────────────────────────────────

def test_insufficient_data_gives_030():
    report = _build_confidence_report(
        tool_log_rows=0,
        metrology_rows=0,
        trend_statuses=[],
    )
    assert report["score"] == pytest.approx(0.30)
    assert report["data_status"] == "INSUFFICIENT_DATA"


def test_partial_data_gives_045():
    report = _build_confidence_report(
        tool_log_rows=3,
        metrology_rows=2,
        trend_statuses=[_stable_trend("rf_power_W")],
    )
    assert report["score"] == pytest.approx(0.45)
    assert report["data_status"] == "PARTIAL_DATA"


def test_sufficient_stable_gives_070():
    report = _build_confidence_report(
        tool_log_rows=20,
        metrology_rows=10,
        trend_statuses=[
            _stable_trend("rf_power_W"),
            _stable_trend("temperature_C"),
            _stable_trend("pressure_mTorr"),
        ],
    )
    assert report["score"] == pytest.approx(0.70)
    assert report["data_status"] == "SUFFICIENT"
    assert report["signal_status"] == "STABLE_NORMAL"
    assert report["confidence_kind"] == "stable_normal_sufficient_data"


def test_sufficient_drift_gives_065():
    report = _build_confidence_report(
        tool_log_rows=20,
        metrology_rows=5,
        trend_statuses=[
            _drift_trend("rf_power_W"),
            _stable_trend("temperature_C"),
        ],
    )
    assert report["score"] == pytest.approx(0.65)
    assert report["signal_status"] == "DRIFT_CANDIDATE"


def test_sufficient_conflicting_gives_050():
    # drift_count > 0 but drift < stable → CONFLICTING_SIGNALS
    report = _build_confidence_report(
        tool_log_rows=20,
        metrology_rows=5,
        trend_statuses=[
            _drift_trend("rf_power_W"),
            _stable_trend("temperature_C"),
            _stable_trend("pressure_mTorr"),
        ],
    )
    assert report["score"] == pytest.approx(0.50)
    assert report["signal_status"] == "CONFLICTING_SIGNALS"


# ── Structural fields ─────────────────────────────────────────────────────────

def test_report_has_required_fields():
    report = _build_confidence_report(
        tool_log_rows=20,
        metrology_rows=5,
        trend_statuses=[_stable_trend("rf_power_W")],
    )
    for key in ("confidence_kind", "score", "data_status", "signal_status", "reasons", "claim_boundary"):
        assert key in report, f"Missing field: {key}"


def test_claim_boundary_is_constant():
    report = _build_confidence_report(
        tool_log_rows=10,
        metrology_rows=4,
        trend_statuses=[_stable_trend("rf_power_W")],
    )
    assert report["claim_boundary"] == "confidence_in_analysis_quality_not_severity"


def test_reasons_is_list():
    report = _build_confidence_report(
        tool_log_rows=5,
        metrology_rows=0,
        trend_statuses=[_stable_trend("rf_power_W")],
    )
    assert isinstance(report["reasons"], list)
    assert len(report["reasons"]) >= 1


# ── Fix verification: no hardcoded 0.3 when data is sufficient ────────────────

def test_semfab_no_evidence_does_not_return_030_when_data_sufficient():
    """When data is sufficient and signals are stable, confidence must be > 0.30."""
    from yieldos.domains.semfab.analyzer import SemFabAnalyzer

    result = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_conf_fix")
    state = result["state"]
    # Whether or not evidence objects were found, confidence must be data-driven
    if not result["evidence_pack"].evidence_objects:
        assert state.confidence > 0.30, (
            f"Bug: confidence was hardcoded to 0.30 when no evidence; "
            f"got {state.confidence} — should be >= 0.45 for partial or 0.70 for stable+sufficient"
        )


def test_confidence_report_score_matches_state_confidence():
    """state.confidence and confidence_report.score must be consistent when no evidence."""
    from yieldos.domains.semfab.analyzer import SemFabAnalyzer

    result = SemFabAnalyzer().analyze("samples/semfab_tel_like", case_id="test_conf_match")
    if not result["evidence_pack"].evidence_objects:
        assert result["state"].confidence == pytest.approx(result["confidence_report"]["score"])
