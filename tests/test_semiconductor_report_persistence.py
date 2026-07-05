"""
tests/test_semiconductor_report_persistence.py

Verifies that running the semiconductor demo generates:
  - process_drift_report.json
  - semiconductor_confidence_report.json

And that these are linked from functional_passport.json and case_manifest.json.

v2.8.5: Semiconductor Report Persistence tests.
v2.8.8: Rewritten to use demo_case_factory fixture (no per-test CLI subprocess).
        Strict-validate and validate-exit smoke tests kept as minimal subprocess calls.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers import run_yieldos_cli as run_cli

# ── Shared semiconductor demo output (one demo run per module) ─────────────────

@pytest.fixture(scope="module")
def semi_out(tmp_path_factory) -> Path:
    """Generate semiconductor demo output once for this module."""
    from yieldos.demo_runner import run_domain_demo_direct
    out = tmp_path_factory.mktemp("semiconductor_persist")
    return run_domain_demo_direct(domain="semiconductor", out_dir=out)


# ── File existence ─────────────────────────────────────────────────────────────

def test_semiconductor_reports_are_written(semi_out):
    assert (semi_out / "process_drift_report.json").exists(), "process_drift_report.json not written"
    assert (semi_out / "semiconductor_confidence_report.json").exists(), \
        "semiconductor_confidence_report.json not written"


def test_semiconductor_reports_are_linked_from_passport_and_manifest(semi_out):
    passport = json.loads((semi_out / "functional_passport.json").read_text(encoding="utf-8"))
    manifest = json.loads((semi_out / "case_manifest.json").read_text(encoding="utf-8"))

    assert passport.get("process_drift_report_ref") == "process_drift_report.json", (
        f"process_drift_report_ref missing or wrong in passport: {passport.get('process_drift_report_ref')}"
    )
    assert passport.get("semiconductor_confidence_report_ref") == "semiconductor_confidence_report.json", (
        f"semiconductor_confidence_report_ref missing or wrong: {passport.get('semiconductor_confidence_report_ref')}"
    )

    optional = manifest.get("optional_outputs", {})
    if isinstance(optional, dict):
        paths = [v.get("path") for v in optional.values()]
    else:
        paths = [item.get("path") for item in optional]

    assert "process_drift_report.json" in paths, (
        f"process_drift_report.json not in optional_outputs paths: {paths}"
    )
    assert "semiconductor_confidence_report.json" in paths, (
        f"semiconductor_confidence_report.json not in optional_outputs paths: {paths}"
    )


# ── Schema validation ──────────────────────────────────────────────────────────

def test_process_drift_report_schema(semi_out):
    pdr = json.loads((semi_out / "process_drift_report.json").read_text(encoding="utf-8"))

    assert pdr.get("schema") == "hal.yieldos.semiconductor.process_drift_report.v1"
    assert pdr.get("domain") == "semiconductor"
    assert "case_id" in pdr
    assert "recent_trend_detection" in pdr
    rtr = pdr["recent_trend_detection"]
    assert "signals" in rtr
    assert "summary_status" in rtr
    assert rtr["summary_status"] in (
        "DRIFT_CANDIDATE", "STABLE_NORMAL", "INSUFFICIENT_DATA", "MIXED_SIGNALS", "UNKNOWN"
    )


def test_confidence_report_schema(semi_out):
    scr = json.loads((semi_out / "semiconductor_confidence_report.json").read_text(encoding="utf-8"))

    assert scr.get("schema") == "hal.yieldos.semiconductor.confidence_report.v1"
    assert scr.get("domain") == "semiconductor"
    assert "case_id" in scr
    assert "confidence_report" in scr
    cr = scr["confidence_report"]
    assert cr.get("confidence_kind") == "analysis_confidence"
    assert 0.0 <= cr.get("score", -1) <= 1.0
    assert "data_status" in cr
    assert "signal_status" in cr


# ── Safety boundary ────────────────────────────────────────────────────────────

def test_process_drift_report_safety_boundary(semi_out):
    pdr = json.loads((semi_out / "process_drift_report.json").read_text(encoding="utf-8"))
    sb = pdr.get("safety_boundary", {})
    assert sb.get("hardware_execution_enabled") is False
    assert sb.get("human_review_required") is True
    assert sb.get("candidate_only") is True


def test_confidence_report_safety_boundary(semi_out):
    scr = json.loads((semi_out / "semiconductor_confidence_report.json").read_text(encoding="utf-8"))
    sb = scr.get("safety_boundary", {})
    assert sb.get("hardware_execution_enabled") is False
    assert sb.get("human_review_required") is True
    assert sb.get("candidate_only") is True


# ── Strict validation (one CLI subprocess for validate only) ──────────────────

def test_semiconductor_strict_validation_passes(semi_out):
    val = run_cli(["validate", "--case", str(semi_out), "--strict"], timeout=60)
    assert val.returncode == 0, (
        f"Strict validation failed.\nSTDOUT: {val.stdout}\nSTDERR: {val.stderr}"
    )
    assert "PASSED" in val.stdout


# ── Forbidden terms ────────────────────────────────────────────────────────────

_FORBIDDEN_TERMS = [
    "execute_recipe", "modify_recipe", "control_deposition",
    "recipe_change_command", "robot_command", "satellite_command",
    "automatic_recovery_execution", "timing_closure_certified",
    "certified_root_cause", "confirmed_root_cause", "safety_certified",
]


def test_process_drift_report_no_forbidden_terms(semi_out):
    text = (semi_out / "process_drift_report.json").read_text(encoding="utf-8").lower()
    for term in _FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term '{term}' found in process_drift_report.json"


def test_confidence_report_no_forbidden_terms(semi_out):
    text = (semi_out / "semiconductor_confidence_report.json").read_text(encoding="utf-8").lower()
    for term in _FORBIDDEN_TERMS:
        assert term not in text, f"Forbidden term '{term}' found in semiconductor_confidence_report.json"


# ── Confidence semantics ───────────────────────────────────────────────────────

def test_confidence_kind_is_analysis_confidence(semi_out):
    scr = json.loads((semi_out / "semiconductor_confidence_report.json").read_text(encoding="utf-8"))
    assert scr["confidence_report"]["confidence_kind"] == "analysis_confidence"


def test_stable_sufficient_score_above_060(semi_out):
    scr = json.loads((semi_out / "semiconductor_confidence_report.json").read_text(encoding="utf-8"))
    cr = scr["confidence_report"]
    if cr.get("data_status") == "SUFFICIENT" and cr.get("signal_status") == "STABLE_NORMAL":
        assert cr["score"] >= 0.60, (
            f"SUFFICIENT+STABLE_NORMAL should give score >= 0.60, got {cr['score']}"
        )


# ── Drift report content ───────────────────────────────────────────────────────

def test_drift_report_no_root_cause_claim(semi_out):
    pdr = json.loads((semi_out / "process_drift_report.json").read_text(encoding="utf-8"))
    assert pdr.get("claim_boundary") == "candidate_drift_not_root_cause"
    text = json.dumps(pdr).lower()
    assert "certified_root_cause" not in text
    assert "confirmed_root_cause" not in text


def test_drift_report_signals_have_claim_boundary(semi_out):
    pdr = json.loads((semi_out / "process_drift_report.json").read_text(encoding="utf-8"))
    for sig in pdr.get("recent_trend_detection", {}).get("signals", []):
        assert sig.get("claim_boundary") == "candidate_trend_not_root_cause", (
            f"Signal {sig.get('metric')} missing claim_boundary"
        )
