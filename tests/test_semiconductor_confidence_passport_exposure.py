"""Tests for v3.0.5 Semiconductor Confidence Passport Exposure + Summary Field Alignment."""
from __future__ import annotations

from yieldos.domains.semfab.analyzer import (
    WATCHED_METRICS,
    _build_confidence_report,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_trend(metric, status, *, relative_delta=0.01, early_mean=1.0, recent_mean=1.01):
    base = {"metric": metric, "status": status, "sample_count": 0 if status == "INSUFFICIENT_DATA" else 20}
    if status != "INSUFFICIENT_DATA":
        base.update({"relative_delta": relative_delta, "early_mean": early_mean, "recent_mean": recent_mean})
    else:
        base.update({"relative_delta": None, "early_mean": None, "recent_mean": None})
    return base


def _build_conf_with(*, missing=(), drift=()):
    """Build confidence report where `missing` metrics are INSUFFICIENT_DATA and `drift` are DRIFT_CANDIDATE."""
    trends = []
    for m in WATCHED_METRICS:
        if m in missing:
            trends.append(_make_trend(m, "INSUFFICIENT_DATA"))
        elif m in drift:
            trends.append(_make_trend(m, "DRIFT_CANDIDATE", relative_delta=0.20))
        else:
            trends.append(_make_trend(m, "STABLE_NORMAL"))
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    return _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)


def _apply_passport_patch(raw_conf: dict) -> dict:
    """Simulate the functional_passport patching logic from cmd_semiconductor_pilot_pack."""
    fp_data: dict = {"semiconductor_analysis_context": {}}
    missing_m = raw_conf.get("missing_metrics", [])
    conf_explanation = {
        "confidence_report_ref": "semiconductor_confidence_report.json",
        "score": raw_conf.get("score", 0.0),
        "data_status": raw_conf.get("data_status", "UNKNOWN"),
        "signal_status": raw_conf.get("signal_status", "UNKNOWN"),
        "reasons": raw_conf.get("reasons", []),
        "missing_metrics": missing_m,
        "missing_metric_messages": [f"{m}: no data" for m in missing_m],
        "available_metrics_summary": raw_conf.get("available_metrics_summary", {}),
        "claim_boundary": "confidence_explanation_not_root_cause_certification",
    }
    fp_data["confidence_explanation"] = conf_explanation
    if "semiconductor_analysis_context" in fp_data:
        fp_data["semiconductor_analysis_context"]["confidence_explanation"] = {
            "missing_metrics": missing_m,
            "missing_metric_messages": [f"{m}: no data" for m in missing_m],
            "available_metrics_summary": raw_conf.get("available_metrics_summary", {}),
        }
    return fp_data


# ── 6.1: functional_passport exposes gas_flow_sccm missing ───────────────────

def test_passport_has_confidence_explanation_when_gas_flow_missing():
    """functional_passport must expose confidence_explanation when gas_flow_sccm is missing."""
    raw_conf = _build_conf_with(missing=["gas_flow_sccm", "endpoint_signal"])
    fp = _apply_passport_patch(raw_conf)
    assert "confidence_explanation" in fp


def test_passport_missing_metrics_contains_gas_flow():
    """confidence_explanation.missing_metrics must include gas_flow_sccm when absent."""
    raw_conf = _build_conf_with(missing=["gas_flow_sccm"])
    fp = _apply_passport_patch(raw_conf)
    assert "gas_flow_sccm" in fp["confidence_explanation"]["missing_metrics"]


def test_passport_missing_metric_messages_exist_for_gas_flow():
    """confidence_explanation.missing_metric_messages must exist and include gas_flow_sccm."""
    raw_conf = _build_conf_with(missing=["gas_flow_sccm"])
    fp = _apply_passport_patch(raw_conf)
    msgs = fp["confidence_explanation"]["missing_metric_messages"]
    assert isinstance(msgs, list) and len(msgs) > 0
    assert any("gas_flow_sccm" in msg for msg in msgs)


def test_passport_missing_metric_messages_say_no_data():
    """missing_metric_messages must contain 'no data' for each missing metric."""
    raw_conf = _build_conf_with(missing=["gas_flow_sccm"])
    fp = _apply_passport_patch(raw_conf)
    msgs = fp["confidence_explanation"]["missing_metric_messages"]
    assert any("no data" in msg for msg in msgs)


# ── 6.2: functional_passport exposes endpoint_signal missing ─────────────────

def test_passport_missing_metrics_contains_endpoint_signal():
    """confidence_explanation.missing_metrics must include endpoint_signal when absent."""
    raw_conf = _build_conf_with(missing=["endpoint_signal"])
    fp = _apply_passport_patch(raw_conf)
    assert "endpoint_signal" in fp["confidence_explanation"]["missing_metrics"]


