"""Tests for v3.0.6 SemFab Confidence Passport/Report Writer Propagation Patch."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yieldos.domains.semfab import SemFabAnalyzer
from yieldos.cli.main import _semiconductor_extra_outputs, _run_and_write

SAMPLE_DIR = Path(__file__).parent.parent / "samples" / "pilot_semiconductor"

_REQUIRED_CE_FIELDS = [
    "confidence_report_ref",
    "score",
    "data_status",
    "signal_status",
    "missing_metrics",
    "missing_metric_messages",
    "available_metrics_summary",
    "claim_boundary",
]


@pytest.fixture(scope="module")
def semfab_write_all_output(tmp_path_factory):
    """Run full SemFab analyze → write_all pipeline (general flow, not pilot-pack)."""
    out = tmp_path_factory.mktemp("semfab_306")
    result = SemFabAnalyzer().analyze(
        data_dir=str(SAMPLE_DIR), case_id="rw306_test", asset_id="chip"
    )
    extra = _semiconductor_extra_outputs(result) or {}
    _run_and_write(result, str(out), "semiconductor", extra_outputs=extra)
    return out


# ── 7.1: functional_passport has confidence_explanation in general flow ───────

def test_general_flow_passport_has_confidence_explanation(semfab_write_all_output):
    """General SemFab analyze flow must produce functional_passport.json with confidence_explanation."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    assert "confidence_explanation" in fp, (
        "functional_passport must have confidence_explanation in general flow"
    )


def test_general_flow_passport_confidence_explanation_has_all_fields(semfab_write_all_output):
    """confidence_explanation in general flow passport must have all required fields."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    ce = fp["confidence_explanation"]
    for field in _REQUIRED_CE_FIELDS:
        assert field in ce, f"confidence_explanation missing field: {field}"


def test_general_flow_passport_claim_boundary_correct(semfab_write_all_output):
    """confidence_explanation claim_boundary must be the no-root-cause sentinel."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    ce = fp["confidence_explanation"]
    assert ce["claim_boundary"] == "confidence_explanation_not_root_cause_certification"


# ── 7.2: endpoint_signal missing appears in passport ─────────────────────────

def test_passport_missing_metrics_is_list(semfab_write_all_output):
    """confidence_explanation.missing_metrics must be a list."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    ce = fp.get("confidence_explanation", {})
    assert isinstance(ce.get("missing_metrics"), list)


def test_passport_missing_metric_messages_match_missing_list(semfab_write_all_output):
    """missing_metric_messages must have one entry per missing metric saying 'no data'."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    ce = fp.get("confidence_explanation", {})
    missing = ce.get("missing_metrics", [])
    msgs = ce.get("missing_metric_messages", [])
    assert len(msgs) == len(missing)
    for m in missing:
        assert any(m in msg and "no data" in msg for msg in msgs), (
            f"missing_metric_messages must contain '{m}: no data'"
        )


# ── 7.3: report.html gets semiconductor confidence section ────────────────────

def test_general_flow_html_has_confidence_section(semfab_write_all_output):
    """report.html in general SemFab flow must contain the semiconductor confidence div."""
    html_path = semfab_write_all_output / "report.html"
    assert html_path.exists(), "report.html must exist"
    html = html_path.read_text(encoding="utf-8")
    assert "semi-confidence-section" in html, (
        "report.html must contain semiconductor confidence section class"
    )


def test_general_flow_html_has_confidence_heading(semfab_write_all_output):
    """report.html must contain 'Semiconductor Process Confidence' heading."""
    html = (semfab_write_all_output / "report.html").read_text(encoding="utf-8")
    assert "Semiconductor Process Confidence" in html


def test_general_flow_html_has_metric_table(semfab_write_all_output):
    """report.html confidence section must have a metric status table."""
    html = (semfab_write_all_output / "report.html").read_text(encoding="utf-8")
    assert "<table>" in html and "<th>Metric</th>" in html


# ── 7.4: report.md gets semiconductor confidence section ─────────────────────

def test_general_flow_md_has_confidence_section_if_generated(semfab_write_all_output):
    """report.md must contain 'Semiconductor Confidence' section if the file exists."""
    md_path = semfab_write_all_output / "report.md"
    if md_path.exists():
        md = md_path.read_text(encoding="utf-8")
        assert "Semiconductor Confidence" in md


def test_general_flow_md_has_metric_table_if_generated(semfab_write_all_output):
    """report.md confidence section must contain markdown metric table."""
    md_path = semfab_write_all_output / "report.md"
    if md_path.exists():
        md = md_path.read_text(encoding="utf-8")
        assert "| Metric | Status |" in md


# ── 7.5: confidence_report data alignment ────────────────────────────────────

def test_confidence_report_score_aligns_with_passport(semfab_write_all_output):
    """semiconductor_confidence_report.json score must equal passport confidence_explanation score."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    conf_rep = json.loads(
        (semfab_write_all_output / "semiconductor_confidence_report.json").read_text(encoding="utf-8")
    )
    inner = conf_rep.get("confidence_report", {})
    ce = fp.get("confidence_explanation", {})
    assert ce.get("score") == inner.get("score"), (
        "passport confidence_explanation score must match semiconductor_confidence_report score"
    )


def test_confidence_report_data_status_aligns_with_passport(semfab_write_all_output):
    """data_status must be consistent between passport and confidence report."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    conf_rep = json.loads(
        (semfab_write_all_output / "semiconductor_confidence_report.json").read_text(encoding="utf-8")
    )
    inner = conf_rep.get("confidence_report", {})
    ce = fp.get("confidence_explanation", {})
    assert ce.get("data_status") == inner.get("data_status")


# ── 7.6: score invariants ─────────────────────────────────────────────────────

def test_confidence_score_in_valid_range(semfab_write_all_output):
    """Confidence score in passport must be a valid float in [0.0, 1.0]."""
    fp = json.loads(
        (semfab_write_all_output / "functional_passport.json").read_text(encoding="utf-8")
    )
    ce = fp.get("confidence_explanation", {})
    score = ce.get("score", -1)
    assert isinstance(score, (int, float)), "score must be numeric"
    assert 0.0 <= score <= 1.0, f"confidence score {score} out of valid range [0.0, 1.0]"


def test_confidence_report_json_still_has_all_fields(semfab_write_all_output):
    """semiconductor_confidence_report.json must still have score, data_status, signal_status, reasons."""
    conf_rep = json.loads(
        (semfab_write_all_output / "semiconductor_confidence_report.json").read_text(encoding="utf-8")
    )
    inner = conf_rep.get("confidence_report", {})
    for field in ("score", "data_status", "signal_status", "reasons", "missing_metrics", "available_metrics_summary"):
        assert field in inner, f"semiconductor_confidence_report.confidence_report missing: {field}"