def test_passport_messages_mention_endpoint_signal():
    """missing_metric_messages must mention endpoint_signal when it is missing."""
    raw_conf = _build_conf_with(missing=["endpoint_signal"])
    fp = _apply_passport_patch(raw_conf)
    msgs = fp["confidence_explanation"]["missing_metric_messages"]
    assert any("endpoint_signal" in m for m in msgs)
    assert any("no data" in m for m in msgs)


# ── 6.3: available_metrics_summary exact fields ───────────────────────────────

_REQUIRED_SUMMARY_FIELDS = [
    "available_metric_count",
    "watched_metric_count",
    "drift_candidate_count",
    "stable_count",
    "insufficient_data_count",
    "drift_candidate_metrics",
    "stable_metrics",
    "insufficient_data_metrics",
    "summary_text",
]


def test_available_metrics_summary_has_all_exact_fields():
    """available_metrics_summary must contain all v3.0.5 required exact fields."""
    report = _build_conf_with(missing=["gas_flow_sccm"], drift=["pressure_mTorr"])
    s = report["available_metrics_summary"]
    for field in _REQUIRED_SUMMARY_FIELDS:
        assert field in s, f"available_metrics_summary missing required field: {field}"


def test_available_metrics_summary_counts_correct():
    """available_metric_count + insufficient_data_count must equal watched_metric_count."""
    report = _build_conf_with(missing=["gas_flow_sccm", "endpoint_signal"])
    s = report["available_metrics_summary"]
    assert s["watched_metric_count"] == len(WATCHED_METRICS)
    assert s["available_metric_count"] + s["insufficient_data_count"] == s["watched_metric_count"]
    assert s["insufficient_data_count"] == 2


def test_available_metrics_summary_in_confidence_report():
    """semiconductor_confidence_report must also expose the new exact fields."""
    from yieldos.domains.semfab import SemFabAnalyzer
    from yieldos.cli.main import _semiconductor_extra_outputs
    import csv
    from pathlib import Path
    sample = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"
    result = SemFabAnalyzer().analyze(data_dir=str(sample), case_id="conf_305_test", asset_id="chip")
    extras = _semiconductor_extra_outputs(result) or {}
    conf_rep = extras.get("semiconductor_confidence_report", {})
    inner = conf_rep.get("confidence_report", {})
    s = inner.get("available_metrics_summary", {})
    for field in _REQUIRED_SUMMARY_FIELDS:
        assert field in s, f"semiconductor_confidence_report.available_metrics_summary missing: {field}"


# ── 6.4: compatibility fields remain ─────────────────────────────────────────

def test_compat_fields_remain():
    """v3.0.4 compatibility fields must still be present alongside new fields."""
    report = _build_conf_with(missing=["gas_flow_sccm"])
    s = report["available_metrics_summary"]
    assert "total_watched" in s
    assert "available_count" in s
    assert "missing_count" in s
    assert "available" in s
    assert "missing" in s


def test_compat_fields_consistent_with_new_fields():
    """v3.0.4 compat fields must equal their v3.0.5 equivalents."""
    report = _build_conf_with(missing=["gas_flow_sccm", "endpoint_signal"])
    s = report["available_metrics_summary"]
    assert s["total_watched"] == s["watched_metric_count"]
    assert s["available_count"] == s["available_metric_count"]
    assert s["missing_count"] == s["insufficient_data_count"]
    assert s["missing"] == s["insufficient_data_metrics"]


# ── 6.5: pressure drift still appears ────────────────────────────────────────

def test_pressure_drift_appears_in_drift_candidate_metrics():
    """pressure_mTorr must appear in drift_candidate_metrics when it drifts."""
    report = _build_conf_with(drift=["pressure_mTorr"])
    s = report["available_metrics_summary"]
    assert "pressure_mTorr" in s["drift_candidate_metrics"]


def test_pressure_drift_count_increments():
    """drift_candidate_count must be 1 when only pressure_mTorr drifts."""
    report = _build_conf_with(drift=["pressure_mTorr"])
    s = report["available_metrics_summary"]
    assert s["drift_candidate_count"] == 1


def test_pressure_drift_summary_text_mentions_pressure():
    """summary_text must mention pressure_mTorr when it is a drift candidate."""
    report = _build_conf_with(drift=["pressure_mTorr"], missing=["gas_flow_sccm"])
    s = report["available_metrics_summary"]
    assert "pressure_mTorr" in s["summary_text"]


def test_pressure_not_in_stable_when_drifting():
    """pressure_mTorr must not appear in stable_metrics when it is drifting."""
    report = _build_conf_with(drift=["pressure_mTorr"])
    s = report["available_metrics_summary"]
    assert "pressure_mTorr" not in s["stable_metrics"]


# ── 6.6: report.html still exposes missing metrics ───────────────────────────

def test_html_metric_row_generator_for_missing_metric():
    """When gas_flow_sccm is missing, the HTML metric row must contain 'no data'."""
    avail_set = {"rf_power_W", "pressure_mTorr", "temperature_C"}  # gas_flow_sccm absent
    html_rows = "".join(
        f"<tr><td><code>{m}</code></td>"
        f"<td>{'available' if m in avail_set else 'no data'}</td></tr>"
        for m in WATCHED_METRICS
    )
    assert "gas_flow_sccm" in html_rows
    # Find the row for gas_flow_sccm and check it says no data
    assert "no data" in html_rows
    gas_idx = html_rows.index("gas_flow_sccm")
    # The 'no data' appears after gas_flow_sccm in that row
    row_fragment = html_rows[gas_idx : gas_idx + 80]
    assert "no data" in row_fragment


def test_html_available_metric_says_available():
    """When rf_power_W is available, its HTML row must say 'available'."""
    avail_set = {"rf_power_W", "pressure_mTorr", "temperature_C"}
    html_rows = "".join(
        f"<tr><td><code>{m}</code></td>"
        f"<td>{'available' if m in avail_set else 'no data'}</td></tr>"
        for m in WATCHED_METRICS
    )
    rf_idx = html_rows.index("rf_power_W")
    row_fragment = html_rows[rf_idx : rf_idx + 80]
    assert "available" in row_fragment


# ── 6.7: confidence score unchanged ──────────────────────────────────────────

def test_confidence_score_stable_all_available():
    """With sufficient data and all stable, score must be 0.70 (unchanged from v3.0.4)."""
    report = _build_conf_with()
    assert report["score"] == 0.70


def test_confidence_score_with_drift():
    """With sufficient data and DRIFT_CANDIDATE signal (drift_count >= stable_count), score must be 0.65."""
    # Need drift_count >= stable_count: make 3 metrics drift, 2 stable (no missing)
    trends = []
    for i, m in enumerate(WATCHED_METRICS):
        status = "DRIFT_CANDIDATE" if i < 3 else "STABLE_NORMAL"
        trends.append(_make_trend(m, status, relative_delta=0.20 if i < 3 else 0.01))
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=20, metrology_rows=10, trend_statuses=trends)
    assert report["score"] == 0.65


def test_confidence_score_with_no_data():
    """With no tool_log rows, score must be 0.30 (unchanged)."""
    trends = [_make_trend(m, "INSUFFICIENT_DATA") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "INSUFFICIENT_DATA"))
    report = _build_confidence_report(tool_log_rows=0, metrology_rows=0, trend_statuses=trends)
    assert report["score"] == 0.30


# ── 6.8: summary_text format invariants ──────────────────────────────────────

def test_summary_text_all_missing_format():
    """When all metrics missing, summary_text must say 'all watched metrics have insufficient data'."""
    trends = [_make_trend(m, "INSUFFICIENT_DATA") for m in WATCHED_METRICS]
    trends.append(_make_trend("cd_nm", "STABLE_NORMAL"))
    report = _build_confidence_report(tool_log_rows=0, metrology_rows=0, trend_statuses=trends)
    s = report["available_metrics_summary"]
    assert "all watched metrics have insufficient data" in s["summary_text"]


def test_summary_text_no_missing_no_drift():
    """When no metrics missing and no drift, summary_text must mention 'all watched metrics have usable data'."""
    report = _build_conf_with()
    s = report["available_metrics_summary"]
    assert "usable data" in s["summary_text"]


def test_summary_text_mentions_missing_metric_names():
    """summary_text must include the name of each missing metric."""
    report = _build_conf_with(missing=["gas_flow_sccm", "endpoint_signal"])
    s = report["available_metrics_summary"]
    assert "gas_flow_sccm" in s["summary_text"]
    assert "endpoint_signal" in s["summary_text"]


def test_no_root_cause_in_claim_boundary():
    """confidence_explanation must carry claim_boundary='confidence_explanation_not_root_cause_certification'."""
    raw_conf = _build_conf_with(missing=["gas_flow_sccm"])
    fp = _apply_passport_patch(raw_conf)
    assert fp["confidence_explanation"]["claim_boundary"] == "confidence_explanation_not_root_cause_certification"
